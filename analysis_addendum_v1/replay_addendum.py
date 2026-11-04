"""Replay fixed addendum in a fresh child directory; no original output overwrite."""
from pathlib import Path
import argparse,subprocess,sys,os,json,hashlib,re,time
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--name',required=True);args=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_-]+',args.name):raise ValueError('Use a plain output directory name')
dest=(HERE/args.name).resolve()
if not dest.is_relative_to(HERE) or dest.exists():raise FileExistsError('Fresh addendum child directory required')
source=HERE/'run_addendum.py'
baseline=json.loads((HERE/'run_manifest.json').read_text())
if sha(source)!=baseline['script_sha256']:raise ValueError('Prepared source version changed')
dest.mkdir()
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
boot="import sys,importlib.util;from pathlib import Path;s=importlib.util.spec_from_file_location('attribution_replay',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.OUT=Path(sys.argv[2]);m.prepare() if sys.argv[3]=='prepare' else m.run()"
for stage in ['prepare','run']:
 with (dest/(stage+'.log')).open('x',encoding='utf-8') as log:
  subprocess.run([sys.executable,'-B','-c',boot,str(source),str(dest),stage],env=env,cwd=HERE.parent,stdout=log,stderr=subprocess.STDOUT,check=True)
checknames=['orders.json','attribution.csv','random_budget_comparison.csv','random_summary.json']
equal={n:sha(HERE/n)==sha(dest/n) for n in checknames}
if not all(equal.values()):raise AssertionError(equal)
new=json.loads((dest/'run_manifest.json').read_text())
check=dict(status='PASS',identical_data_artifacts=equal,new_random_orders=False,
 original_analysis_cpu_seconds=baseline['total_measured_cpu_seconds'],
 replay_cpu_seconds=new['total_measured_cpu_seconds'],
 combined_measured_cpu_seconds=baseline['total_measured_cpu_seconds']+new['total_measured_cpu_seconds'],
 driver_sha256=sha(Path(__file__)),source_sha256=sha(source),
 scope='deterministic replay of the same 200 orders/task, not extra Monte Carlo observations')
if check['combined_measured_cpu_seconds']>600:raise RuntimeError('Combined CPU limit exceeded')
(dest/'replay_check.json').write_text(json.dumps(check,indent=2))
print(json.dumps(check,indent=2))
