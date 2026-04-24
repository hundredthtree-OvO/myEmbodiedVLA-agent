# VLA-Adapter 代码分析：Action Head 与 Bridge Attention

## 1. 分析范围与源码入口

这份笔记聚焦你关心的两个点：

1. 论文里 action head 提到的 `bridge attention` 设计
2. `action query`、三类 attention、以及一些值得学习的工程/模型设计

我主要对照了这些源码入口：

- GitHub 仓库首页：<https://github.com/OpenHelix-Team/VLA-Adapter>
- `prismatic/models/action_heads.py`：<https://github.com/OpenHelix-Team/VLA-Adapter/blob/main/prismatic/models/action_heads.py>
- `experiments/robot/openvla_utils.py`：<https://github.com/OpenHelix-Team/VLA-Adapter/blob/main/experiments/robot/openvla_utils.py>
- `experiments/robot/libero/run_libero_eval.py`：<https://github.com/OpenHelix-Team/VLA-Adapter/blob/main/experiments/robot/libero/run_libero_eval.py>
- `prismatic/models/vlas/openvla.py`：<https://github.com/OpenHelix-Team/VLA-Adapter/blob/main/prismatic/models/vlas/openvla.py>

补充说明：GitHub 页面本身适合确认文件位置与代码片段；为了更连续地读完整文件，我也用 GitExtract 镜像辅助定位了代码段，但结论仍以 GitHub 仓库中的实现为准。

---

## 2. 先给结论：这套 Bridge Attention 在代码里到底是什么

如果用一句话概括：

> VLA-Adapter 并没有把 action 直接当作 LLM token 继续顺序生成，而是额外接了一个轻量 policy head。这个 head 用一组“动作查询槽位”去读取三类上下文，再输出连续动作。

这三类上下文，在代码里对应为：

1. `x` 自身的 token/self attention
2. `h_a + p` 形成的条件分支
3. `h_t` 形成的任务分支

在 `MLPResNetBlock` 和 `MLPResNetBlock_Pro` 里，它们最终都被拼接成一次 softmax attention 来融合。

注意一点：变量命名和论文语义并不是完全一一对应，代码里甚至有一点“task / adapter”命名反过来的情况，所以读代码时不要只盯变量名，要盯“谁来自哪里”。

---

## 3. 整体调用链：从观测到动作

### 3.1 评估入口

在 `experiments/robot/libero/run_libero_eval.py` 中：

- 如果 `cfg.use_l1_regression=True`，会额外加载 `action_head`
- 如果 `cfg.use_proprio=True`，会额外加载 `proprio_projector`

关键逻辑在：

- `get_action_head(...)`
- `get_proprio_projector(...)`
- `get_action(...)`

其中 `get_action_head(...)` 会实例化：

```python
action_head = L1RegressionActionHead(
    input_dim=llm_dim,
    hidden_dim=llm_dim,
    action_dim=ACTION_DIM,
    use_pro_version=cfg.use_pro_version,
)
```

也就是说，bridge attention 不是嵌在主 VLM backbone 里重新训练一个大模型，而是外接一个很轻的连续动作头。

### 3.2 推理时如何喂给模型

`experiments/robot/openvla_utils.py` 的 `get_vla_action(...)` 很关键：

- 主视角图像来自 `obs["full_image"]`
- 如果 `cfg.num_images_in_input > 1`，会把 wrist 图像也一起拼到 `pixel_values`
- 如果 `cfg.use_proprio=True`，会先把 `obs["state"]` 做归一化，再作为 `proprio`
- 最终调用：

```python
action, _ = vla.predict_action(
    **inputs,
    unnorm_key=cfg.unnorm_key,
    do_sample=False,
    proprio=proprio,
    proprio_projector=proprio_projector,
    noisy_action_projector=noisy_action_projector,
    action_head=action_head,
    use_film=use_film,
)
```

这说明 VLM 主干负责产出视觉-语言隐藏表示，真正把这些表示桥接到动作空间的是额外的 `action_head`。

---

## 4. Action Query 在代码里的真实形态

论文里会说 action query，但在这份代码里它不是一个显式命名的 `ActionQuery` 类，而是隐式体现在 `L1RegressionActionHead.predict_action(...)` 里。

关键代码逻辑：

```python
cond_actions_hidden_states = torch.zeros(
    (batch_size, self.action_dim * NUM_ACTIONS_CHUNK, self.hidden_dim),
    device=device, dtype=actions_hidden_states.dtype
).detach()

rearranged_actions_hidden_states = cond_actions_hidden_states.reshape(
    batch_size, NUM_ACTIONS_CHUNK, -1
)
```

这里可以这样理解：

- 先造出一堆全 0 的动作槽位
- 槽位总数和 `action_dim * NUM_ACTIONS_CHUNK` 有关
- 再 reshape 成 `[batch, chunk_len, action_dim * hidden_dim]`
- 这些槽位就是 policy head 的查询起点，也就是 action query 的代码化实现

