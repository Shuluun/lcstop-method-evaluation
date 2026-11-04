"""Parent-side cost broker and offline evaluator. Each strategy owns a fresh worker and ledger."""
from pathlib import Path
import json,subprocess,sys,time,math,os,csv,hashlib
import numpy as np
from scipy.stats import binom
from policies import linear
R=Path(__file__).resolve().parent
METHODS=['full','sh','linear','surestop','taskmax']
NODES=[1,5,15,30,50]
class Broker:
 def __init__(self,items):
  self.ids=[x['id'] for x in items]
  self._loss={x['id']:np.mean(x['seed_loss'],axis=0) for x in items}
  self._cost={x['id']:np.sum(x['seed_cost'],axis=0) for x in items}
  self.position={cid:-1 for cid in self.ids};self.payments=[]
 def request(self,msg):
  if set(msg)!={'op','id','node','purpose'} or msg['op']!='advance':raise ValueError('only advance is allowed')
  cid=msg['id'];j=msg['node'];purpose=msg['purpose']
  if cid not in self.position or not isinstance(j,int) or not 0<=j<=4:raise ValueError('invalid configuration/checkpoint')
  if purpose not in ['prefix','completion','calibration']:raise ValueError('invalid cost category')
  old=self.position[cid]
  if j<=old:raise ValueError('checkpoint already paid or rewind attempted')
  if j!=old+1 and not (old==-1 and j==4 and purpose in ['calibration','completion']):raise ValueError('nonsequential unpaid jump')
  previous=0 if old<0 else self._cost[cid][old]
  delta=float(self._cost[cid][j]-previous)
  if delta<0:raise ValueError('negative cost')
  self.position[cid]=j;self.payments.append(dict(id=cid,node=j,purpose=purpose,seconds=delta))
  return dict(loss=self._loss[cid][:j+1].tolist(),paid_seconds=delta)
 def evaluate(self,result,task,role):
  finals={c:float(self._loss[c][-1]) for c in self.ids};best=min(finals.values());near={c for c in self.ids if finals[c]<=best+1}
  done={c for c,j in self.position.items() if j==4};killed=set(result['killed'])
  if done&killed or done|killed!=set(self.ids):raise AssertionError('incomplete or contradictory terminal statuses')
  selected=result['selected']
  if selected not in done:raise AssertionError('selected config not fully trained')
  actualbest=min(done,key=lambda c:(finals[c],self.ids.index(c)))
  if selected!=actualbest:raise AssertionError('selection did not use completed final validation')
  eligible=self.ids[32:] if result['method']=='surestop' else self.ids
  goods=[c for c in eligible if finals[c]<=20];false=[c for c in goods if c in killed]
  cats={p:sum(x['seconds'] for x in self.payments if x['purpose']==p) for p in ['calibration','prefix','completion']}
  full=sum(float(x[-1]) for x in self._cost.values());spent=sum(cats.values())
  expected=sum(float(self._cost[c][j]) for c,j in self.position.items())
  assert abs(spent-expected)<=1e-7*max(1,expected) and spent<=full*(1+1e-10)
  return dict(task=task,role=role,method=result['method'],n_configs=len(self.ids),n_training_seeds=3,n_near_optimal=len(near),n_near_optimal_completed=len(near&done),
   all_near_optimal_lost=int(not bool(near&done)),n_completed=len(done),n_killed=len(killed),selected=selected,final_validation_regret_pp=finals[selected]-best,
   full_training_recorded_seconds=full,recorded_training_seconds=spent,relative_recorded_cost=spent/full,savings_fraction=1-spent/full,
   calibration_training_seconds=cats['calibration'],prefix_training_seconds=cats['prefix'],completion_training_seconds=cats['completion'],
   eligible_single_run_denominator=len(eligible),n_good_fixed_tau=len(goods),false_good_kills=len(false),single_run_joint_good_killed=len(false)/len(eligible),
   conditional_good_killed=len(false)/len(goods) if goods else None,policy_cpu_seconds=result['policy_cpu_seconds'],info=result['info'])
