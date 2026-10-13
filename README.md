# git-ref-retention

Show which remaining Git refs retain large blobs before a proposed ref drop.

**Alpha, offline diagnostic.** Built for a maintainer investigating why a large Git blob remains reachable after a proposed ref cleanup.
Original implementation with AI assistance; no competitor code or prose copied.
No production impact, adoption or performance advantage is claimed.

## Install and get a useful result

Python 3.10+ and Git 2.30+ on PATH. Clone this repository, then:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
python example.py
```

The bundled fixture is synthetic. `example.py` only creates its own temporary
fixture when present. Exit 0 means a report was produced with no CLI-level failure;
exit 2 reports invalid or unsupported input.
Read the report limits before taking action.

## Input

```bash
git-ref-retention /path/to/full/repository --drop refs/heads/archive --drop refs/tags/old --min-bytes 1048576
```

`--drop` is repeatable and must name an existing full ref exactly; no revision
expressions or HEAD removal are accepted. `--min-bytes` includes the threshold.
`captured_refs` pins the read roots; each reported blob lists original roots and
remaining `retained_by` roots. `logical_bytes_without_named_roots` sums only the
reported large blobs, in uncompressed bytes. Reflogs may still retain them and
packs may occupy different disk space. This command changes nothing.

## Capability and limits

Requires the Git executable and a full local repository; shallow and partial/promisor clones are rejected without fetching. At most 128 named roots plus HEAD within that bound and 200,000 reachable objects. Captures ref OIDs, runs read-only Git graph/metadata commands with lazy fetching, hooks, fsmonitor and transports disabled, then rejects changed refs. HEAD is always retained. Reports large blobs only, including exact remaining-root witnesses and the sum of reported uncompressed bytes that would lose named roots. Reflogs, unreachable objects, alternates, remote roots, compressed/delta pack sizes and immediate reclamation are not modeled. No ref/object deletion or rewrite occurs.

## Acceptance criteria

Dropping an archive branch alone retains its blob via a tag; dropping both loses named roots; checking out that commit retains it through HEAD; exact size thresholds work; annotated tags retain; shallow/promisor/unknown roots fail; refs and worktree remain unchanged.

## Checks and evidence

```bash
python -m unittest -v
python -m compileall -q .
```

[Validation](VALIDATION.md) documents the prepared checks and failure cases.
[Research and alternatives](RESEARCH.md) records dated observations, competing
workflows and a bounded inferred need. The [CI workflow](.github/workflows/test.yml)
builds wheels and tests installed commands outside the checkout on Linux Python
3.10/3.12/3.14. Check the actual current Actions result before relying on it.

[Contributing](CONTRIBUTING.md) · [Support](SUPPORT.md) ·
[Security](SECURITY.md) · [MIT license](LICENSE)
