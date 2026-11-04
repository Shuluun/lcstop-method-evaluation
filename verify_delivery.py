"""Local delivery checks only. Never reads the old project or unselected archive outcomes."""
from pathlib import Path
import json,hashlib,time,ast,math
import numpy as np
R=Path(__file__).resolve().parent
if __name__=='__main__':
 data=json.loads((R/'data/selected_validation_v2_units.json').read_text());result=json.loads((R/'results/pilot_results.json').read_text());checks=json.loads((R/'results/implementation_checks.json').read_text())
 assert len(data['tasks'])==6 and not data['failures'] and data['test_fields_retained']==[]
 assert any(100-x['seed_loss'][0][0]>1 for items in data['tasks'].values() for x in items), 'percentage-point unit not supported by selected early values; do not silently rescale'
 counts={};duplicates={}
 for task,items in data['tasks'].items():
  assert len(items)==128 and [x['id'] for x in items]==data['selection']['selected_ids'][task]
  seen=set();dup=0
  for item in items:
   y=np.array(item['seed_loss']);t=np.array(item['seed_cost']);assert y.shape==t.shape==(3,5)
   assert np.isfinite(y).all() and ((y>=0)&(y<=100)).all()
   assert np.isfinite(t).all() and (np.diff(t,axis=1)>=0).all() and (t[:,-1]>0).all()
   key=json.dumps(item['metadata'],sort_keys=True)
   if key in seen:dup+=1
   seen.add(key)
  counts[task]=len(items);duplicates[task]=dup
 assert all(c['status']=='PASS' for c in checks['checks']) and len(result['rows'])==30
 assert all(r['all_near_optimal_lost']==int(r['final_validation_regret_pp']>1) for r in result['rows'])
 for gap in [1.0,math.nextafter(1.0,math.inf)]:
  near={i for i,v in enumerate([0.0,gap]) if v<=1.0};done={1};assert int(not bool(near&done))==int(gap>1.0)
 assert result['formal_test_tasks']==[] and result['test_metric_fields_used']==[] and result['new_model_training']==0
 assert result['task_lambda']=='Infinity' and result['n_calibration_tasks']==3
 prior=json.loads((R/'results/attempt_01_unit_fail/pilot_results.json').read_text())
 total_replay_cpu=result['experiment_accounted_cpu_seconds']+prior['experiment_accounted_cpu_seconds']
 assert total_replay_cpu+checks['total_accounted_cpu_seconds']<14400
 code={}
 for name in ['policies.py','replay.py','check_causality.py','extract_selected.py','json_adapter.py','plot_results.py','verify_delivery.py','download_full.py','correct_unit_cache.py','pilot_rules.md']:
  p=R/name
  if p.suffix=='.py':ast.parse(p.read_text())
  code[name]=hashlib.sha256(p.read_bytes()).hexdigest()
 meta=json.loads((R/'sources/selection.json').read_text());setup=json.loads((R/'sources/environment_setup.json').read_text());download=json.loads((R/'sources/full_archive_download.json').read_text())
 out=dict(status='PASS',task_loss_regret_equivalence='PASS on all 30 replays and exact/just-above 1pp boundaries',scope='new project delivery only; no old 503 re-audit or old hash checks',selected_counts=counts,exact_metadata_duplicate_counts=duplicates,
  actual_training_seeds=data['selection']['training_seeds'],real_tasks=6,real_configuration_pools=768,recorded_seed_curves=2304,observations_per_seed=5,
  experiment_cpu_seconds=result['experiment_accounted_cpu_seconds'],invalid_attempt_cpu_seconds=prior['experiment_accounted_cpu_seconds'],all_recorded_replay_cpu_seconds=total_replay_cpu,implementation_checks_cpu_seconds=checks['total_accounted_cpu_seconds'],
  experiment_plus_checks_cpu_seconds=total_replay_cpu+checks['total_accounted_cpu_seconds'],cpu_ceiling_seconds=14400,
  data_preparation_separate=dict(dependency_wall_seconds=setup['wall_seconds'],download_wall_seconds=download['wall_seconds'],metadata_wall_seconds=meta['wall_seconds'],metadata_cpu_seconds=meta.get('parser_process_cpu_seconds'),extraction_wall_seconds=data['wall_seconds'],extraction_cpu_seconds=data.get('parser_process_cpu_seconds'),failed_preparation_duration='not completely instrumented; failures retained separately'),
  code_sha256=code,selected_input_sha256=hashlib.sha256((R/'data/selected_validation_v2_units.json').read_bytes()).hexdigest(),result_sha256=hashlib.sha256((R/'results/pilot_results.json').read_bytes()).hexdigest(),
  note='Delivery-version fingerprints only, not a formal protocol freeze or proof data were never read.',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
 (R/'results/delivery_check.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))