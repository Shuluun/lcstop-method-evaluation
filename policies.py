"""Policy process: only receives configuration metadata and paid validation prefixes via stdin.
No data files, endpoint/oracle methods, or prediction caches are accessed here.
This is an audited information interface, not a hostile-code OS sandbox.
"""
import sys,json,math,time,importlib.util,warnings
from pathlib import Path
NODES=[1,5,15,30,50]
def linear(y):
 if len(y)==1:return float(y[-1])
 j=len(y)-1
 return float(min(100,max(0,y[-1]+(y[-1]-y[-2])/(NODES[j]-NODES[j-1])*(50-NODES[j]))))
def surestop_class():
 p=Path(__file__).resolve().parent/'sources/repos/ACNoonan/surestop/src/surestop/core.py'
 spec=importlib.util.spec_from_file_location('audited_surestop_core',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m.KillRule
class Client:
 def __init__(self,request):self._request=request;self.trace=[]
 def advance(self,cid,node,purpose='prefix'):
  r=self._request(dict(op='advance',id=cid,node=node,purpose=purpose))
  if 'error' in r:raise ValueError(r['error'])
  return r['loss']
 def decide(self,cid,node,prediction,stop):
  self.trace.append(dict(id=cid,node=node,prediction=prediction,stop=bool(stop)))
def run(method,ids,client,task_lambda=math.inf):
 info={};completed={};killed=[];start=time.process_time()
 if method=='full':
  for cid in ids:completed[cid]=client.advance(cid,4,'completion')[-1]
 elif method=='sh':
  alive=list(ids)
  for j in range(4):
   vals={cid:client.advance(cid,j)[-1] for cid in alive}
   ranked=sorted(alive,key=lambda c:(vals[c],ids.index(c)))
   keep=ranked[:max(1,math.ceil(len(alive)/2))];drop=set(alive)-set(keep)
   for cid in alive:client.decide(cid,j,vals[cid],cid in drop)
   killed.extend(c for c in alive if c in drop);alive=keep
  for cid in alive:completed[cid]=client.advance(cid,4,'completion')[-1]
 elif method in ['linear','taskmax']:
  anchor=ids[0];completed[anchor]=client.advance(anchor,4,'completion')[-1]
  lam=0 if method=='linear' else task_lambda
  info['lambda']=lam
  for cid in ids[1:]:
   for j in range(4):
    y=client.advance(cid,j);p=linear(y);stop=p-lam>min(completed.values())+1
    client.decide(cid,j,p,stop)
    if stop:killed.append(cid);break
   else:completed[cid]=client.advance(cid,4,'completion')[-1]
 elif method=='surestop':
  import numpy as np
  calibration=[]
  for cid in ids[:32]:
   y=client.advance(cid,4,'calibration');calibration.append(y);completed[cid]=y[-1]
  t=time.process_time()
  with warnings.catch_warnings(record=True) as ws:
   warnings.simplefilter('always');rule=surestop_class()(alpha=.1,good_threshold=20,min_peek=0).fit(np.asarray(calibration))
  info.update(lambda_=rule.lambda_,tau=rule.tau_,n_good_cal=rule.n_good_,n_cal=32,warnings=[str(x.message) for x in ws],calibration_compute_cpu_seconds=time.process_time()-t)
  for cid in ids[32:]:
   for j in range(4):
    y=client.advance(cid,j);stop=rule.should_kill(y);client.decide(cid,j,y[-1],stop)
    if stop:killed.append(cid);break
   else:completed[cid]=client.advance(cid,4,'completion')[-1]
 else:raise ValueError(method)
 return dict(method=method,selected=min(completed,key=lambda c:(completed[c],ids.index(c))) if completed else None,killed=killed,trace=client.trace,info=info,policy_cpu_seconds=time.process_time()-start)
def main():
 init=json.loads(sys.stdin.readline())
 def request(msg):
  print(json.dumps(msg),flush=True);return json.loads(sys.stdin.readline())
 result=run(init['method'],init['ids'],Client(request),init.get('task_lambda',math.inf))
 result['process_cpu_seconds']=time.process_time()
 print(json.dumps(dict(op='done',result=result)),flush=True)
if __name__=='__main__':main()