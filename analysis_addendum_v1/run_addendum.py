"""Bounded retrospective attribution; writes only this addendum directory.
No original policy imports/execution, no new models, no unselected-task objects.
"""
import time
START_CPU=time.process_time()
START_WALL=time.perf_counter()
from pathlib import Path
import sys,json,hashlib,csv,math,platform
import numpy as np
import ijson

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
TASKS=['car','christine','kr-vs-kp']
SEED=20261030
REPEATS=200
EPS=1.0
LIMIT=600.0
CACHE=ROOT/'data/selected_validation_v2_units.json'
INPUTS=[CACHE,ROOT/'policies.py',ROOT/'replay.py',ROOT/'pilot_rules.md']+[ROOT/'results'/f'{t}__{m}.json' for t in TASKS for m in ['sh','surestop']]

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(name,obj):
 p=(OUT/name).resolve()
 assert p.is_relative_to(OUT)
 if p.exists():raise FileExistsError(f'Preserve existing output: {p}')
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def csv_write(name,rows):
 with (OUT/name).open('x',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def fingerprints():
 return {p.relative_to(ROOT).as_posix():digest(p) for p in INPUTS}
def check_budget(prep=0):
 if prep+time.process_time()>LIMIT:raise RuntimeError('600 CPU-second limit reached; no automatic expansion')
def ids_only(task):
 with CACHE.open('rb') as f:
  return [str(x) for x in ijson.items(f,f'tasks.{task}.item.id',use_float=True)]
def task_items(task):
 # Other tasks' lexical tokens may be traversed, but only the named task is materialized.
 with CACHE.open('rb') as f:
  return list(ijson.items(f,f'tasks.{task}.item',use_float=True))
def prepare():
 if (OUT/'plan.json').exists():raise FileExistsError('Existing plan preserved')
 ids={t:ids_only(t) for t in TASKS}
 assert all(len(v)==128 and len(set(v))==128 for v in ids.values())
 streams=np.random.SeedSequence(SEED).spawn(len(TASKS))
 orders={}
 for t,child in zip(TASKS,streams):
  rng=np.random.Generator(np.random.PCG64(child))
  orders[t]=[[ids[t][int(i)] for i in rng.permutation(128)] for _ in range(REPEATS)]
 write('orders.json',orders)
 plan=dict(status='fixed_before_addendum_outcome_computation',tasks=TASKS,seed=SEED,
  rng='NumPy PCG64; SeedSequence(20261030).spawn(3) in task order; 200 sequential permutations/task',
  repeats_per_task=REPEATS,paired_orders_across_budgets=True,orders_sha256=digest(OUT/'orders.json'),
  candidates_by_task=ids,alpha=.1,tau_loss_pp=20,epsilon_loss_pp=EPS,nodes=[1,5,15,30,50],
  seed_aggregation='mean loss over 3 existing training seeds; sum recorded time',
  budgets='saved recorded_training_seconds for each task SH and SureStop; retrospective budget matching',
  exhaustion_rule='Request next ID without costs/labels; if remaining budget cannot finish it, consume remaining and stop; never skip.',
  no_recommendation='kept as failure, regret undefined / +Infinity for all-run CDF and ranks',
  quantiles='all 200 outcomes, inverse empirical CDF (nearest-rank); no-recommendation is +Infinity',
  comparison='strict <, exact tie ==, and > to saved method regret; no added epsilon',
  no_across_task_guarantee=True,cpu_limit_seconds=LIMIT,inputs_sha256=fingerprints(),
  script_sha256=digest(Path(__file__)),prepare_cpu_seconds=time.process_time(),
  prepare_wall_seconds=time.perf_counter()-START_WALL)
 write('plan.json',plan)
 print('PREPARED: three fixed task pools; 200 orders each; no quality labels used in order generation.')
class OrderPolicy:
 """Only ID sequence, never qualities or costs."""
 def __init__(self,order):self._order=tuple(order);self._next=0
 def next_id(self):
  if self._next==len(self._order):return None
  x=self._order[self._next];self._next+=1;return x
class CostEnvironment:
 """Knows actual cost for requested candidate to simulate completion; no cost-based skipping."""
 def __init__(self,costs,budget):
  self._costs=costs;self.budget=float(budget);self.spent=0.;self.done=[];self.done_costs=[]
  self.partial_id=None;self.partial_paid=0.;self.requested=[]
 def request(self,cid):
  assert cid not in self.requested and self.spent<self.budget
  self.requested.append(cid)
  # Only this requested candidate's cost is inspected. Policy has already committed.
  c=float(self._costs[cid])
  finish=math.fsum(self.done_costs+[c])
  if finish<=self.budget:
   self.done.append(cid);self.done_costs.append(c);self.spent=finish;return True
  self.partial_id=cid;self.partial_paid=self.budget-self.spent;self.spent=self.budget;return False
def simulate(order,costs,budget):
 policy=OrderPolicy(order);env=CostEnvironment(costs,budget)
 while env.spent<env.budget:
  cid=policy.next_id()
  if cid is None:break
  if not env.request(cid):break
 return env
def score(env,loss,pool_best,near,ids):
 if not env.done:
  return dict(no_recommendation=1,selected_id='',final_loss_pp='',final_regret_pp='undefined',
   retained_near_optimal=0,near_optimal_completed=0,extended_regret=math.inf)
 best=min(env.done,key=lambda c:(loss[c],ids.index(c)))
 return dict(no_recommendation=0,selected_id=best,final_loss_pp=loss[best],
  final_regret_pp=loss[best]-pool_best,retained_near_optimal=int(bool(set(env.done)&near)),
  near_optimal_completed=len(set(env.done)&near),extended_regret=loss[best]-pool_best)
def implementation_checks():
 e=simulate(['expensive','cheap'],{'expensive':10,'cheap':1},5)
 assert e.done==[] and e.requested==['expensive'] and e.spent==5 and e.partial_paid==5
 e2=simulate(['a','b'],{'a':2,'b':5},4)
 assert e2.done==['a'] and e2.spent==4 and e2.partial_paid==2
 e3=simulate(['a','b'],{'a':2,'b':5},2)
 assert e3.done==['a'] and e3.spent==2 and e3.partial_id is None
 l={'a':5.,'b':0.};s1=score(e2,l,0.,{'b'},['a','b'])
 l2={'a':5.,'b':99.};s2=score(e2,l2,5.,{'a'},['a','b'])
 assert s1['selected_id']==s2['selected_id']=='a'
 # Change invisible labels; recommendation and resource path depend only on paid labels/order/cost.
 assert s1['final_loss_pp']==s2['final_loss_pp']==5
 assert score(e,{'expensive':0,'cheap':1},0,{'expensive'},['expensive','cheap'])['no_recommendation']==1
 return ['no cost look-ahead skipping','partial budget fully charged without endpoint',
  'exact budget boundary completes candidate','unpaid label mutation leaves recommendation and path unchanged',
  'zero-completion trial retained as failure']
def q_emp(values,p):
 a=sorted(values);return a[max(0,math.ceil(p*len(a))-1)]
def finite_or_inf(x):return 'Infinity' if math.isinf(float(x)) else float(x)

def run():
 plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
 assert plan['script_sha256']==digest(Path(__file__)),'Script changed after preparation'
 assert fingerprints()==plan['inputs_sha256'],'Read-only inputs changed'
 assert digest(OUT/'orders.json')==plan['orders_sha256']
 assert not (OUT/'attribution.csv').exists(),'Existing analysis preserved'
 prep=plan['prepare_cpu_seconds'];check_budget(prep)
 orders=json.loads((OUT/'orders.json').read_text())
 checks=implementation_checks()
 attrs=[];random_rows=[];summaries=[];taskdata={}
 for task in TASKS:
  items=task_items(task);ids=[str(x['id']) for x in items]
  assert ids==plan['candidates_by_task'][task]
  loss={};cost={}
  for x in items:
   a=np.asarray(x['seed_loss'],float);c=np.asarray(x['seed_cost'],float)
   raw=np.asarray(x['seed_accuracy_fraction'],float)
   assert a.shape==c.shape==raw.shape==(3,5)
   assert np.array_equal(a,100*(1-raw))
   assert np.isfinite(a).all() and np.isfinite(c).all() and (c[:,-1]>0).all()
   loss[x['id']]=float(np.mean(a,axis=0)[-1]);cost[x['id']]=float(np.sum(c,axis=0)[-1])
  ss=json.loads((ROOT/'results'/f'{task}__surestop.json').read_text())
  sh=json.loads((ROOT/'results'/f'{task}__sh.json').read_text())
  calp=[p for p in ss['payments'] if p['purpose']=='calibration']
  calids=[p['id'] for p in calp]
  assert len(calids)==len(set(calids))==32 and all(p['node']==4 for p in calp)
  assert calids==ids[:32] and all(ss['positions'][i]==4 for i in calids)
  cal=set(calids);later=set(ids)-cal;assert len(later)==96
  poolbest=min(loss.values());near={i for i in ids if loss[i]<=poolbest+EPS}
  poolbestids=[i for i in ids if loss[i]==poolbest]
  calbest=min(calids,key=lambda i:(loss[i],ids.index(i)))
  ss_done=[i for i in ids if ss['positions'][i]==4];laterdone=[i for i in ss_done if i in later]
  ss_best=min(ss_done,key=lambda i:(loss[i],ids.index(i)))
  assert ss_best==ss['metrics']['selected']
  calcost=math.fsum(cost[i] for i in calids)
  paidcal=math.fsum(p['seconds'] for p in calp)
  latercost=math.fsum(p['seconds'] for p in ss['payments'] if p['id'] in later)
  reconcile=max(abs(calcost-paidcal),abs(calcost-ss['metrics']['calibration_training_seconds']),
    abs(math.fsum([paidcal,latercost])-ss['metrics']['recorded_training_seconds']))
  # Existing accounting tolerance; never used to change budget or quality decisions.
  assert reconcile<=1e-7*max(1.,ss['metrics']['recorded_training_seconds'])
  assert abs((loss[ss_best]-poolbest)-ss['metrics']['final_validation_regret_pp'])<1e-12
  a=dict(task=task,n_pool=128,n_calibration=32,n_later=96,calibration_ids_json=json.dumps(calids),
   pool_best_loss_pp=poolbest,pool_best_ids_json=json.dumps(poolbestids),
   pool_best_in_calibration_json=json.dumps([i for i in poolbestids if i in cal]),
   pool_best_in_later_json=json.dumps([i for i in poolbestids if i in later]),
   near_pool_count=len(near),near_calibration_count=len(near&cal),near_later_count=len(near&later),
   near_calibration_ids_json=json.dumps([i for i in ids if i in near&cal]),
   near_later_ids_json=json.dumps([i for i in ids if i in near&later]),
   cal_best_id=calbest,cal_best_loss_pp=loss[calbest],cal_regret_pp=loss[calbest]-poolbest,
   cal_retains_near=int(bool(near&cal)),cal_complete_cost_seconds=calcost,
   surestop_selected_id=ss_best,surestop_selected_group='calibration' if ss_best in cal else 'later',
   surestop_loss_pp=loss[ss_best],surestop_regret_pp=loss[ss_best]-poolbest,
   surestop_near_retained=len(near&set(ss_done)),surestop_original_all_near_lost=ss['metrics']['all_near_optimal_lost'],
   later_completed_count=len(laterdone),later_completed_ids_json=json.dumps(laterdone),
   surestop_total_cost_seconds=ss['metrics']['recorded_training_seconds'],
   later_added_cost_seconds=latercost,later_prefix_cost_seconds=math.fsum(p['seconds'] for p in ss['payments'] if p['id'] in later and p['purpose']=='prefix'),
   later_completion_cost_seconds=math.fsum(p['seconds'] for p in ss['payments'] if p['id'] in later and p['purpose']=='completion'),
   incremental_best_loss_improvement_pp=loss[calbest]-loss[ss_best],
   near_retention_improved=int(bool(near&set(ss_done)))-int(bool(near&cal)),
   accounting_reconciliation_max_abs_seconds=reconcile)
  assert a['incremental_best_loss_improvement_pp']>=0 and a['surestop_original_all_near_lost']==0
  attrs.append(a);taskdata[task]={'loss':loss,'cost':cost,'ids':ids,'near':near,'cal':cal,'ss':ss,'sh':sh}
  for method,result in [('sh',sh),('surestop',ss)]:
   budget=float(result['metrics']['recorded_training_seconds']);obs=float(result['metrics']['final_validation_regret_pp'])
   trial_ext=[];local=[]
   for rep,order in enumerate(orders[task]):
    check_budget(prep)
    assert len(order)==128 and set(order)==set(ids)
    env=simulate(order,cost,budget);v=score(env,loss,poolbest,near,ids)
    assert env.requested==order[:len(env.requested)] and env.spent<=budget
    assert env.partial_id is None or env.spent==budget
    assert len(set(env.done))==len(env.done)
    trial_ext.append(v.pop('extended_regret'))
    r=dict(task=task,budget_reference=method,repeat=rep,seed=SEED,
     budget_seconds=budget,actual_spent_seconds=env.spent,unspent_seconds=budget-env.spent,
     n_completed=len(env.done),completed_ids_json=json.dumps(env.done),unfinished_id=env.partial_id or '',
     unfinished_paid_seconds=env.partial_paid,**v,
     original_method_regret_pp=obs,original_method_retained_near=1-int(result['metrics']['all_near_optimal_lost']))
    local.append(r);random_rows.append(r)
   vals=trial_ext;n=len(vals);rec=[v for v in vals if math.isfinite(v)]
   summaries.append(dict(task=task,budget_reference=method,n_repeats=n,budget_seconds=budget,
    near_retained_count=sum(r['retained_near_optimal'] for r in local),near_retained_fraction=sum(r['retained_near_optimal'] for r in local)/n,
    no_recommendation_count=sum(r['no_recommendation'] for r in local),no_recommendation_fraction=sum(r['no_recommendation'] for r in local)/n,
    regret_min_pp=finite_or_inf(min(vals)),regret_q05_pp=finite_or_inf(q_emp(vals,.05)),regret_q25_pp=finite_or_inf(q_emp(vals,.25)),
    regret_median_pp=finite_or_inf(q_emp(vals,.5)),regret_q75_pp=finite_or_inf(q_emp(vals,.75)),
    regret_q95_pp=finite_or_inf(q_emp(vals,.95)),regret_max_pp=finite_or_inf(max(vals)),
    regret_mean_conditional_on_recommendation_pp=float(np.mean(rec)) if rec else None,
    n_completed_min=min(r['n_completed'] for r in local),n_completed_median=q_emp([r['n_completed'] for r in local],.5),
    n_completed_max=max(r['n_completed'] for r in local),n_completed_mean=float(np.mean([r['n_completed'] for r in local])),
    actual_spent_min_seconds=min(r['actual_spent_seconds'] for r in local),actual_spent_max_seconds=max(r['actual_spent_seconds'] for r in local),
    original_method_regret_pp=obs,original_method_regret_cdf_rank=sum(v<=obs for v in vals)/n,
    random_strictly_better_count=sum(v<obs for v in vals),random_tie_count=sum(v==obs for v in vals),
    random_strictly_worse_count=sum(v>obs for v in vals),
    original_method_beats_fraction=sum(v>obs for v in vals)/n,
    original_method_n_completed=result['metrics']['n_completed'],
    original_method_near_retained=1-int(result['metrics']['all_near_optimal_lost'])))
 csv_write('attribution.csv',attrs);csv_write('random_budget_comparison.csv',random_rows)
 write('random_summary.json',summaries)
 check_budget(prep)
 make_figure(attrs,summaries,random_rows)
 assert fingerprints()==plan['inputs_sha256'],'Protected consulted files changed'
 versions=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,ijson=ijson.__version__,
  script_sha256=digest(Path(__file__)),orders_sha256=digest(OUT/'orders.json'),inputs_sha256=plan['inputs_sha256'],
  input_fingerprints_unchanged=True,scope='only consulted cache, six result files, two policy code files and pilot rules; not all project files',
  prepare_cpu_seconds=prep,analysis_process_cpu_seconds=time.process_time(),total_measured_cpu_seconds=prep+time.process_time(),
  cpu_limit_seconds=LIMIT,run_wall_seconds=time.perf_counter()-START_WALL,
  task_names=TASKS,n_repeats_per_task=REPEATS,random_orders=600,budget_replays=1200,
  checks=checks,formal_evaluation_started=False,new_training=0,new_data=0,
  raw_archives_opened=False,other_task_objects_materialized=False)
 import matplotlib
 versions['matplotlib']=matplotlib.__version__
 write('run_manifest.json',versions)
 make_note(attrs,summaries,versions)
 check_budget(prep)
 print(json.dumps(dict(attribution=[{k:a[k] for k in ['task','cal_regret_pp','surestop_regret_pp','incremental_best_loss_improvement_pp','cal_retains_near','later_added_cost_seconds']} for a in attrs],summary=summaries,total_cpu_seconds=versions['total_measured_cpu_seconds']),indent=2))

