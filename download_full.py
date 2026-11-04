import urllib.request, time, json, hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
p=R/'data/bench_full.zip'; p.parent.mkdir(exist_ok=True)
if p.exists():
 print('exists',p.stat().st_size)
else:
 t=time.perf_counter(); h=hashlib.sha256(); n=0
 req=urllib.request.Request('https://ndownloader.figshare.com/files/22859435',headers={'User-Agent':'LCStop development pilot'})
 with urllib.request.urlopen(req,timeout=90) as r, p.with_suffix('.part').open('xb') as w:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   n+=len(b)
   if n>1813896086: raise ValueError('size ceiling')
   w.write(b);h.update(b)
   if n//(128*1024*1024)!=(n-len(b))//(128*1024*1024):print('download_MB',round(n/1e6),flush=True)
 if n!=1813896086:raise ValueError('size mismatch')
 p.with_suffix('.part').rename(p)
 row=dict(url='https://ndownloader.figshare.com/files/22859435',doi='10.6084/m9.figshare.12408707.v1',license='Apache-2.0 per official Figshare article',bytes=n,sha256=h.hexdigest(),wall_seconds=time.perf_counter()-t,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),scope='archive download; selected validation/time fields extracted separately')
 (R/'sources/full_archive_download.json').write_text(json.dumps(row,indent=2))
 print(json.dumps(row),flush=True)