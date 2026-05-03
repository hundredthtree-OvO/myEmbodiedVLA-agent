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

---

## second-pass 真实回归补充（2026-04-27）

这一天在完成 `symbol-aware / concept-aware` 片段抽取后，又额外做了两组真实仓库回归：

- `ACoT-VLA`
- `VLA-Adapter`

目的不是重新验证第一遍排序，而是专门检查：

- second-pass 是否已经从“文件前缀 excerpt”升级成“更贴近关键 symbol 的局部证据”
- `concept2code.json` 的结论是否更稳、更像人工判断
- 系统是否会因为补了更多局部证据而误把本来只该 `INFERRED` 的概念抬成 `CONFIRMED`

### ACoT-VLA：相对上一版有明确进步

和上一轮相比，这次最重要的进步不是“多确认了几个概念”，而是**证据基础明显变对了**。

上一轮的问题更像：

```text
文件选对了
-> 但 second-pass 主要看的是文件前缀
-> 真正关键的 action path 没被吃进去
```

这次则已经能稳定抽到：

- `sample_actions`
- `compute_loss`
- `action_out_proj` 附近逻辑
- `Observation` 中的 `tokenized_prompt / tokenized_prompt_mask / token_ar_mask / token_loss_mask`

因此，当前 `ACoT-VLA` 的 second-pass 结果更接近人工判断：

- `policy` -> `CONFIRMED / high`
- `architecture` -> `CONFIRMED / high`
- `bridge_attention` -> `INFERRED / medium`
- `reasoning_tokens` -> `INFERRED / medium`
- `action_head` -> `INFERRED / medium`

这里要特别强调：

- `bridge_attention` 在 `ACoT-VLA` 中并不是一个 repo 内显式落地的命名模块，因此保持 `INFERRED` 是合理的
- `reasoning_tokens` 也更像解释性概念，而不是代码里直接存在的 symbol，因此继续保持 `INFERRED` 也是合理的

也就是说，这一版的提升主要体现在：

- 不再因为证据不足而只会引用 schema 或 config 层面的弱证据
- 能用 `sample_actions / compute_loss / action_out_proj` 这类更贴近 action generation 的代码证据支撑判断
- 没有把本来应该保留不确定性的概念误抬成 `CONFIRMED`

当前仍未完全解决的问题是：

- `action_head` 依然只有 `INFERRED`
- 根因不再是“文件选错”，而是 second-pass 虽然已经能打到 action path，但还没有直接打到“head 定义本身”这一层
- 也就是说，现在的系统已经能证明“动作输出路径是核心的一部分”，但还没充分证明“这里存在一个可以直接命名的独立 action head 模块”

结论：  
`ACoT-VLA` 这轮可以判定为**相对上一版有明确进步，而且进步方向是对的**。

### VLA-Adapter：second-pass 的泛化也成立

在确认 `ACoT-VLA` 有明确进步后，又额外跑了 `VLA-Adapter`。

这轮结果说明：新的片段抽取策略并不是只对 `ACoT-VLA` 有效，而是对另一类更典型的 VLA 仓库也能工作。

当前 `VLA-Adapter` 的 merged concept links 大致是：

- `architecture` -> `CONFIRMED / high`
- `policy` -> `CONFIRMED / high`
- `projector` -> `CONFIRMED / high`
- `bridge_attention` -> `INFERRED / low`
- `action_head` -> `INFERRED / medium`

这组结果整体上是合理的：

1. `architecture`
   - `PrismaticVLM`
   - `OpenVLA`
   - `load_vla`
   - `LLMBackbone`
   - `ActionTokenizer`
   这些文件和 symbol 已经能比较清楚地串成完整主链

2. `policy`
   - `OpenVLA.predict_action`
   - `ActionTokenizer.__call__`
   - `ActionTokenizer.decode_token_ids_to_actions`
   现在已经能明确说明“从图像/指令到动作”的实际推理路径，而不只是泛泛说“模型会生成动作”

3. `projector`
   - `PrismaticVLM`
   - `ProprioProjector.forward`
   - `NoisyActionProjector.forward`
   这说明 second-pass 已经能正确命中 projector 的具体实现，而不是只停留在模块名层面

4. `bridge_attention`
   - 继续保持 `INFERRED / low`
   - 这也合理，因为当前本地证据更像“多模态融合进入 LLM token path”，而不是直接看到一个叫 `bridge_attention` 的模块

5. `action_head`
   - 仍然是 `INFERRED / medium`
   - 但这次的 `INFERRED` 比之前更有内容，因为它已经能用：
     - `OpenVLA.predict_action`
     - `ActionTokenizer`
     - `LLMBackbone`
     说明“动作是通过 LLM token output + action token semantics 来实现的”
   - 换句话说，这里保留 `INFERRED` 不是因为完全没抓到动作输出逻辑，而是因为当前证据更支持“复用 LM token head”，而不是“存在一个独立命名的 action_head 类”

结论：  
`VLA-Adapter` 这轮也说明 second-pass 的片段抽取改进具有**可泛化性**，不是只对 `ACoT-VLA` 的定制修补。

### 当前阶段判断更新

截至这轮回归，可以把 second-pass 的现状更新为：

