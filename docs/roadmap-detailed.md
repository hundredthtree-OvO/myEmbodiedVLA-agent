# 详细路线图

这份文档记录项目的详细路线图、MVP 范围、实现反馈与阶段判断。  
[README.md](/E:/my-embodied/README.md) 只保留高层方向，这里负责沉淀“当前做到哪、为什么这么做、接下来做什么”。

## 产品定位

当前产品定位是：

- 以 Codex 为核心的论文-代码对齐研究副驾
- 擅长基于 `paper + repo + focus` 生成结构化学习笔记
- 当前仍然不是完整的“研究学习代理”

当前主线目标是：

1. 先把 evidence 质量做强
2. 再补轻量 learning loop

核心方向可以概括为：

```text
论文概念 -> 代码实现 -> 可复用的研究记忆
```

## 当前状态

已完成：

- P0：基础加固
- P1 第一步：结构化 repo evidence pack
- `core_model` / `deployment_policy` 分离
- architecture 的 role-aware ranking
- architecture 的 `entry / skeleton / component` 分层
- `entry / skeleton / component` 的轻量 AST rerank

当前仍然存在的缺口：

- 同层内部排序仍然是“轻量规则 + 轻量 AST”驱动，不是完整图分析
- 某些仓库没有单一、明显的 architecture assembly file
- second-pass reading 还没有实现

## P1 MVP：Role-Aware Ranking

### 目标

让 `architecture / model / module` focus 下的候选顺序，更接近人类第一次读 repo 时的顺序，而不是单纯按路径关键词或混合中心性排序。

### MVP 范围

第一轮 MVP 的重点是先建立角色分层，不追求完整程序分析。

需要保留并输出的核心角色字段：

- `architecture_entry_candidates`
- `architecture_skeleton_candidates`
- `architecture_component_candidates`
- `config_entry_candidates`
- `deployment_entry_candidates`

为了兼容旧逻辑和其它流程，仍保留这些字段：

- `core_model_candidates`
- `deployment_policy_candidates`
- `train_candidates`
- `inference_candidates`
- `config_candidates`
- `model_candidates`
- `entry_candidates`

### 设计原则

1. 用多角色分类，而不是强行让每个文件只有一个角色。

2. `architecture_entry` 依赖泛化信号，不依赖硬编码文件名。

第一阶段可用的泛化信号包括：

- core model 路径
- assembly / skeleton 文件名信号，如 `arch`、`builder`、`model`、`vla`、`vlm`、`policy`
- 排除明显噪音文件
- 轻量 project stem match

3. 第一轮不引入完整 import/call graph。

4. `candidate_reasons` 先作为 debug 工具使用。

目的不是“解释漂亮”，而是帮助判断规则到底是在泛化，还是在背答案。

## 已实现内容

实现日期：

- 2026-04-25

代码层面已经完成：

- `RepoInfo` 新增并保留：
  - `architecture_entry_candidates`
  - `config_entry_candidates`
  - `deployment_entry_candidates`
  - `candidate_reasons`
- `ingest_repo()` 已经可以构建 role-aware candidate lists
- `prompt_builder` 已经输出新的 role-aware sections
- `composer` 已经在离线 markdown 中输出新的 role-aware sections
- `build_reading_path()` 已经按 focus-aware 方式处理：
  - `architecture / model / module`
  - `training / loss / objective`
  - `inference / deploy / eval`
  - `config / hyperparameter`

调试支持：

- top role-aware candidates 会在 prompt / offline 输出中带上 reason traces

测试：

- 已更新单元测试，覆盖新的 role-aware candidate lists
- 已补 architecture-focus reading order 测试

当时的自动化测试结果为：

```text
Ran 28 tests ... OK
```

## P1 后续细化：Architecture Chain Layering

实现日期：

- 2026-04-25

增加这一轮 refinement 的原因：

