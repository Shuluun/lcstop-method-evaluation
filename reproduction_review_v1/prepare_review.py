from pathlib import Path
import json,hashlib,subprocess,sys
R=Path(__file__).resolve().parents[1]
OUT=R/'reproduction_review_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0')
before={name:sha(R/name) for name in tracked if name}
v=dict(review_date='2026-11-06',status='prepared_before_replay',source_repository='https://github.com/Shuluun/lcstop-method-evaluation',source_commit=commit,
 scope='small-cache reconstruction of published pilot and same-order attribution only',
 tasks=['volkert','higgs','mfeat-factors','car','christine','kr-vs-kp'],demonstration_tasks=['car','christine','kr-vs-kp'],
 selected_configs_per_task=128,recorded_seeds_per_config=3,nodes=[1,5,15,30,50],epsilon_pp=1,alpha=.1,tau_pp=20,
 new_tasks=0,new_models=0,raw_archive_opened=False,formal_test_started=False,private_visibility_required=True,
 pilot_command=['.venv/Scripts/python.exe','-B','tools/reproduce.py','pilot','--name','pilot_replay_01'],
 attribution_command=['.venv/Scripts/python.exe','-B','tools/reproduce.py','addendum','--name','attribution_replay_01'],
 comparison='Exact equality of saved scientific fields, traces, payments and positions; timing-only fields separately excluded. Attribution requires byte-identical four data artifacts.',
 timing_exclusions=['policy_cpu_seconds','online_policy_cpu_seconds','worker_wall_seconds','process_cpu_seconds','calibration_compute_cpu_seconds','task_calibration_compute_cpu_seconds','wall_seconds','experiment_parent_cpu_seconds','policy_child_cpu_seconds','experiment_accounted_cpu_seconds','prepare_cpu_seconds','parser_process_cpu_seconds'],
 figure_requirement='inspect rendered replay figures; identical image bytes not required',
 per_wrapper_wall_timeout_seconds=600,original_pilot_cpu_cap_seconds=14400,attribution_cpu_cap_seconds=600,
 tracked_sha256_before=before)
p=OUT/'plan.json'
with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
print(json.dumps({'source_commit':commit,'tracked_files_protected':len(before),'scientific_work_started':False}))