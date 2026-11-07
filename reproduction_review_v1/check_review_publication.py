from pathlib import Path
import json,re,ast,hashlib,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reproduction_review_v1'
# Redact machine-personal tool locations only in new execution logs, without altering outcomes.
redacted=[]
for p in O.rglob('*.log'):
    t=p.read_text(encoding='utf-8')
    new,n=re.subn(r'(?i)[A-Z]:[\\/]+Users[\\/]+[^\\/\s]+[\\/]+[^\s"<>]*','<local-tool-path>',t)
    if n:p.write_text(new,encoding='utf-8');redacted.append({'file':p.relative_to(O).as_posix(),'occurrences':n})
p=O/'publication_adjustments.json';v=json.loads(p.read_text(encoding='utf-8'))
v.update(new_log_personal_paths_redacted=redacted,dependency_log_shell_note='PowerShell formats uv stderr as NativeCommandError text; uv exit code was zero and isolated imports/replays succeeded. Original stdout/stderr wording otherwise retained.')
p.write_text(json.dumps(v,indent=2),encoding='utf-8')
p=O/'README.md';text=p.read_text(encoding='utf-8')
text+='\n安装日志保留了PowerShell对uv标准错误流的包装格式（含NativeCommandError字样）；uv实际退出码为0，依赖导入与复现成功。发布前只将新日志中的个人工具路径替换为占位符，没有删除失败结果或改写科学输出。\n'
p.write_text(text,encoding='utf-8')
# Verify historic tracked scientific files (only intentional documentation updates allowed).
plan=json.loads((O/'plan.json').read_text(encoding='utf-8'))
changed=[n for n,h in plan['tracked_sha256_before'].items() if hashlib.sha256((R/n).read_bytes()).hexdigest()!=h]
allowed=['README.md','docs/REPRODUCIBILITY.md']
if sorted(changed)!=sorted(allowed):raise ValueError('Unexpected historical change: '+str(changed))
inputs=json.loads((R/'publication/source_protection.json').read_text())
SRC=Path(r'D:\LCStop_20261029_v1')
source_changed=[n for n,h in inputs['before_sha256'].items() if hashlib.sha256((SRC/n).read_bytes()).hexdigest()!=h]
if source_changed:raise ValueError('Original source changed')
files=[R/n for n in allowed]+[p for p in O.rglob('*') if p.is_file()]
findings=[];broken=[];oversize=[];parsed=[]
for p in files:
    rel=p.relative_to(R).as_posix()
    if p.stat().st_size>=100*1024**2:oversize.append(rel)
    if p.suffix=='.png':continue
    t=p.read_text(encoding='utf-8-sig')
    pats=[r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',r'(?i)[A-Z]:[\\/]+Users[\\/]+[A-Za-z0-9_.-]+[\\/]']
    for i,pat in enumerate(pats):
        if re.search(pat,t):findings.append({'file':rel,'pattern':i})
    if p.suffix=='.py':ast.parse(t);compile(t,str(p),'exec');parsed.append(rel)
    if p.suffix=='.md':
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',t):
            if re.match(r'^[a-zA-Z]+://',link) or link.startswith('#'):continue
            if not (p.parent/link.split('#')[0]).exists():broken.append({'file':rel,'target':link})
v=dict(status='PASS' if not findings and not broken and not oversize else 'FAIL',scope='new reproduction additions and two intentionally updated documents; no historical scientific recalculation beyond reported replay',
 reviewed_files=len(files),reviewed_bytes=sum(p.stat().st_size for p in files),python_helpers_ast_compiled=parsed,
 credential_and_personal_path_findings=findings,broken_relative_links=broken,files_over_100_mib=oversize,
 original_source_files_compared=len(inputs['before_sha256']),original_source_files_changed=source_changed,
 intentionally_updated_historical_documents=changed,historical_code_cache_results_unchanged=True,
 figures_visually_checked=['figures/risk_cost.png','figures/failure_case.png','replayed_addendum/comparison.png'],
 raw_archive_opened=False,formal_test_started=False,new_training=0,github_visibility_required='PRIVATE')
(O/'publication_check.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
print(json.dumps(v,indent=2))
if v['status']!='PASS':raise SystemExit(1)