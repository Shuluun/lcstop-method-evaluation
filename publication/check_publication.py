"""Static publication-only checks: no research script imports or execution."""
from pathlib import Path
import ast,csv,json,hashlib,re,stat
R=Path(__file__).resolve().parents[1]
SRC=Path(r'D:\LCStop_20261029_v1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
def walk(d):
    for p in d.iterdir():
        if p.name in ['.git','.cache','__pycache__']:continue
        if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ValueError('reparse point in publication')
        if p.is_dir():walk(p)
        else:files.append(p)
walk(R)
oversize=[p.relative_to(R).as_posix() for p in files if p.stat().st_size>=100*1024**2]
blocked=[p.relative_to(R).as_posix() for p in files if p.suffix.lower() in ['.zip','.pdf','.pem','.key'] or '.venv' in p.parts]
patterns={
 'github_pat':r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
 'private_key':r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
 'aws_access_key':r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'google_api_key':r'\bAIza[A-Za-z0-9_-]{30,}\b',
 'slack_token':r'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
 'authorization_bearer':r'(?i)authorization\s*[:=]\s*["\x27]?(?:bearer|token)\s+[A-Za-z0-9._-]{16,}',
}
findings=[];personal=[];py=[]
for p in files:
    if p.suffix in ['.png']:continue
    text=p.read_text(encoding='utf-8-sig')
    for kind,pat in patterns.items():
        # Scanner source strings cannot match complete credential formats themselves.
        for m in re.finditer(pat,text):findings.append({'file':p.relative_to(R).as_posix(),'line':text.count('\n',0,m.start())+1,'kind':kind})
    for m in re.finditer(r'(?i)(?:[A-Z]:[\\/]+Users[\\/][^\s"<>]+|/home/[A-Za-z0-9_.-]+/)',text):
        personal.append({'file':p.relative_to(R).as_posix(),'line':text.count('\n',0,m.start())+1})
    if p.suffix=='.py':
        ast.parse(text,filename=str(p));compile(text,str(p),'exec');py.append(p.relative_to(R).as_posix())
# Only first-party entry documentation; bundled upstream README links can target omitted upstream docs.
docs=['README.md','README_research_original.md','research_note.md','docs/REPRODUCIBILITY.md','docs/DATA_AND_SOURCES.md','publication/RELEASE_NOTES.md','analysis_addendum_v1/addendum.md']
broken=[]
for name in docs:
    p=R/name;text=p.read_text(encoding='utf-8')
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
        if re.match(r'^[a-zA-Z]+://',target) or target.startswith('#'):continue
        target=target.split('#')[0].replace('%20',' ')
        if not (p.parent/target).exists():broken.append({'file':name,'target':target})
rows=list(csv.DictReader((R/'publication/source_manifest.csv').open(encoding='utf-8')))
copy_mismatch=[x['published_relative'] for x in rows if sha(R/x['published_relative'])!=x['published_sha256']]
protected=json.loads((R/'publication/source_protection.json').read_text())
changed=[name for name,h in protected['before_sha256'].items() if sha(SRC/name)!=h]
status='PASS' if not any([oversize,blocked,findings,personal,broken,copy_mismatch,changed]) else 'FAIL'
out=dict(status=status,scope='Static packaging checks only, not scientific recalculation or a guarantee that no secret can exist',
 files=len(files),bytes=sum(p.stat().st_size for p in files),largest_bytes=max(p.stat().st_size for p in files),
 source_files_compared=len(protected['before_sha256']),source_files_changed=changed,
 source_hash_scope=protected['scope'],copied_files_mismatched=copy_mismatch,python_files_ast_compiled=len(py),
 over_100_mib=oversize,prohibited_files=blocked,credential_pattern_findings=findings,unnecessary_personal_paths=personal,
 first_party_document_links_broken=broken,
 scientific_scripts_executed=False,dependency_installation=False,model_training=False,policy_replay=False,raw_archive_opened=False)
(R/'publication/publication_check.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
if status!='PASS':raise SystemExit(1)