def replay(items,method,task_lambda=math.inf):
 b=Broker(items);t=time.perf_counter()
 p=subprocess.Popen([sys.executable,'-B',str(R/'policies.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',cwd=R)
 p.stdin.write(json.dumps(dict(method=method,ids=b.ids,task_lambda=task_lambda))+'\n');p.stdin.flush()
 try:
  while True:
   line=p.stdout.readline()
   if not line:raise RuntimeError('worker ended unexpectedly: '+p.stderr.read())
   msg=json.loads(line)
   if msg['op']=='done':result=msg['result'];break
   ans=b.request(msg);p.stdin.write(json.dumps(ans)+'\n');p.stdin.flush()
  p.stdin.close();rc=p.wait(timeout=30);err=p.stderr.read()
  if rc:raise RuntimeError(err)
 except BaseException:p.kill();p.wait();raise
 result['worker_wall_seconds']=time.perf_counter()-t
 return b,result

def clean(obj):
 if isinstance(obj,float) and not math.isfinite(obj):return 'Infinity' if obj>0 else '-Infinity' if obj<0 else 'NaN'
 if isinstance(obj,dict):return {k:clean(v) for k,v in obj.items()}
 if isinstance(obj,list):return [clean(x) for x in obj]
 return obj

def main():
 wall=time.perf_counter();cpu=time.process_time();data=json.loads((R/'data/selected_validation_v2_units.json').read_text());sel=data['selection']
 if data['failures'] or any(len(v)!=128 for v in data['tasks'].values()):raise ValueError('selected pool incomplete; do not replace or silently evaluate changed pools')
 assert data['metric']=='100 * (1 - Train/val_balanced_accuracy)', 'unit contract required before any replay'
 for items in data['tasks'].values():
  for x in items:
   a=np.asarray(x['seed_accuracy_fraction']);assert ((a>=0)&(a<=1)).all() and np.array_equal(np.asarray(x['seed_loss']),100*(1-a)), 'unit mismatch'
 tasks=sel['tasks'];cal=tasks[:3];demo=tasks[3:]
 # Predeclared causal predictor, not fitted to calibration task labels.
 st=time.process_time();scores=[]
 for task in cal:
  scores.append(max(linear(np.mean(x['seed_loss'],axis=0)[:j+1])-np.mean(x['seed_loss'],axis=0)[-1] for x in data['tasks'][task] for j in range(4)))
 k=math.ceil((len(cal)+1)*.9);lam=math.inf if k>len(cal) else sorted(scores)[k-1]
 cal_cpu=time.process_time()-st
 aux=sum(float(np.sum(x['seed_cost'],axis=0)[-1]) for task in cal for x in data['tasks'][task])
 outdir=R/'results';outdir.mkdir(exist_ok=True);rows=[];childcpu=0
 for task in tasks:
  for method in METHODS:
   if time.process_time()-cpu+childcpu>14400:raise RuntimeError('CPU budget reached; no automatic extension')
   b,res=replay(data['tasks'][task],method,lam)
   row=b.evaluate(res,task,sel['roles'][task]);row['worker_wall_seconds']=res['worker_wall_seconds'];row['online_policy_cpu_seconds']=max(0,res['policy_cpu_seconds']-res['info'].get('calibration_compute_cpu_seconds',0));rows.append(row);childcpu+=res['process_cpu_seconds']
   (outdir/(task+'__'+method+'.json')).write_text(json.dumps(clean(dict(metrics=row,trace=res['trace'],payments=b.payments,positions=b.position)),indent=2))
   print('REPLAY',task,method,'finished',flush=True)
 summary=[]
 for method in METHODS:
  rs=[r for r in rows if r['task'] in demo and r['method']==method]
  cs=[r for r in rows if r['task'] in cal and r['method']==method]
  n=len(cs);fails=sum(r['all_near_optimal_lost'] for r in cs)
  summary.append(dict(method=method,n_demo_tasks=len(rs),all_near_optimal_lost_count=sum(r['all_near_optimal_lost'] for r in rs),
   mean_task_loss=np.mean([r['all_near_optimal_lost'] for r in rs]).item(),mean_relative_recorded_cost=np.mean([r['relative_recorded_cost'] for r in rs]).item(),
   mean_final_validation_regret_pp=np.mean([r['final_validation_regret_pp'] for r in rs]).item(),
   demo_total_recorded_seconds=sum(r['recorded_training_seconds'] for r in rs),
   auxiliary_calibration_recorded_seconds=aux if method=='taskmax' else 0,
   cold_start_recorded_seconds=sum(r['recorded_training_seconds'] for r in rs)+(aux if method=='taskmax' else 0),
   single_run_joint_false_kill_task_equal=np.mean([r['single_run_joint_good_killed'] for r in rs]).item(),
   ltt_development_n_tasks=n,ltt_development_task_failures=fails,ltt_binomial_pvalue=float(binom.cdf(fails,n,.1)),
   ltt_alpha=.1,ltt_delta=.05,ltt_bonferroni_methods=5,ltt_certified=bool(binom.cdf(fails,n,.1)<.05/5),
   structurally_safe_no_pruning=bool(method in ['full','taskmax']),
   ltt_note='diagnostic only: metadata-selected tasks not established iid; no formal certification. Full/no-pruning is safe by construction, not by this powerless empirical test.'))
 result=dict(status='development_only_completed',task_scores=scores,task_quantile_order=k,n_calibration_tasks=3,task_lambda=lam,task_calibration_compute_cpu_seconds=cal_cpu,
  auxiliary_task_calibration_training_seconds=aux,summary=summary,rows=rows,wall_seconds=time.perf_counter()-wall,
  experiment_parent_cpu_seconds=time.process_time(),policy_child_cpu_seconds=childcpu,experiment_accounted_cpu_seconds=time.process_time()+childcpu,
  cpu_limit_seconds=14400,new_model_training=0,gpu_training=0,formal_test_tasks=[],test_metric_fields_used=[])
 (outdir/'pilot_results.json').write_text(json.dumps(clean(result),indent=2))
 fields=[k for k in rows[0] if k!='info']
 with (outdir/'per_task.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:clean(r[k]) for k in fields} for r in rows)
 print(json.dumps(clean(dict(summary=summary,cpu_seconds=result['experiment_accounted_cpu_seconds'],wall_seconds=result['wall_seconds'])),indent=2))
if __name__=='__main__':main()