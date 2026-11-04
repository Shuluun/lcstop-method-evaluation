from pathlib import Path
import json,csv
R=Path(__file__).resolve().parents[1]
(R/'tools').mkdir(exist_ok=True)
(R/'docs').mkdir(exist_ok=True)
(R/'requirements-replay.txt').write_text('numpy==2.3.5\nscipy==1.18.1\nmatplotlib==3.11.2\nijson==3.6.0\n',encoding='utf-8')
readme="""# LCStop: learning-curve stopping method evaluation

学习曲线前缀早停的可运行复现与方法评估。问题是：能否节省记录训练成本，同时保留固定候选池中的至少一个近优配置？

**状态：已完成开发演示与限定归因补充；停止当前新算法主张，未进入正式测试。**
这是私人研究归档，不声称新算法、已发表论文、正式外部验证或普遍优越性。所有结果均来自已有记录；本次发布没有重跑策略、训练或评价。

## 先读什么

1. [研究笔记](research_note.md)：问题、近邻文献、六任务开发小试、单位纠错和停止决定。
2. [最后的归因补充](analysis_addendum_v1/addendum.md)：32个已完成候选与同成本随机训练对照。
3. [固定规则](pilot_rules.md)、[原运行说明](README_research_original.md)。
4. [主结果](results/pilot_results.json)、[逐任务表](results/per_task.csv)、[归因表](analysis_addendum_v1/attribution.csv)、[随机比较逐次结果](analysis_addendum_v1/random_budget_comparison.csv)。
5. [复现说明](docs/REPRODUCIBILITY.md)、[数据与许可](docs/DATA_AND_SOURCES.md)、[发布修改与排除记录](publication/RELEASE_NOTES.md)。

![风险与成本](figures/risk_cost.png)

## 固定数据与对象

LCBench官方三种子归档v1。六个任务由元数据加固定SHA256规则选出，未按后段表现替换。
volkert、higgs、mfeat-factors是开发校准诊断任务；**car、christine、kr-vs-kp**是三个主要开发演示任务。
每任务128配置，使用原50轮计划实验中的三个记录训练种子；三个种子是同一配置的重复记录，不是三个独立任务。
仓库缓存只保留上述六任务、五节点的验证指标、成本和配置元数据，不含测试指标。没有正式测试池。

- 误差：100 × (1 − validation balanced accuracy fraction)，单位**百分点（pp）**，越低越好。
- 配置表现：三个记录种子的误差平均；配置成本：三个种子的累计elapsed seconds相加。
- 共同终点：epoch50；观察节点：1 / 5 / 15 / 30 / 50。
- 1pp近优：相对同任务预定128配置池的最低终点误差，差≤1pp。
- 任务丢失事件：没有近优候选完成共同终点。完成候选中按终点验证误差选择。
- SureStop α=.1、绝对good阈值τ=20pp；该单配置good事件不同于任务内1pp近优。
- 成本包含原记录的评价/记录开销，**不是本机实测训练加速**，也不是纯训练CPU时间。

## 主要开发结果

来源：[已有有效汇总](results/pilot_results.json)和[逐任务CSV](results/per_task.csv)。
成本节省先按各任务全训练成本归一，再对三个演示任务等权。

| 策略 | 记录成本节省 | 全部近优丢失 | 平均最终验证遗憾pp |
|---|---:|---:|---:|
| 全部训练 | 0.00% | 0/3 | 0.00000 |
| 固定节点Successive Halving（SH） | 86.76% | 0/3 | 0.00000 |
| 简单前缀线性外推 | 98.07% | 3/3 | 1.92724 |
| 原SureStop核心 | 60.90% | 0/3 | 0.08830 |
| 任务最大分数∞回退 | 0.00% | 0/3 | 0.00000 |

SH是固定节点适配，不是完整Hyperband。三个任务不足以支持非平凡90%任务级校准。
∞回退与全训练在线动作相同；简单前缀节省伴随全部任务失败，不能称风险控制成功。
原SureStop控制的单配置事件不能自动替代任务事件。

### 最后的归因结论

三个任务的初始32个完整付费校准候选**均已保留至少一个1pp近优**，足以解释SureStop原0/3任务丢失结果。
没有从原方法删除这32个候选。

| 任务 | 后续96个新增遗憾改善pp | 后续新增记录成本秒 |
|---|---:|---:|
| car | 0.000000 | 541.436 |
| christine | 0.000000 | 705.792 |
| kr-vs-kp | 0.371357 | 9987.732 |

在同一128配置池、每任务200个固定随机顺序下，同成本随机完整训练保留近优的比例为：

| 预算取自 | car | christine | kr-vs-kp |
|---|---:|---:|---:|
| SH实际成本 | 10.0% | 72.0% | 58.0% |
| SureStop实际成本 | 25.0% | 95.5% | 100.0% |

原SH在三个固定池内均达到零验证遗憾，呈现相对同成本随机完整训练的选择优势。
SureStop后续96个只在kr-vs-kp改善最终选择遗憾。
这些是事后预算匹配和贡献分解，**不是纯前缀信息的因果效应或总体风险保证**。
随机重复不是新增独立任务；实际预算包含校准成本，随机策略不能预知成本跳过昂贵候选。

![归因比较](analysis_addendum_v1/comparison.png)

## 安装与复现

建议Python3.12；历史精确环境见[environment.json](sources/environment.json)。
本次未安装依赖或验证全新环境安装；以下命令供取得仓库后执行。
新建自己的环境，不使用或修改原研究环境。

~~~powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements-replay.txt
# A：复制到独立运行目录后，从已用缓存重放主流程
.\\.venv\\Scripts\\python.exe -B tools/reproduce.py pilot --name pilot_replay_01
# A：重放同一固定排列的归因分析，比较历史数据文件；不增加样本
.\\.venv\\Scripts\\python.exe -B tools/reproduce.py addendum --name attribution_replay_01
~~~

[详细说明](docs/REPRODUCIBILITY.md)区分历史已成功命令、此次仅静态检查的封装入口，以及B层原始归档重建。
输出在被忽略的reproductions/中，拒绝覆盖已有运行目录。
没有自动下载、训练、CI或收费存储工作流。

## 数据、第三方与许可

- [官方LCBench](https://github.com/automl/LCBench)，Zimmer, Lucas (2020), data_2k_3seed, [DOI v1](https://doi.org/10.6084/m9.figshare.12408707.v1)。
- 六任务小缓存是上述Apache-2.0数据的选择、单位变换派生物；保留其[许可证全文](licenses/LCBench-Apache-2.0.txt)与[变换记录](sources/unit_correction.json)。
- 仅随附运行所需的[SureStop core.py](sources/repos/ACNoonan/surestop/src/surestop/core.py)，原样字节固定，MIT版权及[许可](sources/repos/ACNoonan/surestop/LICENSE)保留。其他近邻只保留已读范围、来源URL和历史字节指纹，不附整个外部仓库或论文。
- 本人代码未选择统一开源许可；本仓库保持私有，未添加覆盖全仓库的MIT等许可。第三方许可证各自有效。

## 分工与结论边界

高书伦提出研究目标、限制与验收要求，并授权执行开发演示和归因补充；这些职责可由研究任务记录确认。
代码实现、文献/代码整理、报告及发布整理有AI执行与辅助；不声称全部代码由本人手写。
现有工程文件没有逐文件的人工作业登记，不能确认的人工编码比例或逐行贡献不作推断，也未据此声明审核代理是独立实验验证。
SureStop实现、LCBench数据及近邻理论属于各原作者。

研究展示了因果可见性接口、强对照、失败保留、单位纠错和成本归因的复现实践。
近优丢失在既定流程下等价于已有ε简单遗憾；普通LTT/最大分数已有直接风险框架，当前不支持新算法主张。
不把结果与任何旧生物学工程的有效性联系起来。
"""
(R/'README.md').write_text(readme,encoding='utf-8')
data="""# Data and third-party provenance

## Included inputs

The v2 cache contains exactly the six already-used tasks, 128 configurations/task, three recorded seeds and five nodes.
Fields are validation accuracy/loss, recorded elapsed time, configuration metadata and fixed selection metadata; no test metrics.
Both the invalid-unit v1 cache and corrected v2 cache are included so correction history can be inspected without reopening the archive.
No new extraction or sampling was performed for publication.

Official metadata saved in [figshare_12408707.json](../sources/figshare_12408707.json) identifies the dataset as Apache 2.0.
The copied [Apache license](../licenses/LCBench-Apache-2.0.txt) came from the already-acquired official LCBench repository snapshot.
This subset is modified by selection/field restriction and unit conversion, not an unmodified full archive.
Attribution: Zimmer, Lucas (2020). data_2k_3seed. figshare. https://doi.org/10.6084/m9.figshare.12408707.v1 .
No dataset NOTICE was present in the acquired reduced repository snapshot; the large archive was not opened during publication.

## Official full input, not uploaded

- DOI: https://doi.org/10.6084/m9.figshare.12408707.v1
- URL: https://ndownloader.figshare.com/files/22859435
- Official name: bench_full.zip; version1; bytes: 1813896086.
- SHA256: e490969c4f068fc7d96c880f9d3051bc2ae285feae995f6610d6a92092bc1198
- Put at data/bench_full.zip (ignored by Git), or provide its path to the raw preparation wrapper.
- ZIP member: bench_full.json. Do not manually concatenate planned horizons or use test metrics.
- Existing download evidence: [full_archive_download.json](../sources/full_archive_download.json).
- Generators: [download_full.py](../download_full.py), [extract_selected.py](../extract_selected.py), [json_adapter.py](../json_adapter.py).
- The original download/metadata pass succeeded historically. Corrected extractor source exists, but a complete corrected raw-to-results rebuild was not rerun; publication does not claim otherwise.

## SureStop runtime snapshot

Only core.py and its existing LICENSE/README/tree metadata are bundled, not the full repository.
Copyright (c) 2026 Adam Noonan; MIT license. core.py is unmodified:
SHA256 6b3628e2dbf728daf3fb96b18c66d798f047e1dae779707a9bc6cc80dda7cf9a.
Saved Git blob: 9dc0449d8d274ce89d318820850185a7a4b66569.
Saved Git tree: cd05b98240449dbdf39c07b6176460d6dfebf0a2 (a tree, not a commit).
Original URL: https://github.com/ACNoonan/surestop .
The runtime imports this local snapshot explicitly, so it does not depend on mutable HEAD.

## Other neighbors

[read_scope.json](../sources/read_scope.json) and [source_snapshots.json](../sources/source_snapshots.json) retain the historical reading depth, public URLs and byte hashes.
Most paths in the historical snapshot manifest refer to deliberately omitted external sources. The manifest records history; it is not an assertion that all those files are bundled.
[Snapshot inclusion map](../publication/THIRD_PARTY_SNAPSHOT_MAP.csv) states the status of each entry.
Papers, complete downloaded repositories, ifBO weights and unrelated local caches are not included.
No new paper, repository or model weight was downloaded for publication.
"""
(R/'docs/DATA_AND_SOURCES.md').write_text(data,encoding='utf-8')
repro="""# Reproduction levels and actual verification status

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
"""
(R/'docs/REPRODUCIBILITY.md').write_text(repro,encoding='utf-8')
notes="""# Private publication copy: changes and exclusions

Source: LCStop_20261029_v1. The research source is read-only.
No pre-existing final_delivery_v1 directory was found; none was invented.
A new Git history is initialized only in this independent publication copy.

## Exact copy and modifications

[source_manifest.csv](source_manifest.csv) lists each explicitly whitelisted source/destination, original/published hash and change.
Scientific Python scripts, caches, rules, results, fixed permutations and historical check records were copied byte-for-byte.
Only machine-local location examples in three report copies were replaced with descriptive placeholders.
README.md is new; the old README is preserved at README_research_original.md.
.gitignore was written before staging; .gitattributes disables newline conversion so pinned bytes remain stable across Git on Windows.
The new tools/reproduce.py isolates future runs. It does not refactor scientific logic.
requirements-replay.txt narrows installation to runtime packages at their recorded versions; requirements.txt remains unchanged.

## Excluded

No original .git history, .venv, paper PDFs, raw large ZIP, caches/.cache, credentials, full external repositories or old unrelated research projects.
Historical one-off sources/execution_helpers were not required by the runtime and are omitted; operational generation scripts are at the root.
Original AGENTS is not inherited by the publication copy: its historical no-upload rule was explicitly superseded for this private publication only.
No new repository-wide software license is selected. Dataset and SureStop licenses retain their own scope.
No CI, automatic training/download, Git LFS billing or collaborator invitation is configured.

The report references old boundary decisions only as LCStop history; no files from those older projects were read/copied.
The source_protection.json and publication_check.json checks cover the consulted whitelist plus source AGENTS, not the environment or large excluded raw archive.
Historical source hashes are retained, not rewritten to erase failures.
"""
(R/'publication/RELEASE_NOTES.md').write_text(notes,encoding='utf-8')
snaps=json.loads((R/'sources/source_snapshots.json').read_text())
with (R/'publication/THIRD_PARTY_SNAPSHOT_MAP.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['historical_path','status','public_source','historical_sha256']);w.writeheader()
    for x in snaps['files']:
        status='included exact bytes' if (R/x['path']).exists() else 'omitted; historical URL/hash only'
        if x['path']=='sources/repos/automl/LCBench/LICENSE':status='license included at licenses/LCBench-Apache-2.0.txt'
        w.writerow(dict(historical_path=x['path'],status=status,public_source=x['public_source'],historical_sha256=x['sha256']))
print('Publication documentation written; no research executed.')