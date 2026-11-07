from pathlib import Path
import json,csv
R=Path(__file__).resolve().parents[1];O=R/'reproduction_review_v1'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
c=load(O/'comparison.json');pilot=load(O/'pilot_execution.json');att=load(O/'addendum_execution.json');setup=load(O/'dependency_setup.json')
# Normalize only newly generated shell logs/lock text for portable publication.
normalized=[]
for p in O.rglob('*'):
    if p.is_file() and p.suffix in ['.txt','.log']:
        b=p.read_bytes()
        if b.startswith((b'\xff\xfe',b'\xfe\xff')):
            p.write_text(b.decode('utf-16'),encoding='utf-8');normalized.append(p.relative_to(O).as_posix())
result=load(O/'replayed_pilot/pilot_results.json')
tab=[]
for x in result['summary']:
    tab.append(f"| {x['method']} | {(1-x['mean_relative_recorded_cost'])*100:.2f}% | {x['all_near_optimal_lost_count']}/3 | {x['mean_final_validation_regret_pp']:.5f} |")
cpu=c['main_replay_cpu_seconds']+c['synthetic_cpu_seconds']+c['attribution_cpu_seconds']
note=f"""# LCStop干净环境复现：结果与范围

高书伦｜2026年11月6日

**完成：已发布版本的小缓存主流程和归因补充，在独立环境中复现成功。**
**未完成：从1.81GB官方原始归档完整重建、跨平台复现、正式外部验证。**
本轮不增加数据任务、模型、候选池、方法、随机重复或调参；原新算法主张仍停止。

## 从什么版本开始

从私有仓库新克隆提交 {load(O/'plan.json')['source_commit']}，未复制原虚拟环境。
Python3.12.14，新venv不继承system-site-packages且禁用用户site；numpy2.3.5、scipy1.18.1、
matplotlib3.11.2、ijson3.6.0从官方PyPI安装成功。
依赖安装壁钟{setup['wall_seconds']:.3f}秒，和科学回放成本分开。
解析后的依赖锁见[requirements-resolved.txt](requirements-resolved.txt)，环境见[environment.json](environment.json)。

这里的“干净环境”是同一Windows主机上的新包环境，复用现有Python解释器；
不是全新操作系统、容器、另一台计算机或跨平台独立验证。

## 实际运行与核对

| 部分 | 实际执行 | 核对结果 |
|---|---|---|
| 主流程 | check_causality.py、replay.py、plot_results.py、verify_delivery.py | 6任务×5策略共30次回放，科学字段、轨迹、付款与位置精确相同 |
| 合成实现检查 | 重新执行6项检查 | 全部PASS；包含未来标签不影响此前动作、付费接口、原SureStop规则与反例 |
| 归因补充 | 同一seed20261030、同一200排列/任务的确定性重放 | orders.json、attribution.csv、random_budget_comparison.csv、random_summary.json逐字节相同 |
| 图形 | 本轮重新生成并目视检查风险—成本、失败案例、归因比较图 | 可读；图像字节不作为统计或数值一致性条件 |

比较规则在运行前写入[plan.json](plan.json)。[comparison.json](comparison.json)记录{c['recursive_nodes_compared']}个递归节点比较，精确差异0；
明确剔除预先列出的计时字段，没有通过提高数值容差获得一致。
[comparison_rows.csv](comparison_rows.csv)逐行列出30次回放。
主流程壁钟{pilot['wall_seconds']:.3f}秒；归因封装壁钟{att['wall_seconds']:.3f}秒，两者部分并行，不能相加当整体历时。
主回放记账CPU {c['main_replay_cpu_seconds']:.6f}秒、合成检查{c['synthetic_cpu_seconds']:.6f}秒、
归因{c['attribution_cpu_seconds']:.6f}秒，三项合计{cpu:.6f}秒；不把该和当作安装、制图、复制与所有工具开销的精确总量。
均未接近原主流程4 CPU小时/归因600 CPU秒限额。未运行GPU或新模型训练。

## 再现的开发结果

三个演示任务是car、christine、kr-vs-kp，另三个仅用于开发校准诊断。
每任务128个原候选，三个记录种子误差平均、成本求和；
共同终点50轮，节点1/5/15/30/50，误差是100×(1−验证balanced accuracy)，近优阈值1pp。
成本仍为原记录elapsed seconds，不是本机训练加速。

| 方法 | 任务等权记录成本节省 | 全部近优丢失 | 平均验证遗憾pp |
|---|---:|---:|---:|
{chr(10).join(tab)}

这些是已暴露开发资料的确定性复现，不是新样本上的方法评价。
没有把三个任务、配置或种子当成可互换的独立统计单位。

归因结论不变：初始32个完整训练候选在三个任务均已含1pp近优；
后续96个仅在kr-vs-kp改善最终遗憾0.371357pp，新增记录成本9987.732秒。
SH在三个固定池中相对同成本随机完整训练呈现选择优势；
这不分离纯前缀信息的因果效应，也不提供总体风险保证。
原首次量纲错误与无效结果原样保留，本轮没有用其成绩作比较。

## 证据如何保存

- [主流程执行记录](pilot_execution.json)、[完整日志](pilot.log)、[新生成主结果](replayed_pilot/pilot_results.json)。
- [归因执行记录](addendum_execution.json)、[日志](addendum.log)、[确定性核对](replayed_addendum/replay_check.json)。
- 四个相同归因数据文件已经在原analysis_addendum_v1版本化，不再上传第三份相同排列/CSV；
  新run_manifest及图保留在replayed_addendum。
- 根目录历史代码、缓存、结果与科学规则在比较时全部未变；之后仅更新首页/复现说明并新增本目录。
- 本轮没有打开官方大归档，没有访问其他研究工程。
- 未发生科学复现失败，科学失败台账[failures.jsonl](failures.jsonl)为空；
  工具/发布检查若有问题另行记录，不能冒充科学验证。

## 仍然成立的限制

原始归档纠正后的提取源码仍未从头执行，v2缓存仍具有历史单位纠正恢复的来源限制。
只有同主机、同Python及核心库版本的新环境证据；新环境安装成功不证明其他平台可用。
本轮没有新增近邻文献或新算法比较，原STOP保持。
GitHub维持PRIVATE，由本人检查后另行决定是否公开；本次不更改可见性。
"""
(O/'README.md').write_text(note,encoding='utf-8')
(O/'failures.jsonl').write_text('',encoding='utf-8')
(O/'publication_adjustments.json').write_text(json.dumps({'new_shell_text_normalized_utf16_to_utf8':normalized,'scientific_code_changed':False,'historical_results_changed':False,'original_environment_changed':False},indent=2),encoding='utf-8')
case="""# 校准候选、前缀筛选与成本：LCStop方法评估案例

## 研究问题

在一个预先固定的超参数配置池里，训练到共同终点后，哪些早停策略能节省成本而仍保留至少一个近优配置？
这里的“近优”是相对池内验证指标的操作定义，不是测试集泛化最优。
这项工作把四个容易混淆的对象分开：单配置误停、任务级近优全部丢失、最终验证遗憾及完整成本。

## 实际做了什么

使用LCBench既有记录，以元数据和固定规则选定六个开发任务、每任务128配置、三个训练种子和五个观察节点。
实现了受限前缀接口、每策略独立回放、付款账本和离线终点评价器。
实际比较全部训练、固定节点SH、简单线性外推、原SureStop及普通任务最大分数校准。
后者因为校准任务太少而回退至完整训练，没有通过修改分位数制造非平凡保证。
文献/源码核查与实际运行的方法始终分开；没有把所有近邻都说成完成复现。

## 主要发现

简单前缀外推节省约98.07%记录成本，但三个演示任务都丢失全部1pp近优；
固定节点SH节省约86.76%，三个任务均达到零池内验证遗憾。
原SureStop节省约60.90%，平均验证遗憾0.08830pp且任务丢失0/3；
不过32个已完成校准候选本身已经在三个任务中全部保住近优。
后续96个探索只在kr-vs-kp把遗憾再降低0.371357pp。

因此，方法的0/3任务失败不能直接归因于前缀预测。
把校准数据看成免费训练资料，或只在后续配置里统计候选，会改变原方法的成本和决策对象。
同成本随机完整训练提供了另一种解释检验：按固定顺序请求候选，预算不足时耗尽余额，
不读取终点且不跳过昂贵候选。结果支持SH在这些固定池内的选择优势，
但没有辨识纯前缀信息的因果贡献，也没有新增独立任务。

## 方法与工程贡献的范围

可以支持的是一个可运行的方法评价案例：前缀因果可见性、校准样本与候选身份区分、
冷启动成本记账、强简单基线、失败保留和确定性复现。
2026年11月6日的新克隆、新包环境验证了30次主回放科学输出一致，
并验证四个归因数据文件逐字节相同，见[复现报告](README.md)。

它不能支持新算法贡献、正式风险保证、跨平台/跨实验室外部验证或普遍胜出。
新算法主张仍停止。现有工作适合导师讨论及可复现技术作品；
是否有独立论文增量需要额外依据，本案例不据此自动开展新题或扩大实验。
"""
(O/'method_evaluation_note.md').write_text(case,encoding='utf-8')
# New review helpers use the clone root when inspected or reused; no scientific source is changed.
p=O/'prepare_review.py';text=p.read_text(encoding='utf-8');text=text.replace("R=Path(r'D:\\LCStop_Repro_20261106_v1')","R=Path(__file__).resolve().parents[1]");p.write_text(text,encoding='utf-8')
a=load(O/'publication_adjustments.json');a['prepare_helper_path_generalized_after_execution']=True;(O/'publication_adjustments.json').write_text(json.dumps(a,indent=2),encoding='utf-8')
# Add an explicitly dated status update; retain the publication-time history below it.
p=R/'README.md';text=p.read_text(encoding='utf-8');title,rest=text.split('\n',1)
banner="""

> **2026-11-06复现更新：** 从本私有仓库新克隆，在不继承系统包的新环境中安装固定依赖成功。
> 小缓存主流程30次回放的科学输出精确一致，归因四数据文件逐字节一致。
> [复现报告](reproduction_review_v1/README.md) · [方法评估案例](reproduction_review_v1/method_evaluation_note.md)。
> 官方大归档重建及正式外部验证仍未完成。仓库保持PRIVATE。
"""
p.write_text(title+banner+'\n'+rest,encoding='utf-8')
p=R/'docs/REPRODUCIBILITY.md';text=p.read_text(encoding='utf-8');title,rest=text.split('\n',1)
p.write_text(title+'\n\n## 2026-11-06 actual clean-environment replay\n\nA fresh private clone and a new venv without system-site-packages successfully executed both published small-cache wrapper commands. All 30 pilot scientific outputs matched exactly after the predeclared timing exclusions; four attribution data artifacts were byte-identical. See [review report](../reproduction_review_v1/README.md), [comparison](../reproduction_review_v1/comparison.json) and [resolved environment](../reproduction_review_v1/requirements-resolved.txt). Raw-archive reconstruction remains unrun. The original publication-time verification status below is retained as history.\n\n'+rest,encoding='utf-8')
print('Reproduction report and method-evaluation case written; scientific rules unchanged.')