def make_figure(attrs,summaries,rows):
 import os
 os.environ['MPLCONFIGDIR']=str(OUT/'.cache')
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(3,2,figsize=(13,11),layout='constrained')
 for i,task in enumerate(TASKS):
  ax=axes[i,0];bar=axes[i,1]
  attr=next(a for a in attrs if a['task']==task)
  for m,color,label in [('sh','tab:blue','Random at SH budget'),('surestop','tab:orange','Random at SureStop budget')]:
   rs=[r for r in rows if r['task']==task and r['budget_reference']==m]
   finite=sorted(float(r['final_regret_pp']) for r in rs if not r['no_recommendation'])
   if finite:
    xs=np.array(finite);ys=np.arange(1,len(xs)+1)/REPEATS
    ax.step(xs,ys,where='post',color=color,label=label)
   z=next(s for s in summaries if s['task']==task and s['budget_reference']==m)
   ax.axvline(z['original_method_regret_pp'],color=color,linestyle='--',alpha=.7)
   ax.plot(z['original_method_regret_pp'],z['original_method_regret_cdf_rank'],'o',color=color)
  ax.axvline(attr['cal_regret_pp'],color='black',linestyle=':',label='Same 32 only')
  ax.axvline(EPS,color='gray',linestyle='-.',alpha=.6,label='1pp threshold')
  ax.set_xscale('symlog',linthresh=1)
  ax.set(xlabel='Final validation regret (pp; linear to 1, log beyond)',ylabel='Empirical CDF / all 200 orders',ylim=(0,1.03),title=task)
  ax.grid(alpha=.2)
  if i==0:ax.legend(fontsize=8,loc='lower right')
  a=next(s for s in summaries if s['task']==task and s['budget_reference']=='sh')
  b=next(s for s in summaries if s['task']==task and s['budget_reference']=='surestop')
  values=[a['near_retained_fraction'],a['original_method_near_retained'],b['near_retained_fraction'],b['original_method_near_retained'],attr['cal_retains_near']]
  bars=bar.bar(range(5),values,color=['tab:blue','tab:blue','tab:orange','tab:orange','gray'])
  for k in [1,3,4]:bars[k].set_hatch('//')
  for k,v in enumerate(values):bar.text(k,v+.025,f'{100*v:.1f}%',ha='center',fontsize=8)
  bar.set(xticks=range(5),xticklabels=['Random\nSH budget','SH\nobserved','Random\nSS budget','SS\nobserved','Same32\nobserved'],
   ylabel='At least one 1pp-near-optimal completed',ylim=(0,1.16),
   title=f"No recommendation: random SH {a['no_recommendation_count']}/200; SS {b['no_recommendation_count']}/200")
  bar.tick_params(axis='x',labelsize=8)
 fig.suptitle('Retrospective fixed-task attribution; random orders are NOT independent tasks\nDashed lines: original method regrets; circles: random CDF at that regret; hatched bars: one observed outcome',fontsize=12)
 fig.savefig(OUT/'comparison.png',dpi=170)
 plt.close(fig)

