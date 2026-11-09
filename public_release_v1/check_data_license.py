from pathlib import Path
import urllib.request,json,hashlib
R=Path(__file__).resolve().parents[1]
url='https://api.figshare.com/v2/articles/12408707/versions/1'
out={'review_date':'2026-11-08','scope':'versioned license metadata only; no learning-curve data','url':url,'web_tool_attempt':'unavailable; direct HTTPS metadata request follows'}
try:
    req=urllib.request.Request(url,headers={'User-Agent':'LCStop-public-release-check/1.0'})
    with urllib.request.urlopen(req,timeout=25) as r:b=r.read(65537)
    if len(b)>65536:raise ValueError('metadata size ceiling')
    d=json.loads(b)
    out.update(status='PASS',response_sha256=hashlib.sha256(b).hexdigest(),response_bytes=len(b),article_id=d['id'],doi=d['doi'],version=d['version'],license=d['license'],files=[{k:x[k] for k in ['id','name','size','download_url']} for x in d['files']])
    assert d['id']==12408707 and d['version']==1 and d['license']['name']=='Apache 2.0'
except Exception as e:
    out.update(status='UNVERIFIED_LIVE',failure_type=type(e).__name__,failure=str(e),fallback='Existing versioned sources/figshare_12408707.json; original license text and attribution preserved')
(R/'public_release_v1/data_license_check.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))