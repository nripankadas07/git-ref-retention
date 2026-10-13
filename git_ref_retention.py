"""Read-only large-object retention witnesses for an explicit Git ref-drop plan."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def git(repo, args, input_text=None, allowed=(0,)):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update({'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_NOSYSTEM': '1'})
    command = ['git', '--no-replace-objects', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-c', 'protocol.allow=never', '-C', str(repo)] + args
    result = subprocess.run(command, input=input_text, capture_output=True, text=True, env=env, timeout=60)
    if result.returncode not in allowed:
        raise ValueError('Git read failed: ' + result.stderr.strip()[:500])
    return result


def refs(repo):
    result = git(repo, ['for-each-ref', '--format=%(refname) %(objectname)'])
    values = {}
    for line in result.stdout.splitlines():
        ref, oid = line.split(' ', 1)
        if not ref.startswith('refs/') or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', oid):
            raise ValueError('unexpected Git ref response')
        values[ref] = oid
    head = git(repo, ['rev-parse', '--verify', 'HEAD'], allowed=(0, 128))
    if head.returncode == 0:
        values['HEAD'] = head.stdout.strip()
    if len(values) > 128:
        raise ValueError('at most 128 ref roots are supported')
    return values


def analyze(repo, drop, min_bytes=1048576):
    repo = Path(repo).resolve()
    if not repo.is_dir():
        raise ValueError('repository must be an existing directory')
    if type(min_bytes) is not int or min_bytes < 0:
        raise ValueError('min_bytes must be a nonnegative integer')
    if not isinstance(drop, list) or any(not isinstance(x, str) for x in drop) or len(set(drop)) != len(drop):
        raise ValueError('drop must be a list of unique ref names')
    if git(repo, ['rev-parse', '--is-shallow-repository']).stdout.strip() != 'false':
        raise ValueError('shallow repositories are unsupported')
    promisor = git(repo, ['config', '--local', '--get-regexp', r'^(extensions\.partialclone|remote\..*\.promisor)$'], allowed=(0, 1))
    if promisor.returncode == 0:
        raise ValueError('partial/promisor repositories are unsupported')
    before = refs(repo)
    if 'HEAD' in drop or set(drop) - set(before):
        raise ValueError('drop names must be known refs; HEAD is always retained')
    reach, all_objects = {}, set()
    for ref, oid in sorted(before.items()):
        # Feed immutable captured OIDs, never user-supplied revision syntax.
        output = git(repo, ['rev-list', '--objects', '--no-object-names', oid, '--']).stdout
        objects = set(output.splitlines())
        if any(not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', x) for x in objects):
            raise ValueError('unexpected object id response')
        reach[ref] = objects
        all_objects.update(objects)
        if len(all_objects) > 200000:
            raise ValueError('at most 200000 reachable objects are supported')
    sizes = {}
    if all_objects:
        listing = git(repo, ['cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize)'], '\n'.join(sorted(all_objects)) + '\n').stdout
        for line in listing.splitlines():
            pieces = line.split()
            if len(pieces) != 3 or pieces[0] not in all_objects or not pieces[2].isdigit():
                raise ValueError('missing or invalid object metadata')
            if pieces[1] == 'blob' and int(pieces[2]) >= min_bytes:
                sizes[pieces[0]] = int(pieces[2])
        if len(listing.splitlines()) != len(all_objects):
            raise ValueError('incomplete object metadata')
    if refs(repo) != before:
        raise ValueError('refs changed during analysis; take a fresh snapshot')
    rows = []
    for oid, size in sorted(sizes.items(), key=lambda x: (-x[1], x[0])):
        roots = sorted(ref for ref, objects in reach.items() if oid in objects)
        remaining = [r for r in roots if r not in drop]
        rows.append({'oid': oid, 'bytes': size, 'reachable_from': roots, 'retained_by': remaining, 'would_lose_named_roots': not remaining})
    return {'schema': 'git-ref-retention/v1', 'captured_refs': before, 'drop': sorted(drop), 'min_bytes': min_bytes, 'large_blobs': rows,
            'logical_bytes_without_named_roots': sum(r['bytes'] for r in rows if r['would_lose_named_roots']),
            'limits': 'No refs or objects changed. HEAD retained. Reflogs, alternates, unreachable objects, compressed/delta pack savings and remote server roots are not modeled. Losing named roots is not immediate disk reclamation.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('repository')
    p.add_argument('--drop', action='append', default=[])
    p.add_argument('--min-bytes', type=int, default=1048576)
    args = p.parse_args()
    try:
        print(json.dumps(analyze(args.repository, args.drop, args.min_bytes), indent=2, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError) as error:
        print('error: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
