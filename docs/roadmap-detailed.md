# 详细路线图

这份文档记录项目当前阶段、为什么这么做、已经验证了什么，以及接下来的执行主线。

## 产品定位

当前产品定位是：

- 以 Codex 为核心的论文-代码对齐研究副驾
- 擅长基于 `paper + repo + focus` 生成结构化学习笔记
- 当前仍然不是完整的“研究学习代理”，而是以证据组织和代码理解为中心的分析器

当前主线目标可以概括为：

```text
论文概念 -> 代码实现 -> 可复用的结构化研究证据
```

## 当前状态总览

已经完成：

- P0：基础加固
- P1：第一遍 repo evidence 构建与角色排序
- `entry / skeleton / component` 轻量 AST 重排
- P2 前置：两轮 second-pass reading 与结构化 `Concept2Code` 证据落盘

仍然没有做的重机制：

- full AST graph
- Tree-sitter 多语言解析
- 通用 PageRank / centrality
- 长期 memory / retrieval

当前阶段判断：

1. 排序层已经从“可用原型”进入“可持续复用”
2. 主线已经从“继续堆排序规则”切换到“second-pass 深读 + 结构化证据”
3. 下一步重点不是更重的排序算法，而是让 `Concept2Code tracing` 更稳、更可保存

---

## P0：基础加固

### 目标

先把工具跑通、错误信息收清楚、环境依赖去硬编码。

### 已完成内容

- 远程 repo clone 的失败提示与 fallback
- PDF 解析失败时的错误分层
- Codex auth 路径改为环境变量 / 配置可覆盖
- Zotero 默认路径改为通用默认值，并支持环境变量覆盖
- `pyproject.toml` 补上 `pypdf`，README 明确区分 Python 依赖与系统依赖

### 当前结论

这一步已经足够支撑开源使用和跨环境运行，不再是当前主线阻塞项。

---

## P1：第一遍 Evidence Core

### 目标

让仓库分析结果不再只是“命中几个关键词”，而是形成可用于阅读路径的第一遍 repo evidence。

### 两层结构

当前主链是：

```text
类型候选层 -> 角色构建层 -> AST 重排层 -> reading_path
```

#### 1. 类型候选层

回答：

```text
这些文件大概属于什么类型？
```

当前保留的类型字段：

- `train_candidates`
- `inference_candidates`
- `config_candidates`
- `model_candidates`
- `core_model_candidates`
- `deployment_policy_candidates`
- `data_candidates`
- `loss_candidates`
- `env_candidates`
- `docs_candidates`
- `utils_candidates`

#### 2. 角色构建层

回答：

```text
在 architecture 理解链路里，这些文件分别扮演什么角色？
```

当前保留的角色字段：

- `architecture_entry_candidates`
- `architecture_skeleton_candidates`
- `architecture_component_candidates`
- `config_entry_candidates`
- `deployment_entry_candidates`

### reading_path 当前逻辑

在 `architecture` focus 下，当前顺序为：

```text
architecture_entry
-> architecture_skeleton
-> architecture_component
-> config_entry
-> deployment_entry
```

这比早期的混排更接近人第一次读 repo 的顺序。

---

## P1.5 / P1.6：轻量 AST 重排

### 目标

不要再按“被引用次数”粗暴排序，而是让 architecture 相关文件更像真实架构链路：

```text
train / eval / config
-> policy / model / world-model entry
-> backbone / head / bridge / decoder
-> component
```

### 已完成内容

- 只对 Python 仓库建立轻量 AST 索引
- 保持文件级，不做全仓调用图
- 对 `entry / skeleton / component` 三层都接入 AST 定向重排
- 加入 `script_like`、`helper_like`、`abstract_base`、`submodule_builder` 等 penalty
- 加入 world-model / flat repo 的最小泛化支持

### 当前 AST 主要做什么

- 识别 concrete model / abstract base
- 识别 skeleton_like / component_like / script_like
- 识别 `forward / predict_action / encode / predict / rollout / get_cost`
- 结合 train/eval/config 对 architecture 文件做反向加分
- 为 second-pass 提供候选顺序和本地校验信号

### 当前 AST 明确不做什么

- full graph analysis
- 通用 PageRank
- Tree-sitter 多语言支持
- 本地完整符号级推理器

### 当前结论

轻量 AST 已经足够支撑第一遍排序，继续大幅加重排序系统的回报正在下降。

---

## 真实仓库验证反馈

### VLA-Adapter

当前判断：

- `openvla.py`、`prismatic.py` 能稳定进入 architecture entry 前列
- `base_vlm.py` 被压低，不再压过 concrete wrapper
- `action_heads.py` 与 `projectors.py` 至少能在 AST tags / debug 里稳定被识别

结论：

- 入口层已经明显优于早期版本
- 对典型 VLA repo，当前排序已经接近可用

### ReconVLA

当前判断：

- `recon_arch.py`、`recon_qwen.py` 能进入更合理的位置
- 子模块 `pixel_decoder/builder.py`、`multimodal_encoder/builder.py` 不再轻易压过顶层 assembly

