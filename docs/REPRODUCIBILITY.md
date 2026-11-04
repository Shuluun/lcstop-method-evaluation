# Reproduction levels and actual verification status

Run from the repository root with Python3.12 and requirements-replay.txt installed in a fresh environment.
The historical full dependency record remains requirements.txt; pypdf was for paper preparation and is not needed for analysis replay.

## A: already-used small cache and saved results

The recommended wrapper creates a fresh copy under reproductions/<name>/, then runs only within that copy.
It never writes over the checked-in historical results. Names cannot be reused.

~~~powershell
python -B tools/reproduce.py pilot --name pilot_replay_01
python -B tools/reproduce.py addendum --name attribution_replay_01
~~~

Pilot runs the existing check_causality.py, replay.py, plot_results.py and verify_delivery.py in the fresh workspace.
Their historical versions and saved successful records are included. Worker timing is machine-dependent, so new result files are not promised byte-identical.
Addendum calls the existing replay_addendum.py with a new child directory. It recreates the SAME seed20261030 / 200 orders per task and checks the four historical data artifacts for byte equality. It is not a new sample.

Historical evidence:
- [Main delivery check](../results/delivery_check.json), [synthetic checks](../results/implementation_checks.json).
- [Addendum original manifest](../analysis_addendum_v1/run_manifest.json).
- [Previously executed deterministic replay check](../analysis_addendum_v1/replay_verification_v1/replay_check.json).
These are historical evidence, not publication-time reruns.

The wrapper is new publication glue: it was AST/compile checked but NOT executed against the scientific workflow in this publication.
No model training, policy replay, random-order regeneration, outcome evaluation, dependency installation or original script execution occurred during publication.
The old addendum generator contains a machine-local Set-Location example in generated prose; it is not an executable input path. Runtime roots derive from __file__.
The bundled reports replace machine-local locations with descriptive placeholders; commands should be run from the clone root.

## B: official raw archive reconstruction

First obtain the exact v1 archive described in [DATA_AND_SOURCES.md](DATA_AND_SOURCES.md).
No archive is downloaded automatically by the wrapper. Place it at data/bench_full.zip, then:

~~~powershell
python -B tools/reproduce.py raw --name raw_rebuild_01 --archive data/bench_full.zip
~~~

This copies the archive into an isolated workspace, verifies its exact bytes/SHA256, reuses the original fixed sources/selection.json (no reselection),
and runs extract_selected.py extract followed by the same pilot steps. Requires several GB temporary storage and substantial JSON parsing time.
The original historical metadata command is python -B extract_selected.py metadata, but it need not be repeated: selection IDs/seeds are already fixed and versioned.

Direct historical commands, ONLY in a separate scratch copy:
~~~powershell
python -B download_full.py
python -B extract_selected.py metadata
python -B extract_selected.py extract
python -B check_causality.py
python -B replay.py
python -B plot_results.py
python -B verify_delivery.py
~~~

The corrected raw-extraction path was not rerun end-to-end historically or during publication.
Actual current v2 results use correct_unit_cache.py recovery from the saved first-attempt whitelist cache; details and its ~1.5e-12pp conservative arithmetic bound are in sources/unit_correction.json.
To demonstrate that historical correction path, remove ONLY the derived v2 cache in a disposable scratch copy before running correct_unit_cache.py; do not remove or edit checked-in files.

## Limits

- Fresh-environment installation and cross-platform execution were not tested this time.
- Python is an inspectable information-flow interface, not a malicious-code OS sandbox.
- The six tasks are development material; no IID task sampling or general risk claim.
- Empirical time is original elapsed seconds summed over seeds, not current-machine speedup.
- The main SureStop32 candidates remain eligible; addendum never changes the original method.
- The invalid first attempt remains in results/attempt_01_unit_fail and figures/attempt_01_unit_fail; never use its metrics as current results.
- verify_delivery.py has no knowledge of a GitHub upload; its saved PASS is not a release audit or independent scientific validation.
