"""Public read-only HTTP acquisition. All writes are confined to this new workspace."""
from pathlib import Path
import json,urllib.request,hashlib,datetime,time,sys
ROOT=Path(__file__).resolve().parent
def get(url,name,limit=64_000_000):
    path=(ROOT/name).resolve()
    assert ROOT in path.parents
    if path.exists():return path
    path.parent.mkdir(parents=True,exist_ok=True)
    row=dict(url=url,path=name,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    start=time.perf_counter()
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"LCStop-local-development-audit/1.0"})
        with urllib.request.urlopen(req,timeout=35) as response:
            data=response.read(limit+1)
            if len(data)>limit:raise ValueError("download exceeds predeclared byte limit")
            row.update(resolved_url=response.url,content_type=response.headers.get("content-type",""))
        path.write_bytes(data)
        row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),status="downloaded")
    except Exception as exc:
        row.update(status="failed",error=repr(exc))
    row["wall_seconds"]=time.perf_counter()-start
    with (ROOT/"sources/acquisition.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(row)+"\n")
    print(json.dumps(row),flush=True)
    return path if row["status"]=="downloaded" else None
if __name__=="__main__":
    if sys.argv[1]=="metadata":
        jobs=[
        ("https://api.figshare.com/v2/projects/74151/articles","sources/lcbench_figshare_articles.json"),
        ("https://huggingface.co/api/datasets/syne-tune/lcbench/tree/main?recursive=true","sources/hf_lcbench_files.json"),
        ("https://api.figshare.com/v2/projects/74151","sources/lcbench_project.json"),
        ]
        for u,n in jobs:get(u,n)
    elif sys.argv[1]=="fetch":get(sys.argv[2],sys.argv[3],int(sys.argv[4]) if len(sys.argv)>4 else 64_000_000)