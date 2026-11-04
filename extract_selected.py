"""Streaming metadata pass then whitelisted six-task extraction; no test outcomes retained."""
from pathlib import Path
import zipfile,ijson,json,hashlib,time,sys
from json_adapter import NumericJSONAdapter
R=Path(__file__).resolve().parent
TASKS=['volkert','higgs','mfeat-factors','car','christine','kr-vs-kp']
NODES=[1,5,15,30,50]
def order(x):return hashlib.sha256(('LCStop20261029|'+x).encode()).hexdigest()
def events():
 with zipfile.ZipFile(R/'data/bench_full.zip').open('bench_full.json') as f:
  yield from ijson.parse(NumericJSONAdapter(f),use_float=True)
def metadata():
 t=time.perf_counter();ids={x:set() for x in TASKS};seeds={x:set() for x in TASKS};epochs={};cost_clock={};budget={};logkeys=set()
 for p,e,v in events():
  a=p.split('.')
  if a[0] not in ids:continue
  if e=='map_key' and len(a)==2 and str(v)=='50':ids[a[0]].add(a[1])
  if len(a)>=3 and a[2]=='50':
   if e=='map_key' and len(a)==4 and a[3]=='log':seeds[a[0]].add(str(v))
   if e=='map_key' and len(a)==5 and a[3]=='log':logkeys.add(str(v))
   if e=='number' and len(a)==7 and a[3]=='log' and a[5] in ['epoch','time'] and a[1]=='52':
    d=epochs if a[5]=='epoch' else cost_clock
    d.setdefault(a[0]+':'+a[4],[]).append(v)
 out={'tasks':TASKS,'roles':dict(zip(TASKS,['development_calibration']*3+['development_demonstration']*3)),
 'selected_ids':{x:sorted(ids[x],key=order)[:128] for x in TASKS},'available_id_counts':{x:len(ids[x]) for x in TASKS},
 'training_seeds':{x:sorted(seeds[x],key=int)[:3] for x in TASKS},'horizon':50,'nodes':NODES,'metadata_epoch_examples':epochs,'metadata_time_examples':cost_clock,
 'log_fields':sorted(logkeys),'selection_salt':'LCStop20261029','wall_seconds':time.perf_counter()-t,'parser_process_cpu_seconds':time.process_time()}
 if any(len(out['selected_ids'][x])!=128 or len(out['training_seeds'][x])!=3 for x in TASKS):raise ValueError('metadata eligibility insufficient; no outcome replacement')
 (R/'sources/selection.json').write_text(json.dumps(out,indent=2));print('METADATA_SELECTION_SAVED',json.dumps({k:out[k] for k in ['tasks','available_id_counts','training_seeds','log_fields','wall_seconds']}),flush=True)
def extract():
 t=time.perf_counter();sel=json.loads((R/'sources/selection.json').read_text());runs={};configs={}
 allow=['epoch','time','Train/val_balanced_accuracy']
 for p,e,v in events():
  a=p.split('.')
  if a[0] not in sel['selected_ids'] or len(a)<3 or a[1] not in sel['selected_ids'][a[0]] or a[2]!='50':continue
  if len(a)==5 and a[3]=='config' and e in ['string','number','boolean','null']:
   configs.setdefault(a[0]+':'+a[1],{})[a[4]]=v
  if len(a)==7 and a[3]=='log' and a[4] in sel['training_seeds'][a[0]] and a[5] in allow and e in ['number','null']:
   runs.setdefault(a[0]+':'+a[1]+':'+a[4],{}).setdefault(a[5],[]).append(v)
 tasks={};fails=[]
 for task in TASKS:
  items=[]
  for cid in sel['selected_ids'][task]:
   curves=[];clocks=[];accuracies=[]
   for seed in sel['training_seeds'][task]:
    d=runs.get(task+':'+cid+':'+seed,{})
    try:
     ep=d['epoch']; y=d['Train/val_balanced_accuracy'];tm=d['time'];assert len(ep)==len(y)==len(tm)
     ind=[ep.index(n) for n in NODES]
     assert all(0<=q<=1 for q in y) and all(tm[i+1]>=tm[i] for i in range(len(tm)-1))
     # Logger time is cumulative elapsed seconds; include initial recorded setup time if nonnegative.
     assert tm[0]>=0 and 0<tm[-1]<1e7, 'unverified or nonpositive time scale'
     accuracies.append([y[i] for i in ind]);curves.append([100*(1-y[i]) for i in ind]);clocks.append([tm[i] for i in ind])
    except Exception as ex:fails.append(dict(task=task,config=cid,seed=seed,reason=repr(ex)));break
   if len(curves)==3:items.append(dict(id=cid,metadata=configs.get(task+':'+cid,{}),seed_loss=curves,seed_cost=clocks,seed_accuracy_fraction=accuracies))
  tasks[task]=items
 out={'selection':sel,'tasks':tasks,'failures':fails,'metric':'100 * (1 - Train/val_balanced_accuracy)','unit':'percentage points','cost_unit':'recorded elapsed seconds summed over 3 training seeds','wall_seconds':time.perf_counter()-t,'parser_process_cpu_seconds':time.process_time(),'test_fields_retained':[]}
 (R/'data/selected_validation_v2_units.json').write_text(json.dumps(out));(R/'sources/extraction_summary.json').write_text(json.dumps({'counts':{k:len(v) for k,v in tasks.items()},'failures':fails,'wall_seconds':out['wall_seconds'],'test_fields_retained':[]},indent=2))
 print('EXTRACTED_COUNTS',json.dumps({k:len(v) for k,v in tasks.items()}),'failures',len(fails),'seconds',out['wall_seconds'],flush=True)
if __name__=='__main__': {'metadata':metadata,'extract':extract}[sys.argv[1]]()