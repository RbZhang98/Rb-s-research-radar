import json,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class WorkflowTests(unittest.TestCase):
 def test_single_writer_and_no_pr_deploy(self):
  text=(ROOT/'.github/workflows/update.yml').read_text();self.assertIn('group: research-radar-pages',text);self.assertIn('cancel-in-progress: false',text);self.assertEqual(text.count('git push origin HEAD:main'),1);self.assertIn("github.ref == 'refs/heads/main'",text);self.assertNotIn('git push --force',text);self.assertIn('--radar basic',text);self.assertIn('--radar clinical',text)
 def test_rebase_disjoint_main_changes_before_bot_push(self):
  # Exercise actual Git commands in disposable repositories, never the user's branch.
  def git(folder,*args):return subprocess.check_output(['git','-C',str(folder),*args],stderr=subprocess.STDOUT).decode().strip()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);remote=root/'remote.git';a=root/'bot';b=root/'human'
   subprocess.check_output(['git','init','--bare',str(remote)],stderr=subprocess.STDOUT)
   subprocess.check_output(['git','clone',str(remote),str(a)],stderr=subprocess.STDOUT)
   for folder in [a]:git(folder,'config','user.name','test');git(folder,'config','user.email','test@example.invalid')
   git(a,'switch','-c','main');(a/'seed').write_text('base');git(a,'add','.');git(a,'commit','-m','base');git(a,'push','origin','main')
   subprocess.check_output(['git','clone','-b','main',str(remote),str(b)],stderr=subprocess.STDOUT);git(b,'config','user.name','test');git(b,'config','user.email','test@example.invalid')
   (a/'data.json').write_text('new data');git(a,'add','.');git(a,'commit','-m','data')
   (b/'README.md').write_text('concurrent source edit');git(b,'add','.');git(b,'commit','-m','source');git(b,'push','origin','main')
   git(a,'fetch','origin','main');git(a,'rebase','origin/main');git(a,'push','origin','HEAD:main')
   self.assertEqual((a/'README.md').read_text(),'concurrent source edit');self.assertEqual((a/'data.json').read_text(),'new data')