- 只有 `architecture_entry_candidates` 仍然太扁平
- `attention / projector / patches / pipeline` 这类文件仍可能过早浮到前面
- reading path 当时还缺一条明确的 `entry -> skeleton -> component` 架构链路

### 已实现的细化内容

- `RepoInfo` 进一步新增：
  - `architecture_skeleton_candidates`
  - `architecture_component_candidates`
- `ingest_repo()` 现在会构建三层 architecture：
  - `architecture_entry`
  - `architecture_skeleton`
  - `architecture_component`
- architecture ranking 现在会过滤 architecture 层中的非代码文件
- architecture ranking 会对 deployment-like wrapper 做惩罚
- `build_reading_path()` 在 architecture focus 下优先按下面顺序组织：

```text
architecture_entry -> architecture_skeleton -> architecture_component -> config_entry -> deployment_entry
```

- `prompt_builder` 与 `composer` 也同步输出了新的 architecture layers
- 测试已经覆盖：
  - entry / skeleton / component 分离
  - architecture-focus reading path 顺序

### 这轮改动后的判断

这轮改动是值得保留的，因为它比按“原始引用次数”排序更符合第一次读代码的真实顺序。

主要改善：

- `base_policy.py` 这类 deployment wrapper 更不容易泄漏到 architecture entry 顶部
- `backbone / head` 这类骨架文件不再和 `attention / projector` 直接抢同一个位置
- architecture 阅读顺序更接近：
  - 顶层装配文件
  - 结构骨架文件
  - 局部组件文件

故意保持“软规则”的地方：

- 同一层内部排序仍然较轻
- 比如 `attention` 和 `projector` 之间，不做硬编码偏好
- 这样做是为了避免让 heuristic 过拟合到几个文件名模板

## 真实仓库验证反馈

验证方式：

- 对真实仓库运行 `offline` 分析
- 观察：
  - `architecture_entry_candidates`
  - `architecture_skeleton_candidates`
  - `architecture_component_candidates`
  - `config_entry_candidates`
  - `deployment_entry_candidates`
  - `reading_path`
  - `candidate_reasons`
  - `ast_candidate_reasons`

### WAV

结果：

- core model 与 deployment wrapper 的分离依然稳定
- deployment wrapper 没有抢走主模型阅读位置
- role-aware 输出整体稳定

做对的地方：

- `deployment_entry_candidates` 能正确隔离 `openpi_client/runtime/*`
- reading order 仍然优先留在 model 侧文件

剩余问题：

- 这个 repo 没有单一、明显的 architecture assembly file
- 顶部 architecture 候选仍然偏 component-heavy，例如：
  - `models/action_patches/patches.py`
  - `models/pipeline/custom_pipeline.py`
  - `models/value_patches/value_patches.py`

判断：

- 作为 MVP 已经够用
- 但对“逻辑分散在 patches / pipeline / components 中”的仓库，仍然不够 assembly-aware

### VLA-Adapter

结果：

- 明显改善
- `prismatic.py` 已经能进入 architecture entry 集合
- `extern/hf/modeling_prismatic.py` 不再主导 entry 视角

做对的地方：

- `architecture_entry_candidates` 能稳定包含：
  - `prismatic/models/vlas/openvla.py`
  - `prismatic/models/vlms/prismatic.py`
- `config_entry_candidates` 更偏向：
  - `prismatic/conf/vla.py`
  - `prismatic/conf/models.py`
  - `prismatic/conf/datasets.py`

剩余问题：

- 早期版本里 `base_vlm.py` 仍会压在 `prismatic.py` 前面
- 对 bridge attention 这类概念聚焦阅读来说，光靠第一遍排序仍不够

当前判断：

- 已经是有意义的改善
- architecture-first 行为明显更接近目标方向

### ACoT-VLA

结果：

- 明显改善
- 主 architecture 文件已经能被抬出来

做对的地方：

