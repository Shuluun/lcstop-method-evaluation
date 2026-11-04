# LCStop development rules, before inspecting learning-curve values

Old CABOMB/B*/D0 remains STOP / DATA_ONLY, read-only. No formal test pool is created.

## Selection
The official LCBench metafeatures.json lists 35 task names. Sort them by
SHA256("LCStop20261029|" + name), take the first six:
volkert, higgs, mfeat-factors, car, christine, kr-vs-kp.
First three are development calibration tasks, last three are development demonstrations.
These roles do not constitute formal calibration/test data.

On each task, select at most 128 configuration identities by a fixed SHA256 ordering
of metadata IDs using salt LCStop20261029. Read only metadata to establish ID and seed
structure. Use the first three actual training seeds in metadata-sorted order, if available;
do not fabricate missing seeds or count seeds as independent tasks.
All selected runs must belong to the 50-epoch training-horizon experiment.
Do not splice together runs trained with different planned horizons (6/12/25/50).
Configurations failing required support are recorded as unavailable, not replaced by outcomes.

## Target and visibility
Primary validation metric: Train/val_balanced_accuracy, as a percentage; loss=100-accuracy.
If the official schema cannot support this metric/unit/50-epoch mapping, report the gap
before changing the rule. No test metric is allowed in the extracted policy data.
Five observation nodes: epochs [1,5,15,30,50]. No endpoint cherry-picking.
Per configuration, average the three fixed training-seed validation curves at each node;
recorded training cost is the sum of those three training runtimes.
Near-optimal tolerance is exactly 1 percentage point of final mean validation accuracy.
Near-optimal set is defined inside the preselected task/configuration pool at epoch50,
only by the offline evaluator after all policy decisions.
Task failure: no member of that near-optimal set remains to complete epoch50.
Final validation regret: selected completed loss - best pool loss (nonnegative); no completed candidate => undefined.

## Strategies, fixed before computation
1. Full training of all eligible candidates.
2. Synchronous Successive Halving, factor2, at the first four nodes; complete survivors.
   This is a fixed-rung adaptation, not the entire Hyperband bracket scheduler.
3. Simple causal linear extrapolation of the last two visible nodes to epoch50
   (last value at the first node), clipped only to the known metric range [0,100].
   Pay one metadata-selected anchor to epoch50 before pruning; prune only when prediction
   exceeds the best actually completed loss plus 1pp. No theoretical risk claim.
4. The original SureStop KillRule, default last-value predictor, alpha=.1, fixed
   good_threshold=20 loss percentage points, no learned hold-until-resolution.
   First32 metadata/random-order configurations on each demo task are fully paid calibration
   and remain eligible candidates. Its event is good AND stopped, not task near-optimal loss.
   Import only the inspected core source, not Optuna or the LoRA reproduction experiment.
5. A standard task-maximum residual calibration check with alpha=.1:
   max over all preselected configurations and nonterminal checkpoints of
   (linear predicted terminal loss - actual terminal loss), one score per calibration task.
   n_cal_tasks=3; if ceil((n+1)*.9)>n, output infinity and do not prune.
   This is a basic calibration baseline, not a new algorithm.
   Anchor-based pruning uses lower loss bound > completed incumbent loss +1pp.
   Do not assert task-risk control without sufficient exchangeable task calibration.
Replay ordering/ties are deterministic from SHA256 salt LCStop20261029; no extra RNG draws. Training seeds come from recorded data.

## Accounting and limits
Each strategy is replayed with a fresh restricted-prefix interface.
Separate recorded calibration training cost, ordinary prefix training cost, survivor
completion cost, calibration-computation CPU time, and policy/predictor CPU time.
Count calibration training once even if it is also a completed candidate.
For task-calibration baselines, show one-time auxiliary task cost separately and the
unamortized cold-start total; no assumed free calibration.
No GPU, foundation-model training, large scans, or formal tests.
Hard experiment CPU budget=14400 seconds, measured separately from dependency setup,
download, parsing and rendering. Log failures, do not enlarge the budget automatically.
Figure rule fixed before results: show the first failing demonstration task in task selection order, with method priority SH, linear, SureStop. If no failure exists, show a clearly labelled synthetic late-bloomer example. No policy tuning follows this display choice.
