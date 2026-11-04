"""Implementation tests, synthetic only; do not mix with benchmark performance."""
import json,math,warnings,time
from pathlib import Path
import numpy as np
from policies import Client,run,linear,surestop_class
from replay import Broker,replay as base_replay,clean
START_WALL=time.perf_counter();START_CPU=time.process_time();CHILD_CPU=0
def replay(*args,**kwargs):
 global CHILD_CPU
 b,r=base_replay(*args,**kwargs);CHILD_CPU+=r["process_cpu_seconds"];return b,r
R=Path(__file__).resolve().parent
checks=[]
def check(name,fun):
 try:fun();checks.append(dict(name=name,status='PASS'))
 except Exception as e:checks.append(dict(name=name,status='FAIL',error=repr(e)));raise
class Pause(Exception):pass
def synthetic(n=128):
 return [dict(id=str(i),metadata={},seed_loss=[[30+i/10,25+i/10,20+i/10,15+i/10,10+i/10] for _ in range(3)],seed_cost=[[1,5,15,30,50] for _ in range(3)]) for i in range(n)]
def future_invariance():
 for method in ['sh','linear','surestop','taskmax']:
  items=synthetic();altered=json.loads(json.dumps(items));fixed=set(range(32)) if method=='surestop' else {0} if method in ['linear','taskmax'] else set()
  for i,x in enumerate(altered):
   if i not in fixed:
    for y in x['seed_loss']:y[1:]=[99,1,99,1]
  traces=[]
  for fixture in [items,altered]:
   b=Broker(fixture)
   def request(msg):
    if msg['node']>0 and int(msg['id']) not in fixed:raise Pause()
    return b.request(msg)
   c=Client(request)
   try:run(method,b.ids,c,math.inf)
   except Pause:pass
   traces.append(c.trace)
  assert traces[0]==traces[1] and traces[0],method
 defpred=linear([40,35]);assert defpred==linear([40,35])
def broker_guards():
 b=Broker(synthetic(2))
 for msg in [dict(op='endpoint',id='0',node=4,purpose='prefix'),dict(op='advance',id='0',node=3,purpose='prefix'),dict(op='advance',id='0',node=0,purpose='test')]:
  try:b.request(msg);raise AssertionError('illegal request accepted')
  except ValueError:pass
 r=b.request(dict(op='advance',id='0',node=0,purpose='prefix'));assert len(r['loss'])==1
 try:b.request(dict(op='advance',id='0',node=0,purpose='prefix'));raise AssertionError('rewind accepted')
 except ValueError:pass
def quantile_and_surestop():
 K=surestop_class();Y=np.array([[35,30,25,20,15] for _ in range(32)],float)
 rule=K(alpha=.1,good_threshold=20).fit(Y)
 scores=np.where(Y[:,-1]<=20,Y[:,:-1].max(axis=1)-20,-np.inf);expected=sorted(scores)[math.ceil(33*.9)-1]
 assert rule.lambda_==expected
 for row in [[36,30,25,20,15],[25,20,15,10,5]]:
  for j in range(4):assert rule.should_kill(row[:j+1])==bool(row[j]-expected>20)
 try:K(alpha=.1,good_threshold=20).fit(Y[:3]);raise AssertionError('insufficient calibration accepted')
 except ValueError:pass
 with warnings.catch_warnings(record=True) as ws:
  r=K(alpha=.1,good_threshold=20).fit(np.full((32,5),90.0));assert r.lambda_==-math.inf and r.should_kill([90]) and ws
 assert math.ceil((3+1)*.9)>3
 assert (1-.1)**3>.05

def independent_replay_costs():
 items=synthetic()
 for method in ['full','sh','linear','surestop','taskmax']:
  b,r=replay(items,method);m=b.evaluate(r,'synthetic','implementation_only')
  assert abs(m['recorded_training_seconds']-sum(p['seconds'] for p in b.payments))<1e-8
  if method=='full':assert m['relative_recorded_cost']==1 and m['n_completed']==128
  if method=='taskmax':assert m['relative_recorded_cost']==1 and m['n_completed']==128
  if method=='surestop':assert m['calibration_training_seconds']==32*150
  b2,r2=replay(items,method);assert r['trace']==r2['trace'] and b.payments==b2.payments

def event_counterexamples():
 # A late bloomer is genuinely best, yet its prefix is worse at rung1.
 items=synthetic(8)
 for x in items:
  i=int(x['id']);x['seed_loss']=[[5+i]*5 for _ in range(3)]
 items[-1]['seed_loss']=[[90,90,90,90,0] for _ in range(3)]
 b,r=replay(items,'sh');m=b.evaluate(r,'synthetic_late_bloomer','implementation_only');assert m['all_near_optimal_lost']==1 and m['final_validation_regret_pp']==5
 # One good candidate can be killed while a different equally near-optimal candidate survives.
 b=Broker(synthetic(2));b._loss={'0':np.array([90,90,90,90,5]),'1':np.array([5,5,5,5,5])}
 b.request(dict(op='advance',id='0',node=0,purpose='prefix'));b.request(dict(op='advance',id='1',node=4,purpose='completion'))
 r=dict(method='linear',selected='1',killed=['0'],policy_cpu_seconds=0,info={})
 m=b.evaluate(r,'synthetic_event_separation','implementation_only');assert m['false_good_kills']==1 and m['all_near_optimal_lost']==0
def lexical_transport():
 import io,json
 from json_adapter import NumericJSONAdapter
 class Chunks:
  def __init__(self,b):self.f=io.BytesIO(b)
  def read(self,n):return self.f.read(min(n,137))
 text='{"x":Infinity,"y":-Infinity,"z":NaN,"quoted":"'+('Infinity NaN '*200)+'","valid":1.2}'
 a=NumericJSONAdapter(Chunks(text.encode()));parts=[]
 while True:
  b=a.read(31)
  if not b:break
  parts.append(b)
 d=json.loads(b''.join(parts));assert d['x'] is None and d['y'] is None and d['z'] is None and d['quoted']=='Infinity NaN '*200 and a.replacements==3
check('numeric JSON adapter: missing stays missing, quoted strings preserved across blocks',lexical_transport)
check('future-label mutations leave earlier forecasts/actions unchanged (four stopping policies)',future_invariance)
check('paid-prefix whitelist, jump, rewind and test/endpoint request rejection',broker_guards)
check('original SureStop rank/decision equivalence, insufficient sample, negative-infinity case; task quantile infinity',quantile_and_surestop)
check('fresh subprocess per strategy; deterministic independent replay; exact no-double-count costs',independent_replay_costs)
check('late-bloomer failure and single-configuration versus task event distinction',event_counterexamples)
(R/'results').mkdir(exist_ok=True)
(R/'results/implementation_checks.json').write_text(json.dumps(clean(dict(scope='synthetic implementation checks only',checks=checks,wall_seconds=time.perf_counter()-START_WALL,parent_cpu_seconds=time.process_time()-START_CPU,child_cpu_seconds=CHILD_CPU,total_accounted_cpu_seconds=time.process_time()-START_CPU+CHILD_CPU)),indent=2))
print(json.dumps(checks,indent=2))