### 4.1 为什么说它是 query

因为后面进 `MLPResNet` 之后：

- `x` 就是当前动作槽位表示
- `q = self.q_proj(x)` 用它生成 query
- 然后 query 去读三路上下文

也就是说：

- 动作不是“被直接预测出来”
- 而是“先给几个动作查询槽位”
- 这些槽位通过 bridge attention 去读视觉/任务/本体状态条件
- 再经过 MLP ResNet 输出连续动作

这是很典型的 query-based decoder/policy 设计思路。

### 4.2 一个很值得注意的实现细节

训练阶段他们会加一段扰动：

```python
random_perturbations = learnable_random_perturbations(...)
rearranged_actions_hidden_states = rearranged_actions_hidden_states + random_perturbations
```

但这里有一个非常值得警惕的点：

- `learnable_random_perturbations(...)` 返回的是一次前向里临时创建的 `nn.Parameter`
- 它没有注册到 module 上
- 也就不会稳定出现在 optimizer 参数里

所以从严格实现上说，它并不是“真正可学习的 persistent query parameter”，更像是“每次训练前向注入的随机扰动”

这和很多 transformer decoder 里“可学习查询向量”那种长期训练参数并不一样。

这点很值得学习，也很值得批判性阅读：

- 从论文表述上，容易让人以为这是标准 learnable action queries
- 从代码实现上，它更像 zero query + stochastic perturbation

如果你后面想复现或改进这部分，我会优先考虑把它改成：

1. 显式注册的 `nn.Parameter` action queries
2. 再叠加可选噪声

这会更接近论文直觉，也更容易分析。

---

## 5. Bridge Attention 的三路 attention：代码怎么落地

### 5.1 原始版：`MLPResNetBlock`

在 `prismatic/models/action_heads.py` 里，`MLPResNetBlock` 做的事情很清楚：

- `x` 自己做 self attention
- `h_a` 和 `p` 先 concat 成一个条件分支
- `h_t` 作为另一组条件分支
- 三路 attention score 拼接后统一 softmax

对应代码逻辑可以压缩成：

```python
conditions = []
if h_a is not None:
    conditions.append(h_a)
if p is not None:
    conditions.append(p)
h = torch.cat(conditions, dim=1)

q_1 = self.q_proj(x)
k_tokens = self.k_proj(x)
v_tokens = self.v_proj(x)

k_task = self.k_proj(task_k)
v_task = self.v_proj(task_v)

k_adapter = self.k_proj(adapter_k)
v_adapter = self.v_proj(adapter_v)

attn_scores_tokens = q @ k_tokens^T
attn_scores_task = q @ k_task^T
attn_scores_adapter = q @ k_adapter^T * ratio_g

attn_scores = cat([tokens, task, adapter], dim=-1)
attn_weights = softmax(attn_scores / sqrt(d))
output = attn_weights @ cat([v_tokens, v_task, v_adapter], dim=2)
```

### 5.2 三路 attention 具体分别是什么

从“数据来源”而不是变量名看：

1. `attn_scores_tokens`
   - 来源：`x` 对 `x`
   - 作用：动作查询槽位之间的自组织/self attention
   - 意义：保证多个 action chunk / action slot 之间能互相协调

2. `attn_scores_task`
   - 来源：query 对 `h_a + p`
   - 代码变量名里写成了 `task`
   - 但实际输入是动作相关隐藏状态 `h_a` 加 proprio `p`
   - 更准确地说，这是“动作/状态条件分支”

3. `attn_scores_adapter`
   - 来源：query 对 `h_t`
   - 代码变量名里写成了 `adapter`
   - 但实际输入是 task hidden states
   - 更准确地说，这是“任务语义分支”

所以这里最容易把人绕晕的一点是：

> 代码变量名 `task` 和 `adapter`，在语义上基本是反着叫的。

如果按实际来源重命名，我会更愿意写成：

- `self_attn`
- `condition_attn` (`h_a + p`)
- `task_attn` (`h_t`)

### 5.3 gate 的作用

这部分有一个单标量门控：

```python
self.gating_factor = nn.Parameter(torch.zeros(1))
ratio_g = tanh(g)
attn_scores_adapter = ... * ratio_g
```

它控制的是第三路分支的相对强度。

这很像一个“可学习桥梁阀门”：

- 如果 gate 很小，模型主要依赖自注意力和另一条件分支
- 如果 gate 变大，说明模型更愿意从任务语义分支读信息

从 bridge attention 的视角看，这个 gate 很关键，因为它让模型不是死板地把所有条件等权融合，而是学会“什么时候更该听哪一路条件”。

---

## 6. Pro 版 Bridge Attention：更像一个正规的小型多源解码器

