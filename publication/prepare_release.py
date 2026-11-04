"""Publication-only preparation. Never executes research scripts."""
from pathlib import Path
import json,hashlib,csv,stat,shutil,re
SRC=Path(r'D:\LCStop_20261029_v1')
DST=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(p,root):
    if not p.is_relative_to(root): raise ValueError('outside source root')
    for q in [p,*list(p.parents)[:len(p.parts)-len(root.parts)]]:
        if q.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError('reparse point excluded: '+str(q))
    if not p.is_file(): raise FileNotFoundError(p)
rootfiles=['check_causality.py','correct_unit_cache.py','download_full.py','extract_selected.py','json_adapter.py','plot_results.py','policies.py','public_io.py','replay.py','verify_delivery.py','requirements.txt','research_note.md','pilot_rules.md']
datafiles=['data/metafeatures.json','data/selected_validation.json','data/selected_validation_v2_units.json']
sources=['acquisition.jsonl','curve_schema_metadata.json','environment.json','environment_setup.json','exposure.csv','extraction_summary.json','failures.jsonl','figshare_11604705.json','figshare_11662422.json','figshare_11662488.json','figshare_12408707.json','full_archive_download.json','lcbench_figshare_articles.json','lcbench_project.json','lightweight_archive_members.json','pilot_rules_before_unit_fix.md','read_scope.json','schema_probe_metadata.json','selection.json','selection_version.json','source_snapshots.json','three_seed_archive_members.json','unit_correction.json']
tasks=['volkert','higgs','mfeat-factors','car','christine','kr-vs-kp']
methods=['full','sh','linear','surestop','taskmax']
resultfiles=[f'results/{t}__{m}.json' for t in tasks for m in methods]
resultfiles+=['results/'+n for n in ['pilot_results.json','per_task.csv','plot_runtime.json','figure_case.json','implementation_checks.json','document_check.json','delivery_check.json']]
resultfiles+=[f'results/attempt_01_unit_fail/{t}__{m}.json' for t in tasks for m in methods]
resultfiles+=['results/attempt_01_unit_fail/'+n for n in ['pilot_results.json','per_task.csv','plot_runtime.json','figure_case.json']]
figs=[f'figures/{a}{n}.png' for a in ['','attempt_01_unit_fail/'] for n in ['risk_cost','cost_accounting','failure_case']]
add=['addendum.md','attribution.csv','random_budget_comparison.csv','comparison.png','orders.json','plan.json','random_summary.json','run_manifest.json','run_addendum.py','replay_addendum.py','delivery_check.json']
verified=['addendum.md','attribution.csv','random_budget_comparison.csv','comparison.png','orders.json','plan.json','random_summary.json','run_manifest.json','replay_check.json','prepare.log','run.log']
pairs=[(x,x) for x in rootfiles+datafiles+['sources/'+n for n in sources]+resultfiles+figs]
pairs+=[('README.md','README_research_original.md')]
pairs += [('analysis_addendum_v1/'+n,'analysis_addendum_v1/'+n) for n in add]
pairs += [('analysis_addendum_v1/replay_verification_v1/'+n,'analysis_addendum_v1/replay_verification_v1/'+n) for n in verified]
pairs += [(x,x) for x in ['sources/repos/ACNoonan/surestop/src/surestop/core.py','sources/repos/ACNoonan/surestop/LICENSE','sources/repos/ACNoonan/surestop/README.md','sources/repos/ACNoonan/surestop/tree.json']]
pairs += [('sources/repos/automl/LCBench/LICENSE','licenses/LCBench-Apache-2.0.txt')]
if (DST/'publication/source_manifest.csv').exists(): raise FileExistsError('Publication already prepared')
protected={str(SRC/'AGENTS.md'):sha(SRC/'AGENTS.md')}
rows=[]
for a,b in pairs:
    p=SRC/a;safe(p,SRC)
    if p.stat().st_size>=100*1024**2: raise ValueError('100 MiB file excluded')
    protected[str(p)]=sha(p)
for a,b in pairs:
    p=SRC/a;q=DST/b
    if q.exists(): raise FileExistsError(q)
    q.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,q)
    change='byte-identical'
    if b in ['research_note.md','analysis_addendum_v1/addendum.md','analysis_addendum_v1/replay_verification_v1/addendum.md']:
        txt=q.read_text(encoding='utf-8')
        txt=txt.replace(r'Set-Location D:\LCStop_20261029_v1','Set-Location <your-clone-directory>')
        txt=txt.replace(chr(96)+r'D:\LCStop_20261029_v1'+chr(96),chr(96)+'<original LCStop workspace>'+chr(96))
        txt=txt.replace(chr(96)+r'D:\DCABOMB_Bstar_20261026'+chr(96),chr(96)+'<excluded legacy workspace>'+chr(96))
        q.write_text(txt,encoding='utf-8',newline='\n')
        change='documentation only: replace machine-local locations with descriptive placeholders'
    rows.append(dict(source_relative=a,published_relative=b,bytes=p.stat().st_size,source_sha256=sha(p),published_sha256=sha(q),change=change))
with (DST/'publication/source_manifest.csv').open('x',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(DST/'publication/source_protection.json').write_text(json.dumps({'scope':'whitelisted source files plus AGENTS only; not the raw archive, environment or whole disk','before_sha256':{str(Path(k).relative_to(SRC)).replace('\\','/'):v for k,v in protected.items()},'all_match_after_copy':all(sha(Path(k))==v for k,v in protected.items())},indent=2),encoding='utf-8')
(DST/'publication/release_identity.json').write_text(json.dumps({'kind':'LCStop private GitHub publication copy','source':'LCStop_20261029_v1','version':1,'source_final_delivery_v1_exists':(SRC/'final_delivery_v1').exists(),'scientific_recalculation_in_this_publication':False,'source_environment_modified':False},indent=2),encoding='utf-8')
(DST/'.gitignore').write_text("""# Local environments, credentials and runtime outputs
.venv/
venv/
.env
.env.*
!.env.example
*.pem
*.key
**/__pycache__/
*.py[cod]
.cache/
**/.cache/
data/bench_full.zip
data/*.part
*.zip
*.pdf
reproductions/
publication/local_*
# Historical outputs are explicitly versioned; new runs belong in reproductions/.
""",encoding='utf-8')
(DST/'.gitattributes').write_text('* -text\n',encoding='utf-8')
print(json.dumps({'copied_files':len(rows),'copied_bytes':sum((DST/r['published_relative']).stat().st_size for r in rows),'source_files_unchanged':all(sha(Path(k))==v for k,v in protected.items()),'largest':sorted([(r['published_relative'],(DST/r['published_relative']).stat().st_size) for r in rows],key=lambda x:x[1],reverse=True)[:5]}))