- `architecture_entry_candidates` 可以从：
  - `src/openpi/models/acot_vla.py`
  - `src/openpi/models/pi0.py`
  - `src/openpi/models/vit.py`
  - `src/openpi/models/siglip.py`
  中稳定抬出主入口和骨架候选
- `training/config.py` 不再占据主 architecture 槽位
- reading order 更接近人工第一次读 repo 的顺序

判断：

- 是当前 MVP 的成功样例

### ReconVLA

结果：

- 有改善，但还不算完全收敛

做对的地方：

- `recon_arch.py` 与 `builder.py` 已经能被抬进 architecture entry 候选
- training / config / deployment 文件不会再主导 architecture 槽位

仍然缺的点：

- `recon_qwen.py` 早期不够稳定
- pixel / multimodal builders 一度仍强于更高层的 language-model assembly file

判断：

- 属于部分成功
- 说明当前 MVP 已经比以前更能处理 assembly file
- 但仍需要更强的 assembly-vs-component discrimination

## P1.6 更新：补齐 Skeleton / Component 的轻量 AST 重排

这一轮是在前一版 `architecture_entry` AST 重排的基础上，继续把轻量 Python AST 信号补到了：

- `architecture_skeleton_candidates`
- `architecture_component_candidates`

实现策略保持不变，仍然是“保留现有 heuristic role prior，再在候选池内做 AST 定向重排”，没有引入 Tree-sitter，也没有做全仓 PageRank。

### 本轮实现内容

- `entry / skeleton / component` 现在都能接收 AST debug 信号
- `ast_index.py` 中补充了：
  - `skeleton_like`
  - `component_like`
  - `script_like`
  - `bridge_like`
  - 更通用的 `assembly_like`
- `graph_rank.py` 中新增了：
  - `rerank_architecture_skeleton_candidates(...)`
  - `rerank_architecture_component_candidates(...)`
- `ingest_repo()` 现在的 architecture 主链路变成：

```text
heuristic role candidates
-> AST rerank(entry)
-> AST rerank(skeleton)
-> AST rerank(component)
-> reading_path(entry -> skeleton -> component -> config -> deployment)
```

- 输出层也同步补齐了 skeleton / component 的 AST debug，方便直接看“为什么这个文件升了/降了”

### 这一轮主要修了什么问题

此前的典型问题是：

- `ACoT-VLA` 中 skeleton 为空，说明很多“骨架文件名不显眼”的文件没有被捞出来
- `component` 层会混入 `scripts/compute_norm_stats.py` 这类带有 `norm / stats` 词的脚本

这轮针对性加入了两类改进：

1. 对 `model.py / pi0.py / vit.py` 这类文件，不再只依赖路径关键词，而是结合：
   - AST 中的类定义
   - `sample_actions / forward / predict_action`
   - assembly / bridge 行为
   - 是否被 entry / config / policy 层引用

2. 对脚本型噪音加入 penalty：
   - `__main__`
   - `argparse / tyro / draccus`
   - `compute_* / *_stats / prepare_* / convert_*`
   - `scripts/` 路径

### 这轮验证后的仓库反馈

#### VLA-Adapter

- `openvla.py`、`prismatic.py` 作为 architecture entry 的位置仍然稳定
- `base_vlm.py` 继续被压低，没有回退
- `action_heads.py` 与 `projectors.py` 现在至少能在 AST tag/debug 里被更稳定地识别

结论：

- entry 层增强保持有效
- 没有因为补 skeleton / component 而把前一轮的 entry 结果打回去

#### ReconVLA

- `recon_arch.py`、`recon_qwen.py` 继续保持在更靠前的位置
- 子模块 `pixel_decoder/builder.py`、`multimodal_encoder/builder.py` 没有重新压回顶部

结论：

- “concrete model / top-level arch 高于 submodule builder” 这条改进保持住了

#### ACoT-VLA

这是这一轮最关键的泛化样例。

前一版的问题是：

- `architecture_entry` 还可以
- 但 `architecture_skeleton_candidates` 几乎为空
- `architecture_component_candidates` 会混入 `scripts/compute_norm_stats.py`