- 第一遍排序层已经基本够用，不再是当前主瓶颈
- second-pass 已经从“能跑”进入“开始真正提升结论质量”的阶段
- 新的 `symbol-aware / concept-aware` 片段抽取已经在真实仓库上证明有收益
- 当前主要短板不再是“完全吃不到关键文件”，而是：
  - 对某些概念能证明输出路径存在
  - 但还不能总是直接打到“独立模块定义”这一层

因此，后续最合理的主线仍然是：

1. 继续提升 second-pass 的局部证据抽取与补片段策略
2. 不再优先加重排序层
3. 在此基础上再逐步考虑：
   - evidence quality gate 的细化
   - prompt budget
   - repo cache
   - session / memory 的后续积累

---

## P2.1 短计划：paper understanding pass + 结构问句驱动 second-pass

结合这轮讨论，P2.1 不建议再走“继续补 concept template”的路线，而应该收成下面这条更稳的主线：

### 目标

让系统不再只靠 `focus` 关键词驱动 second-pass，而是先形成一层轻量的 paper-side understanding，再决定去代码里验证什么。

### 核心改动

1. 新增 `paper understanding pass`
   - 从论文文本层和图示层抽：
     - 核心主张
     - 显式模块
     - 关键待验证问题
     - 论文概念是 `paper_explicit` 还是 `paper_implicit`

2. second-pass 从“概念词命中”升级成“结构问句驱动”
   - 例如对 `bridge_attention`，不再只找 `bridge/attention`
   - 而是去问：
     - query 在哪
     - condition KV 在哪
     - cross/self attention 在哪
     - fusion/gating 在哪

3. 输出层区分：
   - `paper_status`
   - `code_status`
   让“论文显式、代码结构性落地”这种情况能够被更清楚地表达

### 实现约束

- 不走“大而全 concept template 库”
- 不写 repo-specific 规则
- 优先保留通用结构角色框架，再由每篇论文临时生成自己的结构假设
- 论文读取后续走双通道：
  - 文本层：`pypdf`
  - 图示层：关键页/关键图截图 + 视觉理解
  - OCR 仅做补充

### 进入条件

当前 second-pass 已经证明“片段抽取”有明显收益，因此 P2.1 可以作为下一轮最自然的延续，而不是继续把主要精力放在排序层上。

### 当前进展补充（2026-04-27）

这一轮已经把 P2.1 的基础设施部分先落下来了，重点是“论文侧工作目录 + 轻量 paper understanding”，而不是一开始就做很重的论文理解系统。

已完成部分：

1. 论文统一工作目录
   - 同一篇论文现在会落到：
     - `result/<paper_slug>/`
   - 目录下已拆分出：
     - `source/`
     - `extracted/`
     - `notes/`
     - `outputs/`

2. 文本层落盘
   - 当前论文文本会保存到：
     - `result/<paper_slug>/extracted/paper_text.md`

3. 图示层基础缓存
   - 如果输入是 PDF，会尝试：
     - 基于页文本选关键页
     - 初次渲染这些关键页为 PNG
     - 保存到：
       - `result/<paper_slug>/extracted/figures/`
   - 当前只做页级渲染与缓存复用
   - 暂时不上 OCR

4. `paper understanding pass`
   - 会生成：
     - `result/<paper_slug>/notes/paper-understanding.md`
     - `result/<paper_slug>/notes/paper-concepts.json`
   - 当前版本已经能记录：
     - focus 概念在论文里是 `paper_explicit / paper_implicit / user_defined`
     - 概念摘要
     - 结构角色提示
     - 待验证问题

5. pipeline 轻接入
   - `paper understanding` 已接入 analyze 主流程
   - second-pass 会把 `paper understanding` 里的概念/问题一起带入 prompt 与局部证据选择
   - 最终笔记还会额外写回：
     - `result/<paper_slug>/outputs/study-note.md`
   - 如果本轮有 second-pass 结果，也会写回：
     - `result/<paper_slug>/outputs/concept2code.json`

当前仍未做的部分：

- OCR
- 自动精确裁图
- 从图中自动抽模块框与箭头
- 更强的 paper-side 结构图理解

因此，这轮更准确的定位是：

```text
P2.1 的论文侧基础设施已经到位，
paper understanding pass 已经轻量接入，
下一步才是继续增强“论文理解如何更强地驱动 second-pass”。
```

---

## 2026-05-03 重构补充

这轮做了三件基础重构：

1. PDF 管线切换到 `PyMuPDF`
   - 论文文本提取和关键页渲染统一走同一后端
   - 不再把 `pypdf / pdftotext` 作为当前主路径

2. `src/study_agent` 目录按领域拆分
   - `paper/`：论文工作目录、PDF、论文理解
   - `repo/`：repo ingestion、代码解析、排序
   - `graph/`：图模型、图存储、图查询抽象

3. `paper_understanding` 升级为 `claim / concept / question` 抽取器
   - `focus` 退到补充和加权角色
   - 系统先抽论文 claim、显式概念、隐式概念，再生成待验证问题

当前结论：

- 这轮已经把论文侧上游从“关键词主导”推进到“论文理解主导的过渡态”
- 下一步主线仍然是继续增强 paper-side understanding，并把 second-pass 逐步迁到 span / 局部子图级证据
