import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    tool=shutil.which('git-ref-retention');assert tool, 'install the console command first'
    with tempfile.TemporaryDirectory() as d:
        repo=Path(d)
        def git(*args):
            return subprocess.run(['git','-C',d,*args],check=True,capture_output=True,text=True).stdout.strip()
        git('init','--initial-branch=main');git('config','user.name','Synthetic Fixture');git('config','user.email','fixture@example.invalid')
        (repo/'small').write_text('base');git('add','.');git('commit','-m','base')
        git('switch','-c','archive');(repo/'large').write_bytes(b'x'*2048);git('add','.');git('commit','-m','large');git('tag','archive-tag');git('switch','main')
        before=git('show-ref')
        run=subprocess.run([tool,d,'--drop','refs/heads/archive','--min-bytes','1024'],cwd=d,capture_output=True,text=True)
        assert run.returncode==0,run.stderr
        report=json.loads(run.stdout);assert report['large_blobs'][0]['retained_by']==['refs/tags/archive-tag']
        assert report['logical_bytes_without_named_roots']==0
        assert git('show-ref')==before
        print(json.dumps(report,indent=2))
        failed=subprocess.run([tool,d,'--drop','--all'],cwd=d,capture_output=True,text=True)
        assert failed.returncode==2,failed
        assert git('show-ref')==before


if __name__=='__main__':main()
