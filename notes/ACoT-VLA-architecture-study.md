# ACoT-VLA 架构学习笔记

## 1. 任务与输入

- Repository: `https://github.com/AgibotTech/ACoT-VLA`
- Paper: `https://arxiv.org/pdf/2601.11404`
- Focus: `EAR`, `IAR`, `kv cache`
- Analysis mode: `paper-aligned`

## 2. 仓库入口与主干候选

- Candidate 1: `src/openpi/models/acot_vla.py` - `class ACOT_VLA`
  - 作用：这是 ACoT-VLA 的核心实现，EAR、IAR、AGP 风格的动作预测流程都集中在这里。
- Candidate 2: `src/openpi/training/config.py` - `TrainConfig(name="acot_icra_simulation_challenge_reasoning_to_action")`
  - 作用：这里决定 baseline 训练时是否启用 EAR/IAR，以及 IAR 用的是哪一种 KV-cache 交互策略。
- Candidate 3: `README.md`
  - 作用：给出论文层面的组件划分，能帮助把 Figure 2 的三块结构映射回代码。

## 3. 架构总览

ACoT-VLA 在代码里不是拆成多个顶层模型文件，而是把整套结构折叠进 `src/openpi/models/acot_vla.py` 的 `ACOT_VLA` 类中。主干首先构建一个共享的视觉语言底座 `self.PaliGemma = nnx.Dict(llm=llm, img=img)`，其中 `img` 来自 SigLIP，`llm` 来自 Gemma，并且 `gemma.Module(configs=[paligemma_config, coarse_action_expert_config, action_expert_config], ...)` 明确表明这里同时维护了基础 VLM、粗动作 expert、细动作 expert 三套配置。这个设计对应论文 Figure 2 中“共享 VLM backbone + EAR + IAR + action head”的总体框架。`CONFIRMED`

从功能上看，代码里的三段主流程分别是：

- 前缀编码：`embed_prefix()` 把图像 token 和文本 token 组织成共享前缀，再送入 `self.PaliGemma.llm(...)` 得到 prefix 表征与 `kv_cache`。
- EAR 路径：使用 `suf_type="reasoner"` 的 suffix，把粗粒度 noisy actions 投影后送入 coarse expert 分支，输出 coarse reference trajectory。
- IAR 路径：直接从 prefix forward 得到的 `kv_cache` 中抽取 K/V，再通过隐式 extractor 得到 action prior tokens。
- 最终动作预测：`suf_type="expert"` 的 suffix 同时接收 noisy actions、EAR 输出和 IAR 输出，经融合后由 action expert 分支预测最终动作。

把论文 Figure 2 的三块映射到代码时，可以这样看：

- 共享 VLM backbone: `src/openpi/models/acot_vla.py` - `ACOT_VLA.__init__`, `embed_prefix`
- EAR: `src/openpi/models/acot_vla.py` - `coarse_action_in_proj`, `coarse_action_out_proj`, `UnifiedAttentionModule explicit_action_reasoner`, `embed_suffix(..., suf_type="reasoner")`
- IAR: `src/openpi/models/acot_vla.py` - `LearnableQueryExtractor` / `AttentionPoolingExtractor` / `DownsampleExtractor`，以及 `implicit_action_reasoner_interact`
- Action-Guided Prediction: `src/openpi/models/acot_vla.py` - `embed_suffix(..., suf_type="expert")`, `action_reasoning_fusion`, `action_out_proj`

一个重要实现差异是：论文把 EAR 描述成一个轻量 Transformer，把 IAR 描述成 KV-cache 上的 cross-attention 模块；代码里它们最终都被嵌入到 `ACOT_VLA` 这个大类里，并通过共享 `PaliGemma.llm` 和一组对齐/融合模块来落地，而不是完全独立的顶层子模型。这个“单文件整合实现”是代码理解时最重要的入口。`CONFIRMED`

## 4. 核心执行路径

### 4.1 训练时的主路径

1. `src/openpi/models/acot_vla.py` - `compute_loss`
   - 入口，接收 `observation`, `actions`, `coarse_actions`，并构造 flow-matching 风格的 noisy action 状态。
2. `src/openpi/models/acot_vla.py` - `embed_prefix`
   - 将图像与文本 prompt 编成 prefix tokens，并建立 prefix attention mask。
3. `src/openpi/models/acot_vla.py` - `self.PaliGemma.llm([prefix_tokens, None, None], ...)`
   - 先只跑 prefix，拿到共享上下文和 `kv_cache`。
4. `src/openpi/models/acot_vla.py` - `embed_suffix(..., suf_type="reasoner")`
   - 构造粗动作 reasoner 的 suffix token 序列。
5. `src/openpi/models/acot_vla.py` - `self.PaliGemma.llm([prefix_tokens, suffix_ref_action_tokens, None], ...)`
   - 让 coarse action expert 生成 EAR 对应的 reference trajectory。
