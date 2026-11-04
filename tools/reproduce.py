"""Optional replay entry; writes only a fresh reproductions/<name> scratch tree.
Publication did not execute this wrapper's scientific commands.
"""
from pathlib import Path
import argparse,csv,hashlib,os,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
RAW_SHA='e490969c4f068fc7d96c880f9d3051bc2ae285feae995f6610d6a92092bc1198'
RAW_BYTES=1813896086
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['pilot','addendum','raw'])
    p.add_argument('--name',required=True,help='fresh output name; never overwrite')
    p.add_argument('--archive',type=Path,help='existing official v1 ZIP, required for raw mode')
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.name):p.error('Use a plain output name')
    out=(ROOT/'reproductions'/a.name).resolve()
    if not out.is_relative_to(ROOT/'reproductions') or out.exists():raise FileExistsError('Fresh scratch output required')
    if a.mode=='raw':
        if a.archive is None:p.error('--archive is required; no automatic download')
        archive=a.archive.resolve()
        if archive.is_symlink() or archive.stat().st_size!=RAW_BYTES or digest(archive)!=RAW_SHA:
            raise ValueError('Official raw version/size/hash mismatch')
    out.mkdir(parents=True)
    rows=list(csv.DictReader((ROOT/'publication/source_manifest.csv').open(encoding='utf-8')))
    for row in rows:
        rel=Path(row['published_relative']);src=(ROOT/rel).resolve();dst=out/rel
        if not src.is_relative_to(ROOT) or not dst.resolve().is_relative_to(out):raise ValueError('unsafe path')
        if digest(src)!=row['published_sha256']:raise ValueError('Published input changed: '+str(rel))
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    env=os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(out/'.cache/matplotlib'))
    def run(*args):
        subprocess.run([sys.executable,'-B',*args],cwd=out,env=env,check=True)
    if a.mode=='addendum':
        run('analysis_addendum_v1/replay_addendum.py','--name','publication_replay')
    else:
        if a.mode=='raw':
            shutil.copyfile(archive,out/'data/bench_full.zip')
            run('extract_selected.py','extract')
        for script in ['check_causality.py','replay.py','plot_results.py','verify_delivery.py']:run(script)
    print('Scratch output:',out)
if __name__=='__main__':main()