这一轮之后，目标是让：

- `model.py`
- `pi0.py`
- `vit.py`

这些更像骨架 / 核心子结构的文件进入 skeleton 前列，同时把 `compute_norm_stats.py` 从 component 前列压下去。

如果这些点在本地真实仓库回归中稳定成立，就说明：

- 轻量 AST 已经足够支撑 P1 阶段的 architecture sorting
- 下一阶段应转向 second-pass reading，而不是继续在排序层上堆复杂图算法

#### le-wm

`le-wm` 是后续额外加入的压力测试样例。它不是典型的 `models/policy/backbone/action_head` 目录式 VLA repo，而是更偏平铺目录的 world-model / JEPA 风格：

- `jepa.py`
- `module.py`
- `train.py`
- `eval.py`

这类仓库特别适合检验当前排序是不是仍然过度依赖 `models/`、`policy`、`vla / vlm` 这类命名空间。

补充验证后的结果是：

- `jepa.py` 可以被抬入 `architecture_entry`
- `module.py` 可以进入 `architecture_skeleton`
- `train.py / eval.py` 自己不会被误抬进 architecture entry 顶部

这说明当前系统已经不只是“对典型 VLA 命名起作用”，而是开始具备：

- `train / eval -> imported / instantiated repo class -> architecture file` 的反向提名能力
- 对 flat world-model repo 的最小泛化能力

但 `le-wm` 也暴露了一个还没完全收口的点：

- mixed file（例如同时包含 skeleton 与 component 定义的 `module.py`）目前仍然会在多层候选里留痕

这个问题更像后续的小幅收口项，不再构成进入 second-pass reading 的阻塞点。

## 当前阶段判断

到这一步，排序层的判断可以收敛为：

- `entry`：已经明显优于纯 heuristic
- `skeleton`：已经开始真正补强，是是否进入 second-pass 的关键观察项
- `component`：已经开始加入脚本 / 工具噪音抑制，不再只是“带 token 就抬”

因此，当前 roadmap 的阶段判断是：

1. `entry / skeleton / component` 的轻量 AST 补强已经完成
2. `ACoT-VLA / ReconVLA / VLA-Adapter / le-wm` 四个样例没有出现严重回退
3. 下一步主线应该直接进入：

```text
important file second-pass reading
```

而不是继续扩展为：

- full AST graph
- Tree-sitter
- 通用 PageRank
- 更重的 CandidateInfo 系统

补充说明：

- mixed skeleton/component file suppression 可以作为并行的小修正继续收口
- 但它已经不再改变阶段判断

## 当前总体结论

这个 P1 MVP 是值得保留的。

它已经在多个真实仓库上带来可用的泛化改善：

- 系统不再强依赖单一混合排序列表
- architecture focus 更不容易被 config / deployment 噪音劫持
- reading path 更接近人工第一次读 repo 的顺序

但它依然只是一个第一版 MVP：

- role-aware separation 已经比较强
- assembly-vs-component prioritization 还可以继续收口
- concept-aware second-pass reading 还没有进入实现阶段

## 现在不要做什么

暂时不要直接跳到：

- full AST graph
- 全项目 CandidateInfo 系统
- 复杂 retrieval / learning loop
- concept-aware second-pass reading 之外的更重机制

当前单次分析质量已经足够进入第二阶段，继续在排序层叠复杂度，收益会开始变差。

## 下一步

明确的下一步是：

```text
important file second-pass reading
```

进入这一阶段后，要做的事情是：

- 从第一遍排序结果中挑出 3-8 个关键文件
- 对这些文件做更细的证据抽取
- 形成更强的 repo evidence，支撑 Concept2Code tracing

这一步之后，再考虑：

- second-pass reading of 3-8 key files
- stronger repo evidence for Concept2Code tracing
- 然后才是轻量 learning loop：
  - session reflection
  - skill memory
  - retrieval