6. `src/openpi/models/acot_vla.py` - `self.implicit_action_reasoner(K_rearranged, V_rearranged)`
   - 从 prefix `kv_cache` 中提取 IAR 对应的隐式动作先验。
7. `src/openpi/models/acot_vla.py` - `embed_suffix(..., suf_type="expert")`
   - 将 noisy expert actions 与显式/隐式 reason 融合成最终 expert suffix。
8. `src/openpi/models/acot_vla.py` - `self.PaliGemma.llm([prefix_tokens, None, suffix_expert_tokens], ...)`
   - 最终动作 expert 分支输出 `suffix_expert_out`。
9. `src/openpi/models/acot_vla.py` - `action_out_proj` / `coarse_action_out_proj`
   - 投影到动作空间，并计算 flow matching 损失。

### 4.2 推理时的主路径

1. `src/openpi/models/acot_vla.py` - `sample_actions`
   - 推理入口。
2. `src/openpi/models/acot_vla.py` - prefix forward 得到 `kv_cache`
   - 先只缓存图像+语言前缀。
3. `src/openpi/models/acot_vla.py` - `step_explicit_action_reasoner`
   - 通过 `jax.lax.while_loop` 迭代去噪，得到 coarse reference trajectory。
4. `src/openpi/models/acot_vla.py` - `step_expert`
   - 再用最终动作 expert 在同样的 ODE/flow matching 循环里生成最终动作。

这意味着推理过程是“两阶段去噪”而不是“一次性直接出动作”：先出 coarse action reason，再出 final action。这个执行顺序和论文“EAR 先给显式引导，再辅助最终动作头”的叙述是一致的。`CONFIRMED`

## 5. 核心模块深挖

### 5.1 共享 VLM Backbone

- 定位：`src/openpi/models/acot_vla.py` - `ACOT_VLA.__init__`
- 角色：负责统一处理视觉和语言前缀，是 EAR、IAR、最终动作预测共用的感知语义底座。
- 构造方式：
  - `img = _siglip.Module(...)`
  - `llm = _gemma.Module(configs=[paligemma_config, coarse_action_expert_config, action_expert_config], ...)`
  - `self.PaliGemma = nnx.Dict(llm=llm, img=img)`
- 输入输出：
  - 输入：多视角图像、tokenized prompt、后续可拼接的 action suffix
  - 输出：prefix/suffix token hidden states，以及 `kv_cache`
- 关键调用链：
  - `embed_prefix` -> `self.PaliGemma.img(...)`
  - `self.PaliGemma.llm([prefix_tokens, ...])`
- 证据等级：`CONFIRMED`

这里一个值得注意的点是，代码中的 “dual experts” 不是额外的 Python 顶层模块，而是通过 `Gemma` 的多 config 机制并进同一个 `llm` 里。这使得 ACoT-VLA 的“共享 backbone + 双 action reasoners”在实现上看起来更像一个多分支 Gemma/VLM 体系，而不是松耦合的三块网络。`INFERRED`

### 5.2 EAR 对应的粗动作推理分支

- 定位：`src/openpi/models/acot_vla.py` - `coarse_action_in_proj`, `coarse_action_out_proj`, `embed_suffix(..., suf_type="reasoner")`, `step_explicit_action_reasoner`
- 角色：生成 coarse reference trajectory，对应论文里的 Explicit Action Reasoner。
- 构造方式：
  - 粗动作输入先经 `coarse_action_in_proj`
  - 时间条件通过 `coarse_time_mlp_*` 注入
  - 如果要与最终动作分支对齐，则使用 `self.explicit_action_reasoner = UnifiedAttentionModule(...)`
- 输入输出：
  - 输入：粗动作噪声 `x_ref_t`、时间步 `t`、prefix context
  - 输出：coarse reference trajectory，再被作为 `explicit_action_reason`
- 关键调用链：
  - `compute_loss` / `sample_actions`
  - `embed_suffix(..., suf_type="reasoner")`
  - `self.PaliGemma.llm([prefix_tokens, suffix_ref_action_tokens, None], ...)`
  - `coarse_action_out_proj(...)`
- 证据等级：`CONFIRMED`

论文说 EAR 是 lightweight transformer。代码层面没有一个单独命名为 `EARTransformer` 的类，而是通过“coarse action expert + suffix token 序列 + Gemma 分支”来实现。因此你读代码时不要死盯着“有没有 EAR 类名”，真正的 EAR 语义是这条 coarse branch。`CONFIRMED`

### 5.3 IAR 对应的隐式动作推理分支

