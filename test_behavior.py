import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from git_ref_retention import analyze


def command(repo,*args):
    return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()


def fixture(repo):
    command(repo,'init','--initial-branch=main');command(repo,'config','user.name','Fixture');command(repo,'config','user.email','fixture@example.invalid')
    (repo/'small').write_text('base');command(repo,'add','.');command(repo,'commit','-m','base')
    command(repo,'switch','-c','archive');(repo/'large').write_bytes(b'x'*2048);command(repo,'add','.');command(repo,'commit','-m','large')
    command(repo,'tag','retention-tag');command(repo,'switch','main')


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.repo=Path(self.tmp.name);fixture(self.repo)
    def tearDown(self):self.tmp.cleanup()
    def test_branch_drop_alone_retains_tag(self):
        r=analyze(self.repo,['refs/heads/archive'],1024);self.assertEqual(len(r['large_blobs']),1);self.assertEqual(r['large_blobs'][0]['retained_by'],['refs/tags/retention-tag']);self.assertEqual(r['logical_bytes_without_named_roots'],0)
    def test_all_named_archive_roots_removed(self):
        r=analyze(self.repo,['refs/heads/archive','refs/tags/retention-tag'],1024);self.assertEqual(r['logical_bytes_without_named_roots'],2048)
    def test_current_head_retained_even_if_branch_dropped(self):
        command(self.repo,'switch','archive');r=analyze(self.repo,['refs/heads/archive','refs/tags/retention-tag'],1024);self.assertEqual(r['large_blobs'][0]['retained_by'],['HEAD'])
    def test_exact_threshold(self):
        self.assertEqual(len(analyze(self.repo,[],2048)['large_blobs']),1);self.assertEqual(analyze(self.repo,[],2049)['large_blobs'],[])
    def test_no_mutation(self):
        before=command(self.repo,'show-ref');status=command(self.repo,'status','--porcelain');analyze(self.repo,['refs/heads/archive'],0);self.assertEqual(command(self.repo,'show-ref'),before);self.assertEqual(command(self.repo,'status','--porcelain'),status)
    def test_unknown_head_and_option_drop_rejected(self):
        for drop in [['HEAD'],['refs/heads/nope'],['--all'],['refs/heads/archive']*2]:
            with self.subTest(drop=drop),self.assertRaises(ValueError):analyze(self.repo,drop)
    def test_partial_clone_explicitly_rejected_without_fetch(self):
        command(self.repo,'config','remote.origin.promisor','true')
        with self.assertRaisesRegex(ValueError,'partial/promisor'):analyze(self.repo,[])
    def test_shallow_boundary_rejected(self):
        (self.repo/'.git'/'shallow').write_text(command(self.repo,'rev-parse','HEAD')+'\n')
        with self.assertRaisesRegex(ValueError,'shallow'):analyze(self.repo,[])
    def test_not_a_repository(self):
        with tempfile.TemporaryDirectory() as other,self.assertRaises(ValueError):analyze(other,[])
    def test_nonnegative_integer_threshold(self):
        for n in [-1,True,0.5]:
            with self.subTest(n=n),self.assertRaises(ValueError):analyze(self.repo,[],n)
    def test_annotated_tag_root(self):
        command(self.repo,'tag','-a','annotated','refs/heads/archive','-m','retainer');r=analyze(self.repo,['refs/heads/archive','refs/tags/retention-tag'],1024);self.assertEqual(r['large_blobs'][0]['retained_by'],['refs/tags/annotated'])
    def test_unborn_empty_repository(self):
        with tempfile.TemporaryDirectory() as d:
            command(d,'init','--initial-branch=main');r=analyze(d,[],0);self.assertEqual(r['captured_refs'],{});self.assertEqual(r['large_blobs'],[])


if __name__=='__main__':unittest.main()
