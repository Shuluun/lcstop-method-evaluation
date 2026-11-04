"""Development-only figures; no confidence/coverage claims from three task demonstrations."""
from pathlib import Path
import json,os,time
PLOT_WALL_START=time.perf_counter()
R=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(R/'.cache/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
NODES=np.array([1,5,15,30,50]);METHODS=['full','sh','linear','surestop','taskmax']
LABELS=['Full training','Fixed-rung SH','Linear prefix','SureStop (original)','Task-max (n=3)']
def main():
 d=json.loads((R/'results/pilot_results.json').read_text());data=json.loads((R/'data/selected_validation_v2_units.json').read_text());figdir=R/'figures';figdir.mkdir(exist_ok=True)
 rows=[r for r in d['rows'] if r['role']=='development_demonstration'];s=d['summary']
 fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
 for i,m in enumerate(METHODS):
  rs=[r for r in rows if r['method']==m];xs=[100*(1-r['relative_recorded_cost']) for r in rs];ys=[r['all_near_optimal_lost'] for r in rs]
  ax[0].scatter(xs,np.array(ys)+(i-2)*.025,s=30,alpha=.45,color=plt.get_cmap('tab10')(i))
  ax[0].scatter([np.mean(xs)],[np.mean(ys)],s=95,marker='X',label=LABELS[i],color=plt.get_cmap('tab10')(i))
  ax[1].plot(xs,[r['final_validation_regret_pp'] for r in rs],'o',label=LABELS[i],color=plt.get_cmap('tab10')(i))
 ax[0].set(xlabel='Recorded training cost saved (%)',ylabel='All near-optimal candidates lost (0/1)',title='Tasks (vertical display jitter); X: task mean',ylim=(-.1,1.15));ax[0].legend(fontsize=8)
 ax[1].set(xlabel='Recorded training cost saved (%)',ylabel='Final validation regret (percentage points)',title='Development only: 3 tasks, no formal risk bound')
 fig.savefig(figdir/'risk_cost.png',dpi=170);plt.close(fig)
 fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained');x=np.arange(5);bottom=np.zeros(5)
 for field,label in [('calibration_training_seconds','Within-task calibration'),('prefix_training_seconds','Prefix training'),('completion_training_seconds','Candidate completion')]:
  vals=[sum(r[field] for r in rows if r['method']==m)/3600 for m in METHODS];ax.bar(x,vals,bottom=bottom,label=label);bottom+=vals
 aux=[d['auxiliary_task_calibration_training_seconds']/3600 if m=='taskmax' else 0 for m in METHODS];ax.bar(x,aux,bottom=bottom,label='Auxiliary 3-task calibration (unamortized)',hatch='//',alpha=.65)
 ax.set(xticks=x,xticklabels=LABELS,ylabel='Recorded training hours (sum over 3 demonstration tasks)',title='Stored benchmark runtime; not local replay CPU or measured speed-up');ax.legend(fontsize=8)
 fig.savefig(figdir/'cost_accounting.png',dpi=170);plt.close(fig)
 # Predeclared display rule: first failing demonstration task, with method priority SH,linear,SureStop.
 case=next((r for t in data['selection']['tasks'][3:] for m in ['sh','linear','surestop'] for r in rows if r['task']==t and r['method']==m and r['all_near_optimal_lost']),None)
 if case:
  items=data['tasks'][case['task']];res=json.loads((R/'results'/(case['task']+'__'+case['method']+'.json')).read_text());Y=np.array([np.mean(z['seed_loss'],axis=0) for z in items]);ids=[z['id'] for z in items];best=Y[:,-1].min();near=np.where(Y[:,-1]<=best+1)[0]
  fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
  for row in Y:ax.plot(NODES,row,color='lightgray',alpha=.35,lw=.8)
  for k in near:
   cid=ids[k];ax.plot(NODES,Y[k],color='tab:red',alpha=.7,lw=1.5);j=res['positions'][cid];ax.plot(NODES[j],Y[k,j],'rx',ms=9)
  k=ids.index(case['selected']);ax.plot(NODES,Y[k],color='tab:blue',lw=2,label='Selected completed candidate');ax.plot([],[],color='tab:red',label='Near-optimal at endpoint (offline only)');ax.plot([],[],'rx',label='Actual stopping checkpoint')
  ax.set(xlabel='Epoch',ylabel='Validation balanced error (percentage points)',title=case['task']+' / '+case['method']+': all near-optimal candidates stopped');ax.legend(fontsize=8)
  fig.savefig(figdir/'failure_case.png',dpi=170);plt.close(fig);case_info={k:case[k] for k in ['task','method','n_near_optimal','final_validation_regret_pp']};case_info['scope']='post-replay development failure illustration; not policy input'
 else:
  fig,ax=plt.subplots(figsize=(8,4),layout='constrained');ax.plot(NODES,[5,5,5,5,5],'-o',label='Early leader');ax.plot(NODES,[90,90,90,90,0],'-o',label='Hidden late bloomer');ax.plot(1,90,'rx',ms=12);ax.set(xlabel='Epoch',ylabel='Synthetic validation loss',title='Synthetic implementation counterexample (not LCBench result)');ax.legend();fig.savefig(figdir/'failure_case.png',dpi=170);plt.close(fig);case_info={'scope':'synthetic only; no observed task failure in three demos'}
 (R/'results/figure_case.json').write_text(json.dumps(case_info,indent=2));(R/'results/plot_runtime.json').write_text(json.dumps(dict(wall_seconds=time.perf_counter()-PLOT_WALL_START,cpu_seconds=time.process_time(),scope='figure rendering only'),indent=2));print(json.dumps(case_info))
if __name__=='__main__':main()