- 定位：`src/openpi/models/acot_vla.py` - `LearnableQueryExtractor`, `AttentionPoolingExtractor`, `DownsampleExtractor`, `implicit_action_reasoner_interact`
- 角色：从 VLM 内部表示中抽取潜在动作先验，对应论文里的 Implicit Action Reasoner。
- 构造方式：
  - `ACOTConfig` 支持三种 extractor：query-based、attention-pooling、downsample-based
  - baseline 配置实际打开的是 `downsample_based_implicit_extractor=True`
  - 之后再通过 `implicit_action_reasoner_interact = UnifiedAttentionModule(...)` 与 action expert token 交互
- 输入输出：
  - 输入：`kv_cache` 重排后的 `K_rearranged`, `V_rearranged`
  - 输出：每层聚合后的 `implicit_action_reason`
- 关键调用链：
  - prefix forward -> `kv_cache`
  - `K_all, V_all = kv_cache`
  - `einops.rearrange(..., 'L B T 1 D -> B L T D')`
  - `self.implicit_action_reasoner(...)`
  - `self.implicit_action_reasoner_interact(...)`
- 证据等级：`CONFIRMED`

### 5.4 AGP 风格的最终动作预测分支

- 定位：`src/openpi/models/acot_vla.py` - `embed_suffix(..., suf_type="expert")`, `action_reasoning_fusion`, `action_out_proj`
- 角色：把 noisy action、自显式 reason、自隐式 reason 融合后输出最终可执行动作。
- 构造方式：
  - 先构造 action expert token
  - 若双 reason 同时启用，分别得到 `aligned_explicit_action_reason_tokens` 与 `aligned_implicit_action_reason_tokens`
  - 先各自线性投影到统一宽度，再拼接后通过 `action_reasoning_fusion`
- 输入输出：
  - 输入：expert noisy actions + optional explicit/implicit guidance
  - 输出：`suffix_expert_out` -> `action_out_proj` -> final actions
- 关键调用链：
  - `embed_suffix(..., suf_type="expert")`
  - `explicit_action_reasoner(...)`
  - `implicit_action_reasoner_interact(...)`
  - `action_reasoning_fusion(...)`
  - `self.PaliGemma.llm([prefix_tokens, None, suffix_expert_tokens], ...)`
- 证据等级：`CONFIRMED`

这里最值得学的是：论文图里看起来像“一个动作头接两个 guidance”，但代码里其实是“先对齐，再投影，再融合，再送入 action expert”。这比图上画得更工程化一些。`CONFIRMED`

## 6. 关注点专项

### 6.1 EAR

- Direct symbol hit: `yes`
- Closest evidence: `src/openpi/models/acot_vla.py` - `self.explicit_action_reasoner`, `embed_suffix(..., suf_type="reasoner")`, `step_explicit_action_reasoner`
- 解释：
  - 论文里的 EAR 是显式动作推理器，代码里对应一条单独的 coarse action branch。
  - `coarse_action_in_proj` 负责把粗动作序列投到 coarse expert 维度。
  - `embed_suffix(..., suf_type="reasoner")` 负责把 coarse noisy actions + time embedding 变成 reasoner token 序列。
  - 训练时通过 `self.PaliGemma.llm([prefix_tokens, suffix_ref_action_tokens, None], ...)` 一次前向得到 `suffix_ref_action_out`，再经 `coarse_action_out_proj` 变回 coarse trajectory。
  - 推理时通过 `step_explicit_action_reasoner` 在 `while_loop` 中不断更新 `x_t`，最后得到 `explicit_action_reason`。
- 装配位置：
  - 在 `ACOT_VLA.__init__` 中创建粗动作相关投影和 `explicit_action_reasoner`
  - 在 `compute_loss` 和 `sample_actions` 中实际调用
- 上下游：
  - 上游：prefix context、coarse noisy action、time embedding
  - 下游：最终 expert 分支在 `embed_suffix(..., suf_type="expert")` 中再次消费 `explicit_action_reason`
- 证据等级：`CONFIRMED`

一个容易误解的点是：`self.explicit_action_reasoner = UnifiedAttentionModule(...)` 本身不是 EAR 的全部，它更像是“把 coarse reason 对齐到 final action token 空间”的桥接器；真正的 EAR 还包含 coarse branch 的 token 化、LLM 前向和 coarse output projection。`CONFIRMED`

### 6.2 IAR

- Direct symbol hit: `yes`
- Closest evidence: `src/openpi/models/acot_vla.py` - `self.implicit_action_reasoner`, `implicit_action_reasoner_interact`
- 解释：
  - IAR 先从 prefix-only forward 的 `kv_cache` 中读出 K/V。
  - 然后根据配置选择 extractor。baseline 使用 `DownsampleExtractor`，而不是论文 Table 6 中的另两种备选。
  - 抽出的隐式 token 并不直接拼到动作头，而是先通过 `implicit_action_reasoner_interact` 与 `action_expert_tokens` 做一次 cross-attention 风格交互。
