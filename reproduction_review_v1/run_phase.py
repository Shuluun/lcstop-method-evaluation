"""Run one predeclared small-cache reproduction phase, preserving logs."""
from pathlib import Path
import sys,os,json,time,subprocess,importlib.metadata
R=Path(__file__).resolve().parents[1];O=R/'reproduction_review_v1'
phase=sys.argv[1]
if phase not in ['pilot','addendum']:raise ValueError(phase)
plan=json.loads((O/'plan.json').read_text(encoding='utf-8'))
cmd=plan['pilot_command' if phase=='pilot' else 'attribution_command']
env=os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(R/'.cache/matplotlib'),TEMP=str(R/'.cache/tmp'),TMP=str(R/'.cache/tmp'))
start=time.perf_counter();status='FAILED';rc=None
log=O/(phase+'.log')
with log.open('x',encoding='utf-8') as f:
    p=subprocess.Popen(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
    try:rc=p.wait(timeout=plan['per_wrapper_wall_timeout_seconds'])
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=f,stderr=subprocess.STDOUT)
        status='TIMEOUT'
    else:status='PASS' if rc==0 else 'FAIL'
v=dict(phase=phase,status=status,returncode=rc,wall_seconds=time.perf_counter()-start,command=cmd,raw_archive_opened=False,new_training=False,formal_test=False)
(O/(phase+'_execution.json')).write_text(json.dumps(v,indent=2),encoding='utf-8')
print(json.dumps(v))
if rc!=0:raise SystemExit(1)