def make_note(attrs,summaries,v):
 text='# 早停开发结果的限定收尾归因\n\n2026年10月30日｜事后固定任务补充；原停止决定不变\n\n'
 text+='本补充仅使用car、christine、kr-vs-kp三个原开发演示任务的v2缓存和六个原SH/SureStop结果文件。没有重抽候选，没有新增任务、训练、模型、权重或正式评价。三记录种子的验证误差取均值，记录时间求和，终点50轮、1pp近优、α=.1、τ=20pp、节点1/5/15/30/50均不变。成本单位为原记录elapsed seconds，不是本机训练CPU或实测加速。\n\n'
 text+='## A：原32个完整候选与后续96个的新增收益\n\n32个身份来自原SureStop付款账本purpose=calibration的完整付款，核对了32个唯一ID、node4及原结果的完成位置，并与原池前32个一致。没有删除这些候选或改写原SureStop的0/3任务失败结果。所有配置身份及组别在[attribution.csv](attribution.csv)中完整登记。\n\n'
 text+='| 固定任务 | 32组最佳ID | 32组遗憾pp | 32组近优数/全池 | SureStop最终遗憾pp | 后续新增改善pp | 32完整成本秒 | 后续新增成本秒 |\n|---|---|---:|---:|---:|---:|---:|---:|\n'
 for a in attrs:
  text+=f"| {a['task']} | {a['cal_best_id']} | {a['cal_regret_pp']:.6f} | {a['near_calibration_count']}/{a['near_pool_count']} | {a['surestop_regret_pp']:.6f} | {a['incremental_best_loss_improvement_pp']:.6f} | {a['cal_complete_cost_seconds']:.3f} | {a['later_added_cost_seconds']:.3f} |\n"
 text+='\n'
 for a in attrs:
  bestcal=json.loads(a['pool_best_in_calibration_json']);bestlater=json.loads(a['pool_best_in_later_json'])
  text+=f"- **{a['task']}**：全池最低误差{a['pool_best_loss_pp']:.6f}pp；池内最佳位于32组{bestcal}、后续组{bestlater}。1pp近优在两组分别{a['near_calibration_count']}与{a['near_later_count']}个。仅32组的近优保留为{a['cal_retains_near']}；后续96组另完成{a['later_completed_count']}个，最终选择{a['surestop_selected_id']}（{a['surestop_selected_group']}），遗憾下降{a['incremental_best_loss_improvement_pp']:.6f}pp。新增费用由前缀{a['later_prefix_cost_seconds']:.3f}秒与补完{a['later_completion_cost_seconds']:.3f}秒构成。\n"
 text+='\n以上“新增改善”是原方法后续探索相对同一32组参考的实际选择改善，包含更多候选机会、前缀筛选和资源分配的共同效果；不能仅凭该分解给前缀信息一个普适因果贡献百分比。若32组已足以保存近优，该任务的近优保留成功无需后续96组才能实现；即便终点误差继续改善，也要和1pp事件分开。\n\n'
 text+='## B：同成本随机完整训练\n\n每个任务固定200个随机排列，seed=20261030，NumPy PCG64及SeedSequence派生方式、完整600个排列在[plan.json](plan.json)与[orders.json](orders.json)中。先执行prepare，只从缓存构造任务/ID，不按质量或成本生成顺序；同任务两预算使用同200个排列以配对，但每次都建立新环境独立回放，没有借大预算轨迹给小预算提供信息。\n\n'
 text+='两个预算分别直接取原SH、SureStop的recorded_training_seconds，属于事后匹配，不是前瞻盲验证。策略只给出下一个ID；环境在该ID被请求后用其缓存成本模拟完成时刻。预算不足时消耗全部余额，不返回该候选终点，立即停止，不跳过它寻找便宜候选。已完成候选中验证终点最佳者才可推荐。无完成候选则无推荐、任务失败，遗憾undefined；排序/CDF按+∞保留，分母始终200。分位数取全部200结果的逆经验CDF（nearest-rank），不插值、不排除无推荐。\n\n'
 text+='| 固定任务/预算 | 预算秒 | 随机遗憾Q05 / 中位 / Q95 pp | 保留近优/200 | 无推荐/200 | 完成数min / 中位 / max | 实际支出范围秒 |\n|---|---:|---|---:|---:|---|---|\n'
 def fmt(x):return x if isinstance(x,str) else f'{x:.5f}'
 for z in summaries:
  text+=f"| {z['task']} / {z['budget_reference']} | {z['budget_seconds']:.3f} | {fmt(z['regret_q05_pp'])} / {fmt(z['regret_median_pp'])} / {fmt(z['regret_q95_pp'])} | {z['near_retained_count']}/200 | {z['no_recommendation_count']}/200 | {z['n_completed_min']} / {z['n_completed_median']} / {z['n_completed_max']} | {z['actual_spent_min_seconds']:.3f}–{z['actual_spent_max_seconds']:.3f} |\n"
 text+='\n[全部1200次回放](random_budget_comparison.csv)包含完成ID、未完成ID及其已付成本、支出、推荐、遗憾和失败；[分布汇总](random_summary.json)还给出最小/最大/Q25/Q75、仅有推荐者的均值（明确是条件均值）及完成数均值。没有把200个随机顺序当新增独立任务。\n\n'
 text+='| 固定任务/原方法 | 原方法遗憾pp | 随机更好 / 相同 / 更差（分母200） | 随机ECDF在原方法遗憾处F(r) | 原方法完成数 |\n|---|---:|---|---:|---:|\n'
 for z in summaries:
  text+=f"| {z['task']} / {z['budget_reference']} | {z['original_method_regret_pp']:.6f} | {z['random_strictly_better_count']} / {z['random_tie_count']} / {z['random_strictly_worse_count']} | {z['original_method_regret_cdf_rank']:.3f} | {z['original_method_n_completed']} |\n"
 text+='\nF(r)是随机回放遗憾不高于原方法的比例，越小表示原结果越难由该随机基线达到；它不是p值、置信区间或任务总体风险保证。同池近优可能很多，因此“随机保留近优”与“随机恰好达到最佳终点”不能混说。\n\n'
 text+='## 归因结论与限制\n\n'
 for a in attrs:
  zs=[z for z in summaries if z['task']==a['task']]
  text+=f"- **{a['task']}**：同一32组已{'能' if a['cal_retains_near'] else '不能'}解释1pp近优保留；后续实际提供{a['incremental_best_loss_improvement_pp']:.6f}pp改善、支付{a['later_added_cost_seconds']:.3f}秒。随机在SH预算下近优保留{100*zs[0]['near_retained_fraction']:.1f}%，在SureStop预算下{100*zs[1]['near_retained_fraction']:.1f}%；原策略在各自预算下均保留近优。更细的终点优势由上表胜/平/负区分。\n"
 text+='\nA把已完成参考本身的收益与后续新增选择收益/成本分开；B回答同样实际预算下的随机完整训练能解释多少。它们不是对“是否使用前缀”的随机化因果实验，且没有单独固定完成数、开销及候选机会来识别纯信息效应。SH与随机的差异只能作为这三个固定池中前缀指导资源分配的描述性证据。SureStop在32组之外的改善也不能一概归功于预测器。没有据结果换预算、增种子、调阈值或扩大任务。\n\n'
 text+='原策略结果、0/3失败记录、alpha/tau/1pp规则及原停止决定均不改。补充完成即停止，不恢复新算法开发或正式评价。\n\n'
 text+='![事后同成本比较](comparison.png)\n\n左图CDF分母200，无推荐质量在+∞，不画成有限点；横轴0–1pp线性，之后对数。虚线是原方法终点遗憾，圆点是其在随机CDF的位置，黑点线为同一32组遗憾。右图实色随机比例来自200个顺序，斜线条是单个原策略/32组观测0或1，不是可交换的独立样本或概率保证。\n\n'
 text+='## 重放与实际版本\n\n'
 fence=chr(96)*3
 text+=fence+'powershell\nSet-Location D:\\LCStop_20261029_v1\n$env:PYTHONDONTWRITEBYTECODE=1\n$env:OMP_NUM_THREADS=1\n.\\.venv\\Scripts\\python.exe -B analysis_addendum_v1\\run_addendum.py prepare\n.\\.venv\\Scripts\\python.exe -B analysis_addendum_v1\\run_addendum.py run\n'+fence+'\n\n'
 text+='上述prepare/run均在本次实际执行成功。入口拒绝覆盖已有plan/输出；如需重放，先将本补充目录复制成新的同级目录，保留原始版本后在副本执行（副本中的既有输出须由使用者妥善归档），不要直接覆盖本轮结果。程序依据自身目录定位同一研究根目录；不调用原replay.py或其他历史命令。\n\n'
 text+=f"Python {v['python'].splitlines()[0]}；NumPy {v['numpy']}；ijson {v['ijson']}；Matplotlib {v['matplotlib']}。脚本SHA256={v['script_sha256']}，排列SHA256={v['orders_sha256']}。prepare CPU {v['prepare_cpu_seconds']:.6f}秒，分析/作图进程CPU {v['analysis_process_cpu_seconds']:.6f}秒，合计{v['total_measured_cpu_seconds']:.6f}秒，限额600秒。输入/实际环境详情见[run_manifest.json](run_manifest.json)。\n\n"
 text+='只核对了本次读取的缓存、六个结果、两个原策略代码及原规则前后指纹一致；不声称审计了整个研究目录。缓存物理上包含六任务，流式选择仅构造三个指定任务对象，其他任务数值令牌跳过，不进入本次计算、上下文、图表或汇总；未打开raw归档、旧CABOMB或旧隔离数据。部分成本/身份缺件会报错，不补默认值。本次全部必需字段可用。\n\n'
 text+='合成实现检查：'+ '；'.join(v['checks'])+'。这些只验证预算/可见性语义，不是统计独立验证。\n'
 (OUT/'addendum.md').write_text(text,encoding='utf-8')

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['prepare','run']:raise SystemExit('Use prepare or run')
 if sys.argv[1]=='prepare':prepare()
 else:run()