`MLPResNetBlock_Pro` 比原始版明显更成熟，主要升级有三点。

### 6.1 三路分支各自独立的 K/V 投影

原始版里：

- `k_proj/v_proj` 基本复用

Pro 版里：

- `k_self, v_self`
- `k_adapter, v_adapter`
- `k_task, v_task`

分开了。

这意味着不同来源的上下文不再被强迫映射到同一个 K/V 子空间，而是可以学到各自更合适的表示结构。

这是我认为最值得学习的一点之一，因为它体现了一个很常见的建模升级：

> 当你有多个异质条件源时，独立投影通常比共享投影更稳。

### 6.2 加了 RoPE

Pro 版里对：

- `q_1` 与 self tokens 的 key
- adapter key
- task key

都加入了 RoPE。

这说明作者意识到：

- 动作 chunk 本身有序
- task tokens / action-state tokens 也是序列
- 仅靠 MLP + attention，位置关系表达可能不够

RoPE 的加入能让这个小 policy head 更像一个轻量 transformer decoder。

### 6.3 仍然保留 gate，但更规范

Pro 版还是：

```python
attn_scores = [
    q @ k_tokens^T,
    q @ k_adapter^T,
    q @ k_task^T * ratio_g,
]
```

本质还是三路融合，只是实现更干净。

### 6.4 FiLM 代码存在，但基本没启用

Pro 版里有：

```python
self.film_gen = nn.Sequential(nn.Linear(dim, dim * 2))
```

但源码注释明确写了：

> `FiLM is useless; to avoid conflict with chkpt, it can be kept as is for now.`

而且 forward 里的 FiLM 调制代码是注释掉的。

这说明：

- 作者实验过 FiLM
- 但最终 checkpoint 对应的有效实现并不依赖它

这也是非常值得学习的现实细节：论文/仓库里出现的模块，不一定都是真正贡献性能的核心路径。

---

## 7. `h_t`、`h_a`、`p` 到底分别是什么

在 `L1RegressionActionHead.predict_action(...)` 里：

```python
task_hidden_states = actions_hidden_states[:, :, :self.num_task_tokens, :]
actions_hidden_states = actions_hidden_states[:, :, self.num_task_tokens:, :]
proprio_features = proprio_projector(proprio).unsqueeze(1)
```

可以这样理解：

### 7.1 `h_t`

- 来自前 `num_task_tokens`
- 是从 VLM 隐状态里切出来的一段“任务相关 token”
- 语义上更接近 language/task-conditioned context

### 7.2 `h_a`

- 是剩余部分的 hidden states
- 更接近动作相关、视觉相关、或桥接后的主上下文表示

### 7.3 `p`

- proprio 经 `proprio_projector` 投影到 LLM hidden dim
- 再作为额外 token 拼进去

所以这个 action head 的条件源可以概括成：

1. 任务语义 `h_t`
2. VLM 主体输出里与动作更相关的上下文 `h_a`
3. 本体状态 `p`

这三者共同构成“bridge”的输入。

---

## 8. 这套架构为什么有效

我认为它有效的核心不是“发明了一个很复杂的新 attention”，而是做对了下面几件事。

### 8.1 没让 LLM 直接硬扛连续控制

很多 VLA 会直接把 action tokenization 做得很重，逼着 LLM 按语言 token 的方式顺序生成动作。

VLA-Adapter 则是：

- backbone 负责视觉-语言理解
- 轻量 action head 负责连续控制映射

这种解耦特别适合 tiny-scale VLM。

### 8.2 条件注入是“主动读取”，不是“被动拼接”

如果只是简单把 proprio / image / text 全拼接后做 MLP，模型要自己学会怎么分辨谁更重要。

这里是 action query 主动去读：

- self
- action-state condition
- task condition

这种 query-based reading 往往比纯 concat 更高效。

### 8.3 gate 让“桥梁强度”可学习

bridge attention 最妙的地方不只是多看几路输入，而是允许模型学习“桥到底该搭多宽”。

一个标量 gate 虽然简单，但已经能明显体现这种 inductive bias。

### 8.4 Pro 版把异质条件分支处理得更干净

独立 K/V + RoPE 的升级，本质上是在告诉模型：

- 自注意力
- 任务条件
- 动作/本体条件

它们不是同一种信息，不应该完全共用投影空间。

---

## 9. 我觉得特别值得学习的几个模型部分

### 9.1 多视角图像输入的工程做法很实用

在 `get_vla_action(...)` 里，主视角和 wrist 图像分别经 processor 后，再在 `pixel_values` 维度拼接。

优点：

- 不需要重写整套数据接口
- 很容易扩展到双腕/多相机
- 对机器人任务很实用

这是一个很值得复用的工程模式。

### 9.2 Proprio 单独 projector，而不是粗暴 concat