结论：

- “top-level arch 高于 submodule builder”这条已经基本站住
- 仍有 refinement 空间，但已经不妨碍进入 second-pass

### ACoT-VLA

P1.5 时的问题：

- `architecture_entry` 可以用
- 但 `architecture_skeleton_candidates` 基本为空
- `component` 层会混入 `scripts/compute_norm_stats.py`

P1.6 之后：

- `skeleton` 不再为空
- `pi0.py`、`vit.py`、`model.py` 一类文件能进入 skeleton 列表
- `compute_norm_stats.py` 不再污染 component 前列

结论：

- `skeleton / component` 的 AST 补强是有效的
- ACoT-VLA 从“入口层可用、骨架层很弱”提升到了“整体基本可用”

### le-wm

这是额外加入的压力测试样例。它不是典型的 `models/policy/backbone/action_head` 风格，而是更偏 flat world-model / JEPA 风格：

- `jepa.py`
- `module.py`
- `train.py`
- `eval.py`

补强后的结果：

- `jepa.py` 能被抬到 `architecture_entry`
- `module.py` 能进入 `architecture_skeleton`
- `train.py / eval.py` 自身不会误抬成 architecture entry 顶部

结论：

- 当前系统已经开始具备对 flat world-model repo 的最小泛化能力
- mixed skeleton/component file 仍然会多层留痕，但已经不是进入 second-pass 的阻塞点

---

## P2 前置：两轮 second-pass reading

### 目标

从第一遍排序结果中挑 3-8 个关键文件，做更细的文件内证据抽取，强化 `Concept2Code tracing`。

### 当前实现状态

已完成，日期：

- 2026-04-26

当前 `codex` 主流程已经变成：

```text
first-pass ranking
-> second-pass round 1
-> 本地校验 missing files / uncertain links
-> second-pass round 2
-> concept2code.json / session artifacts
-> final markdown
```

### Round 1

本地会先从第一遍排序结果中选出 3-8 个关键文件。

选择来源优先级：

- `reading_path`
- `architecture_entry`
- `architecture_skeleton`
- 少量 `architecture_component`
- 少量 train / config / inference 文件

本地会对这些文件抽取：

- `excerpt`
- `top_symbols`
- `local_evidence`
- `selected_reason`

然后交给 Codex 做第一轮深读。

### Round 2

Codex 可以在 Round 1 中返回：

- `missing_files`
- `uncertain_links`

但这些建议不会直接进入补读，而是必须经过本地校验：

- 文件必须真实存在于 repo
- 文件必须与 Round 1 关键文件或已有链路存在可解释关联
- helper / script 噪音会被过滤
- 补读数量受 `round2_max_files` 限制

因此 Round 2 的真实逻辑是：

```text
Codex 提建议 -> 本地筛选 -> 再补读
```

### 结构化证据落盘

当前 session 不再只有：

- `request.json`
- `evidence.md`
- `output.md`

还会新增：

- `second-pass-round-1.json`
- `second-pass-round-1.md`
- `second-pass-round-2.json`
- `second-pass-round-2.md`
- `concept2code.json`

其中 `concept2code.json` 不是简单的 `concept -> file`，而是最小可复用证据单元，字段至少包括：

- `concept`
- `status`
- `files`
- `symbols`
- `evidence_span`
- `confidence`
- `reason`
- `round`

这一步的意义是：

- 后续接长期 memory 时，不需要再从最终 markdown 里反解析
- 可以更清楚地区分 `CONFIRMED`、`INFERRED`、`MISSING`

### 配置

当前没有新增复杂 CLI，而是沿用现有配置体系，新增了：

- `second_pass_enabled`
- `second_pass_round1_max_files`
- `second_pass_round2_max_files`

默认值：

```text
enabled = true
round1_max_files = 8
round2_max_files = 4
```

### 测试状态

本轮已补：

- mock Codex 测试
- Round 2 本地校验测试
- `second_pass_enabled = false` 的回退测试
- `concept2code.json` 落盘测试

当前全量测试结果：

```text
48 passed
```

### 当前结论

此前“second-pass 还没有实现”的判断已经过期。

更新后的判断是：

1. 第一遍排序层已经够用
2. 两轮 second-pass 已经进入实现
3. 当前主线应转向：
   - 用真实仓库继续验证 Concept2Code tracing 的稳定性
   - 再把结构化 evidence 接到长期 memory

---

## 现在不要优先做什么

当前不建议优先投入：

- full AST graph
- Tree-sitter
- 通用 PageRank
- 更重的排序层重构

原因不是这些永远没用，而是当前收益顺序已经变了：

```text
排序层继续变重 < second-pass 质量提升 < 结构化证据复用
```

---

## 下一步

明确的下一步是：

1. 用真实仓库继续校验两轮 second-pass 的 `Concept2Code tracing`
2. 检查 `concept2code.json` 是否足够稳定，可直接接到后续长期 memory
3. 再考虑：
   - session reflection
   - skill memory
   - retrieval

