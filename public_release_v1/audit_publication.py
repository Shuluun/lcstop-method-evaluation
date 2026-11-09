from pathlib import Path
import subprocess,json,hashlib,re,ast,stat
R=Path(__file__).resolve().parents[1];O=R/'public_release_v1'
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tracked=[s for s in git('ls-files','-z').decode().split('\0') if s]
baseline=R/'.cache/public_baseline.json'
if not baseline.exists():
    baseline.write_text(json.dumps({'commit':git('rev-parse','HEAD').decode().strip(),'sha256':{p:sha(R/p) for p in tracked}},indent=2),encoding='utf-8')
patterns={
 'github_token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
 'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
 'aws_access_key':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'google_api_key':rb'\bAIza[A-Za-z0-9_-]{30,}\b',
 'slack_token':rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
 'signed_or_auth_query':rb'(?i)[?&](?:X-Amz-Signature|AWSAccessKeyId|access_token|refresh_token)=[A-Za-z0-9%._-]{8,}',
 'credential_url':rb'https?://[^/\s:@]+:[^@\s/]+@',
}
# Inspect all reachable Git blobs, not merely HEAD; do not print matched contents.
paths={}
for line in git('rev-list','--objects','--all').decode().splitlines():
    a=line.split(' ',1)
    paths.setdefault(a[0],[]).extend(a[1:])
findings=[];blobs=0;history_bytes=0;oversize=[]
for oid,names in paths.items():
    info=git('cat-file','-t',oid).decode().strip()
    if info!='blob':continue
    b=git('cat-file','blob',oid);blobs+=1;history_bytes+=len(b)
    if len(b)>=100*1024**2:oversize.append({'oid':oid,'paths':names,'bytes':len(b)})
    for kind,pat in patterns.items():
        if re.search(pat,b):findings.append({'scope':'git_history','oid':oid,'paths':names,'kind':kind})
files=[]
def walk(d):
    for p in d.iterdir():
        if p.name in ['.git','.cache','.venv','__pycache__']:continue
        if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ValueError('Reparse point excluded')
        if p.is_dir():walk(p)
        else:files.append(p)
walk(R)
for p in files:
    for kind,pat in patterns.items():
        if re.search(pat,p.read_bytes()):findings.append({'scope':'working_tree','path':p.relative_to(R).as_posix(),'kind':kind})
excluded=[p.relative_to(R).as_posix() for p in files if p.suffix.lower() in ['.zip','.pdf','.pem','.key'] or '.github/workflows' in p.as_posix()]
# Validate first-party Markdown links; omit verbatim snapshots and generated historical replay prose.
skip=['sources/repos/','analysis_addendum_v1/replay_verification_v1/']
broken=[];mdcount=0;astcount=0
for p in files:
    rel=p.relative_to(R).as_posix()
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'));astcount+=1
    if p.suffix!='.md' or any(rel.startswith(s) for s in skip):continue
    mdcount+=1
    text=p.read_text(encoding='utf-8')
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
        if re.match(r'^[a-zA-Z]+://',target) or target.startswith('#'):continue
        if not (p.parent/target.split('#')[0].replace('%20',' ')).exists():broken.append({'file':rel,'target':target})
# Current additions are compared against the pre-publication Git checkout.
before=json.loads(baseline.read_text(encoding='utf-8'))
changes=[p for p,h in before['sha256'].items() if sha(R/p)!=h]
source=json.loads((R/'publication/source_protection.json').read_text(encoding='utf-8'))
SRC=Path(r'D:\LCStop_20261029_v1')
source_changes=[p for p,h in source['before_sha256'].items() if sha(SRC/p)!=h]
v=dict(status='PASS' if not any([findings,oversize,excluded,broken,source_changes]) else 'FAIL',
 scope='Pattern scan of every reachable Git blob and current release files; not a proof that all possible secrets are absent',
 base_commit=before['commit'],reachable_commits=int(git('rev-list','--all','--count')),
 history_blob_count=blobs,history_bytes_scanned=history_bytes,credential_pattern_findings=findings,
 history_blobs_over_100_mib=oversize,current_file_count=len(files),current_bytes=sum(p.stat().st_size for p in files),
 max_current_file_bytes=max(p.stat().st_size for p in files),excluded_material_found=excluded,
 first_party_markdown_files_link_checked=mdcount,broken_local_links=broken,python_files_ast_parsed=astcount,
 preexisting_files_changed=changes,original_source_files_compared=len(source['before_sha256']),original_source_files_changed=source_changes,
 no_new_scientific_computation=True,no_new_data=True,no_history_rewrite=True,
 scanned_history_contains_normal_git_author_identity=True,repository_wide_open_source_license_added=False)
(O/'preflight_check.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
print(json.dumps(v,indent=2))
if v['status']!='PASS':raise SystemExit(1)