`proprio_projector` 把低维机器人状态先投到 LLM hidden dim，再作为单独条件 token 提供给 action head。

这个做法比直接把 proprio 拼进最终 MLP 输入更自然，因为：

- 维度对齐更清晰
- 更适合走 attention 融合
- 更方便后续替换成多 token proprio encoding

### 9.3 主干和 policy 头完全解耦，checkpoint 也分开存

从 `get_action_head(...)` / `get_proprio_projector(...)` 的加载逻辑能看出来：

- action head 单独 checkpoint
- proprio projector 单独 checkpoint

这使得：

- 微调更灵活
- 部署更轻
- 也更适合做 ablation

这是非常值得学习的研究代码组织方式。

### 9.4 chunked open-loop action 设计

动作不是一步一步只吐 1 个 action，而是和 `NUM_ACTIONS_CHUNK`、`num_open_loop_steps` 绑定。

这意味着模型更像是在一次前向里预测一个短时动作片段。

对机器人控制来说，这通常能：

- 降低推理频率压力
- 提高吞吐
- 让 policy 学到更平滑的局部动作结构

---

## 10. 读这份代码时最容易误解的地方

### 10.1 变量名和语义来源有点错位

在 `MLPResNetBlock` 里：

- `task_k/task_v` 实际来自 `h_a + p`
- `adapter_k/adapter_v` 实际来自 `h_t`

所以不要按变量名理解，要按输入来源理解。

### 10.2 action query 不是标准“注册参数查询”

它更像：

- zero-init query slots
- 训练时叠加临时噪声

如果你按 DETR 那种 learnable queries 去理解，会和实现有偏差。

### 10.3 FiLM 不是当前关键路径

代码里有 FiLM，但当前实现里基本处于停用状态。

所以如果你要抓重点，不要把 FiLM 当成核心贡献。

---

## 11. 如果我要复现/改进这部分，我会优先做什么

### 方向 1：把 action query 改成真正可学习参数

当前实现里，query 起点是 0 张量，训练时只加临时噪声。

更自然的版本应该是：

- `self.action_queries = nn.Parameter(...)`
- 推理和训练都共享这组稳定参数
- 再额外叠加可控噪声

### 方向 2：把 gate 从单标量升级成向量或 head-wise gate

现在只有一个标量 `gating_factor`。

可以改成：

- per-head gate
- per-branch gate
- token-wise gate

这样能更细粒度控制任务条件注入强度。

### 方向 3：重新整理三路分支命名

纯工程角度，建议改名成：

- `self_attn`
- `state_attn`
- `task_attn`

这样论文和代码会更一致，也更方便后来人维护。

### 方向 4：研究 `h_t` 切分策略

现在是：

```python
task_hidden_states = actions_hidden_states[:, :, :self.num_task_tokens, :]
```

也就是固定切前 512 个 token。

这个设计很直接，但也比较硬。后面可以尝试：

- learned pooling
- language token mask
- instruction-only token extraction
- cross-layer fusion

---

## 12. 最后总结

VLA-Adapter 这套 action head 的核心思想，其实可以概括成一句很实用的话：

> 不要让小 VLM 直接去“说出动作”，而是让它提供高层 VL 表示，再用一个轻量 query-based policy 去主动读取任务、状态和动作上下文。

从代码上看，最值得你重点记住的是：

1. `action query` 在实现上是零初始化动作槽位，而不是显式类
2. bridge attention 本质是三路融合：self / 条件分支 / 任务分支
3. `gating_factor` 是桥接强度控制器
4. Pro 版通过独立 K/V 和 RoPE，把这个 head 做成了更成熟的小型多源解码器
5. 代码里存在一些“变量名和语义不完全一致”的地方，读时一定要按数据来源理解

如果你愿意，我下一步可以继续给你补一版：

- “按张量 shape 逐层展开”的版本
- 或者“把这套 bridge attention 画成结构图”的版本
- 或者“对比 OpenVLA/OpenVLA-OFT 的 action head 差异”的版本

---

## 参考链接

- GitHub 仓库：<https://github.com/OpenHelix-Team/VLA-Adapter>
- Action head 源码：<https://github.com/OpenHelix-Team/VLA-Adapter/blob/main/prismatic/models/action_heads.py>
- 推理工具：<https://github.com/OpenHelix-Team/VLA-Adapter/blob/main/experiments/robot/openvla_utils.py>
- LIBERO 评估入口：<https://github.com/OpenHelix-Team/VLA-Adapter/blob/main/experiments/robot/libero/run_libero_eval.py>
- OpenVLA wrapper：<https://github.com/OpenHelix-Team/VLA-Adapter/blob/main/prismatic/models/vlas/openvla.py>
- 辅助阅读镜像：<https://gitextract.com/OpenHelix-Team/VLA-Adapter>
