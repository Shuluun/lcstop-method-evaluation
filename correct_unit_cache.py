"""Explicit unit correction of the preserved first-attempt whitelist cache.
Original archive and first cache unchanged. This is not a new sample or threshold.
"""
from pathlib import Path
import json,hashlib,time
import numpy as np
R=Path(__file__).resolve().parent
def main():
 src=R/'data/selected_validation.json';dst=R/'data/selected_validation_v2_units.json'
 if dst.exists():raise FileExistsError('Corrected input already exists; no overwrite')
 d=json.loads(src.read_text());allx=[];maxround=0
 for items in d['tasks'].values():
  for item in items:
   old=np.asarray(item['seed_loss'],float);accuracy=100-old
   assert np.all((accuracy>=0)&(accuracy<=1))
   assert np.array_equal(accuracy,accuracy.astype(np.float32).astype(float)), 'recovery not on float32 grid; return to raw archive'
   assert np.array_equal(100-accuracy,old), 'old cache roundtrip failed'
   item['seed_accuracy_fraction']=accuracy.tolist()
   item['seed_loss']=(100*(1-accuracy)).tolist();allx.extend(accuracy.ravel().tolist())
 d['metric']='100 * (1 - Train/val_balanced_accuracy)';d['unit']='percentage points'
 d['unit_correction']={'source_cache_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'raw_stored_unit':'fraction [0,1]','loss_conversion':'100*(1-accuracy_fraction)','evidence':'all selected cached values in [0,1]; all restored values exactly on float32 grid, zero old-cache roundtrip error; standard balanced-accuracy definition is [0,1]','recovery_note':'Accuracy restored as 100-old_loss from preserved cache, not a new raw extraction. Original archive remains authoritative. All recoveries on float32 grid with exact cached roundtrip; no claim of bytewise raw JSON recovery. At most about 1.5e-12 pp worst-case double arithmetic bound if original precision was finer.','metadata_selection_changed':False,'configuration_or_seed_changed':False,'tau_loss_pp':20,'epsilon_loss_pp':1,'alpha':.1,'raw_recovered_range':[min(allx),max(allx)],'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 dst.write_text(json.dumps(d))
 (R/'sources/unit_correction.json').write_text(json.dumps(d['unit_correction'],indent=2))
 print(json.dumps(d['unit_correction'],indent=2))
if __name__=='__main__':main()
