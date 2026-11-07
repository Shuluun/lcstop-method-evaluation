"""Compare a predeclared clean-environment replay with committed scientific outputs."""
from pathlib import Path
import json,csv,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R/'reproduction_review_v1'
P=R/'reproductions/pilot_replay_01'
A=R/'reproductions/attribution_replay_01/analysis_addendum_v1/publication_replay'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=load(O/'plan.json');exclude=set(plan['timing_exclusions'])
def strip(x):
    if isinstance(x,dict):return {k:strip(v) for k,v in x.items() if k not in exclude}
    if isinstance(x,list):return [strip(v) for v in x]
    return x
diff=[];maxdiff=0.;count=0
def compare(a,b,path):
    global maxdiff,count
    count+=1
    if isinstance(a,dict) and isinstance(b,dict):
        if set(a)!=set(b):diff.append({'path':path,'reason':'different fields'});return
        for k in a:compare(a[k],b[k],path+'/'+str(k))
    elif isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b):diff.append({'path':path,'reason':'different lengths'});return
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
    elif a!=b:
        v={'path':path,'reason':'exact value mismatch'}
        if isinstance(a,(int,float)) and isinstance(b,(int,float)):
            delta=abs(a-b);maxdiff=max(maxdiff,delta);v['abs_difference']=delta
        diff.append(v)
for f in ['pilot_execution.json','addendum_execution.json']:
    if load(O/f)['status']!='PASS':raise RuntimeError('Execution did not succeed: '+f)
tasks=plan['tasks'];methods=['full','sh','linear','surestop','taskmax']
rows=[]
for task in tasks:
    for m in methods:
        name=f'{task}__{m}.json';n=len(diff)
        compare(strip(load(R/'results'/name)),strip(load(P/'results'/name)),name)
        rows.append({'task':task,'method':m,'exact_scientific_outputs_match':len(diff)==n})
compare(strip(load(R/'results/pilot_results.json')),strip(load(P/'results/pilot_results.json')),'pilot_results.json')
compare(load(R/'results/figure_case.json'),load(P/'results/figure_case.json'),'figure_case.json')
oldchecks=load(R/'results/implementation_checks.json');newchecks=load(P/'results/implementation_checks.json')
compare(oldchecks['checks'],newchecks['checks'],'synthetic_checks')
with (R/'results/per_task.csv').open(encoding='utf-8-sig',newline='') as f:oldcsv=list(csv.DictReader(f))
with (P/'results/per_task.csv').open(encoding='utf-8-sig',newline='') as f:newcsv=list(csv.DictReader(f))
compare(strip(oldcsv),strip(newcsv),'per_task.csv')
datafiles=['orders.json','attribution.csv','random_budget_comparison.csv','random_summary.json']
equal={n:sha(R/'analysis_addendum_v1'/n)==sha(A/n) for n in datafiles}
preserved=[n for n,h in plan['tracked_sha256_before'].items() if sha(R/n)!=h]
v=dict(status='PASS' if not diff and all(equal.values()) and not preserved else 'FAIL',
 comparison_rule=plan['comparison'],pilot_replays_compared=len(rows),pilot_scientific_output_comparisons=rows,
 recursive_nodes_compared=count,exact_mismatches=diff,max_abs_numeric_mismatch=maxdiff,timing_fields_excluded=sorted(exclude),
 synthetic_checks_reexecuted=len(newchecks['checks']),synthetic_statuses=[c['status'] for c in newchecks['checks']],
 attribution_byte_identical=equal,attribution_replay_check=load(A/'replay_check.json')['status'],
 historical_tracked_files_changed=preserved,main_delivery_check=load(P/'results/delivery_check.json')['status'],
 main_replay_cpu_seconds=load(P/'results/pilot_results.json')['experiment_accounted_cpu_seconds'],
 synthetic_cpu_seconds=newchecks['total_accounted_cpu_seconds'],
 attribution_cpu_seconds=load(A/'run_manifest.json')['total_measured_cpu_seconds'],
 new_training=0,new_tasks=0,formal_test_tasks=load(P/'results/pilot_results.json')['formal_test_tasks'],raw_archive_opened=False)
(O/'comparison.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
# Include new outputs compactly; deterministic byte-identical data are already versioned once.
dest=O/'replayed_pilot';dest.mkdir(exist_ok=False)
for x in (P/'results').iterdir():
    if x.is_file() and x.name!='document_check.json':shutil.copyfile(x,dest/x.name)
figdest=O/'figures';figdest.mkdir()
for x in (P/'figures').iterdir():
    if x.is_file():shutil.copyfile(x,figdest/x.name)
dest=O/'replayed_addendum';dest.mkdir()
for n in ['run_manifest.json','replay_check.json','prepare.log','run.log','comparison.png']:
    shutil.copyfile(A/n,dest/n)
(O/'comparison_rows.csv').write_text('task,method,exact_scientific_outputs_match\n'+''.join(f"{x['task']},{x['method']},{x['exact_scientific_outputs_match']}\n" for x in rows),encoding='utf-8')
print(json.dumps({k:v[k] for k in ['status','pilot_replays_compared','recursive_nodes_compared','exact_mismatches','max_abs_numeric_mismatch','attribution_byte_identical','historical_tracked_files_changed','main_replay_cpu_seconds','synthetic_cpu_seconds','attribution_cpu_seconds']},indent=2))
if v['status']!='PASS':raise SystemExit(1)