- 装配位置：
  - `ACOT_VLA.__init__` 中根据配置选择 extractor
  - `compute_loss` / `sample_actions` 中从 `kv_cache` 提取
- 上下游：
  - 上游：prefix 的图像+文本缓存
  - 下游：`embed_suffix(..., suf_type="expert")` 中的融合逻辑
- 证据等级：`CONFIRMED`

IAR 在代码里最关键的不是“再跑一遍大模型”，而是“复用 prefix kv_cache 做轻量抽取”。这点和论文“latent action priors from VLM internal representations”是严格对齐的。`CONFIRMED`

### 6.3 kv cache

- Direct symbol hit: `yes`
- Closest evidence: `src/openpi/models/acot_vla.py` - `compute_loss`, `sample_actions`
- 解释：
  - `kv_cache` 的第一次生成发生在 prefix-only forward：
    - `prefix_tokens, prefix_mask, prefix_ar_mask = self.embed_prefix(observation)`
    - `_, kv_cache = self.PaliGemma.llm([prefix_tokens, None, None], ...)`
  - 这说明 cache 里装的是图像和语言前缀，不是动作 suffix。
  - 对 IAR 来说，cache 被拆成 `K_all, V_all`，再被重排成 `(B, L, T, D)` 供 extractor 按层读取。
  - 对推理来说，同一个 `kv_cache` 还会在 `step_explicit_action_reasoner` 和 `step_expert` 里被复用，以避免每一步都重算 prefix。
- 状态结构：
  - 原始形式：`K_all, V_all`
  - 重排形式：`einops.rearrange(K_all, 'L B T 1 D -> B L T D')`
- 读写时机：
  - 写入：prefix-only forward 时一次性建立
  - 读取 1：IAR 从 cache 抽动作先验
  - 读取 2：推理阶段的 reasoner/expert suffix 解码复用同一 cache
- 触发条件：
  - 只要进入 `compute_loss` 或 `sample_actions`，都先做 prefix forward 填 cache
- 证据等级：`CONFIRMED`

这份代码里的 kv cache 不是一个“单纯为了加速解码的工程细节”，而是同时承担了两种职责：

1. 给 IAR 提供跨层内部表示
2. 给后续 suffix 解码提供 prefix 复用

这正是它在 ACoT-VLA 里比普通 decoder cache 更值得研究的地方。`CONFIRMED`

## 7. 非核心层与暂不展开部分

- `scripts/train.sh` - 训练脚本包装层，只负责启动训练流程，不定义 ACoT 结构。
- `scripts/server.sh` - 服务启动脚手架，不包含模型架构本体。
- `examples/libero/convert_libero_data_to_lerobot.py` - 数据预处理层，和 EAR/IAR/AGP 的模型逻辑无关。
- `src/openpi/policies/*` - 策略/机器人适配层，负责数据接口和平台差异，不是 ACoT-VLA 的结构核心。
- `README.md` - 架构解释入口有帮助，但不是实现主体。

## 8. 建议阅读顺序

1. 从 `src/openpi/models/acot_vla.py` 的 `ACOT_VLA.__init__` 开始，先建立“共享 VLM + coarse expert + action expert + extractor”的整体图。
2. 再读 `src/openpi/models/acot_vla.py` 的 `embed_prefix`，看图像和文本如何变成 prefix tokens 与 `kv_cache`。
3. 接着读 `src/openpi/models/acot_vla.py` 的 `embed_suffix`，这是理解 EAR/IAR 如何注入最终动作分支的关键。
4. 然后读 `src/openpi/models/acot_vla.py` 的 `compute_loss`，看训练时如何把 coarse action、implicit reason、expert action 串起来。
5. 最后读 `src/openpi/models/acot_vla.py` 的 `sample_actions`，看推理时怎样先生成 explicit reason 再生成 final action。
6. 读完核心实现后，再回到 `src/openpi/training/config.py`，确认 baseline 实际打开的是哪些模块，特别是 `downsample_based_implicit_extractor=True`。

## 9. 未确认点

- 论文 Figure 2 中把 EAR 画成 Transformer block；代码里更像“coarse action expert 分支 + suffix token 化 + projection + optional alignment block”的组合实现。两者语义一致，但模块边界不是 1:1 命名对应。`INFERRED`
- `Gemma` 三配置并存的内部细节更多落在 `src/openpi/models/gemma.py`，这次没有展开到那一层，所以对“coarse expert 与 action expert 在 llm 内部到底共享多少参数”还不能完全确认。`INFERRED`
- 训练配置文件展示了 baseline 使用 downsample IAR，但不同 benchmark 配置是否都严格复现论文表中的最佳设置，还需要逐个 config 和实验日志核对。`INFERRED`