如果这三步稳定，再进入更完整的 Learning Loop。

---

## ACoT-VLA second-pass 校验（2026-04-26）

这一次专门用本地已 clone 的 `ACoT-VLA` 做了真实 second-pass 校验，目标是检查：

- 两轮 second-pass 的 `Concept2Code tracing` 产出是否已经达到“可用”
- `concept2code.json` 风格的结构化结论是否已经足够稳

### 校验方式

- 使用本地 paper 输入：
  - `notes/ACoT-VLA-architecture-study.md`
- 使用本地 repo：
  - `.study-agent/repos/ACoT-VLA`
- focus：
  - `architecture`
  - `policy`
  - `bridge_attention`
  - `reasoning_tokens`
  - `action_head`
- 实际触发了真实 Codex 的两轮 second-pass

### 当前 second-pass 产出表现

当前 merged 后的核心 concept links 大致是：

- `policy` -> `CONFIRMED / high`
- `architecture` -> `CONFIRMED / high`
- `bridge_attention` -> `INFERRED / medium`
- `reasoning_tokens` -> `INFERRED / medium`
- `action_head` -> `INFERRED / medium`

### 做得对的地方

- `policy` 的确认是可靠的，能够正确落到 `src/openpi/policies/policy.py`
- architecture 主骨架也基本找对了，能把：
  - `acot_vla.py`
  - `pi0.py`
  - `pi0_fast.py`
  - `model.py`
  - `training/config.py`
  这几类文件串起来
- 对 `bridge_attention`、`reasoning_tokens` 保持 `INFERRED` 是合理的
  - `bridge_attention` 更像在别的论文或仓库里会显式命名的概念，在 `ACoT-VLA` 里并不是一个直接落地成模块名的核心术语
  - `reasoning_tokens` 在这个 repo 里也更像解释性概念，而不是代码中显式存在的 symbol
- Round 2 的本地校验链路是有效的，能够把 `model.py`、`pi0_fast.py` 这类补读文件加进来，而不是完全盲信 Codex 点名

### 还不满足要求的地方

当前结果还不能算“完全满足要求”，但问题已经不应再归咎于 `bridge_attention / reasoning_tokens` 仍是 inferred。

真正还不够好的地方主要是：

1. `action_head` 仍然只有 `INFERRED`
   - 但人工检查 `src/openpi/models/acot_vla.py` 可以看到：
     - `self.coarse_action_out_proj`
     - `self.action_out_proj`
     - `sample_actions()`
     - `compute_loss()`
   - 这些其实已经提供了更直接的 action output / action projection 证据

2. 与 action generation 更直接相关的代码链还没有被 second-pass 吃深
   - 例如：
     - `explicit_action_reasoner`
     - `implicit_action_reasoner`
     - `UnifiedAttentionModule`
     - `action_reasoning_fusion`
     - `action_out_proj`

3. 当前补读会提出“继续读已经选中过但 excerpt 不完整的大文件”
   - 这说明问题不完全是选错文件
   - 更大的问题是：
     - 对大文件只取了前部 excerpt
     - 还没有做面向 concept 的二次定位与补片段

### 根因判断

这次 `ACoT-VLA` 校验暴露的主要短板不是第一遍排序，而是 second-pass 的局部证据切片策略。

当前 second-pass 对大文件更像：

```text
选中文件 -> 截前一段 excerpt -> 交给 Codex
```

而 `ACoT-VLA` 这种大文件真正关键的 Concept2Code 证据往往在：

- 类定义的后半段
- `compute_loss()`
- `sample_actions()`
- `action_out_proj / reasoner / fusion` 等成员定义附近

所以系统现在更像“文件选对了，但喂给 Codex 的片段还不够对”。

### 当前阶段结论

对 `ACoT-VLA` 来说，这版两轮 second-pass 的水平可以评价为：

- `整体可用`
- `能正确保留不确定性`
- `对于跨仓库迁移来的概念没有乱确认`
- `但对 repo 内本来可以直接确认的 action-generation 证据还吃得不够深`

更具体地说：

- 如果目标只是“先把关键文件与大致概念链路找出来”，这版已经够用
- 如果目标是“把 action output / action reasoning path 做到代码级直接确认”，这版还不够

### 下一步修正重点

基于这次校验，当前最值得做的不是继续加重排序层，而是补 second-pass 的局部证据抽取：

1. 对大文件从“前缀 excerpt”改成“symbol-aware / concept-aware 片段抽取”
2. 如果 Round 1 / Round 2 都在反复点名同一个文件，允许补读该文件的后续片段，而不是只补新文件
3. 优先围绕这些高价值 symbol 做片段抽取：
   - `sample_actions`
   - `compute_loss`
   - `action_out_proj`
   - `coarse_action_out_proj`
   - `explicit_action_reasoner`
   - `implicit_action_reasoner`
   - `action_reasoning_fusion`

这说明下一步的主线仍然是 second-pass 质量提升，而不是回到更重的排序系统重构。
