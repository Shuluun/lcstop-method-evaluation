# LCStop: causal prefix replay development pilot

This is a new workspace, separate from the read-only CABOMB/B*/D0 project.
Start with [research_note.md](research_note.md) for the method audit, real development
results, limits and continuation decision. This directory is not a new formal benchmark.

## Main entry points

Use the new local `.venv` only. No GPU or old CABOMB commands are required.

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OMP_NUM_THREADS='1'
$env:MPLCONFIGDIR="$PWD\.cache\matplotlib"
.\.venv\Scripts\python.exe -B check_causality.py
.\.venv\Scripts\python.exe -B replay.py
.\.venv\Scripts\python.exe -B plot_results.py
```

`replay.py` reads only `data/selected_validation_v2_units.json`. It starts a fresh policy process
for every task and strategy. The worker sees JSON replies containing paid prefixes only;
this is a reviewed information interface, not an OS security sandbox for malicious code.
The offline evaluator owns the hidden endpoints. No test metrics are in the selected file.

To rebuild the local selected input from the official archive (larger data-preparation step):

```powershell
.\.venv\Scripts\python.exe -B download_full.py
.\.venv\Scripts\python.exe -B extract_selected.py metadata
.\.venv\Scripts\python.exe -B extract_selected.py extract
```

The raw 1.81GB zip is preserved unchanged; no 6GB decompressed JSON is written.
`json_adapter.py` handles nonstandard numeric Infinity/NaN tokens during parsing; it
preserves quoted strings, maps numeric nonfinite tokens to null, and never imputes a
required validation/time value. Metadata selection precedes outcome extraction.
Re-running preparation/replay overwrites only derived outputs in this new workspace;
it cannot modify the old project. Use a copied new version directory to retain a run.

## Files and scope

- `pilot_rules.md`: pre-outcome task/configuration selection, endpoint, tolerance and policies.
- `policies.py`: full training, fixed-rung SH, causal linear prefix, unchanged SureStop core,
  and elementary task-max calibration baseline.
- `replay.py`: paid-cost broker, independent workers, evaluator and accounting.
- `check_causality.py`: synthetic invariance, API guards, equivalence and failure checks.
- `results/`: exact per-task results and paid histories; `figures/`: development plots.
- `sources/read_scope.json`: actual paper/code reading depth, not claimed full proof verification.
- `sources/environment.json`, `source_snapshots.json`, `failures.jsonl`: environment,
  public source versions and failures. Downloads carry URL/version/license/hash records.

Only SureStop core is imported from the external source snapshots. CBES GPs, ifBO weights,
MIP solvers, MF-BAI optimizers and the old CABOMB models are not run.
## Unit correction history

Attempt01 was rejected for treating fraction accuracy as percent. Original cache and results/plots are preserved. Current input selected_validation_v2_units.json was produced by the actually executed correct_unit_cache.py path. The corrected full archive extraction path was not re-run. See sources/unit_correction.json for the cache recovery precision limits.

python -B verify_delivery.py also completed successfully. No new formal test set or algorithm claim is created.
