# 论文概念到代码结构映射

这份文档讨论一个在 `Concept2Code tracing` 中非常关键、也很容易被误判的问题：

- 论文里明确提出了一个模块或概念
- 代码仓库里却没有出现同名类、同名函数或同名文件
- 但代码实际上很可能已经以“结构性实现”的方式落地了这个概念

`VLA-Adapter` 中的 `bridge_attention` 就是一个典型例子。

---

## 1. 问题定义

当前系统在做 `Concept2Code tracing` 时，已经能处理两类情况：

1. 论文概念和代码命名接近  
   例如论文说 `projector`，代码里就有 `projectors.py`、`ProprioProjector`、`NoisyActionProjector`

2. 论文概念没有完全同名，但代码中有明显近义 symbol  
   例如论文说 `policy`，代码里有 `predict_action`、`Policy`、`sample_actions`

但还有第三类情况：

3. 论文概念在论文里是显式提出的结构模块  
   代码中却没有任何同名 symbol  
   只能通过多个局部结构共同推断它的实现

`bridge_attention` 就属于第三类。

如果仍然用“关键词是否命中代码”来判断，这类概念的质量会长期偏低，容易出现两种问题：

- 过弱：因为代码里没有这个词，所以永远只会得到非常模糊的 `INFERRED`
- 过强：因为看到了一些 `bridge` 或 `attention` 词，就误把不完整证据抬成 `CONFIRMED`

所以后续必须从“词匹配”升级到“结构判据匹配”。

---

## 2. 核心原则

后续对这类概念的处理，建议分成两层：

### 2.1 论文层

先承认一个事实：

- 某个概念在论文里是显式提出的
- 它有作者给出的定义、图示、信息流和功能角色

这一层不需要代码证明。

例如对 `bridge_attention`，论文层可以明确说：

- 它是论文 Figure 5 中明确命名的模块
- 它位于 `VLM -> Policy` 的桥接位置
- 其目标是让 action query 主动读取来自 VLM / condition 的信息

### 2.2 代码层

代码层不再问：

```text
代码里有没有 "bridge_attention" 这个词？
```

而改成问：

```text
代码里是否存在一组结构特征，共同实现了论文中 bridge_attention 的功能？
```

也就是说，代码层要判断的是“结构性对应”，不是“字面同名”。

---

## 3. 从论文概念到结构判据

对于这类概念，系统后续应该先把论文概念翻译成一组“结构判据模板”。

### 3.1 以 `bridge_attention` 为例

根据 Figure 5，`bridge_attention` 不是一个单纯的 Attention 层名，而是一组结构关系：

1. 存在一条 `policy` 分支
2. 存在 `action query` 或 action latent
3. 存在来自 `VLM / condition` 的 `KV`
4. 存在 `cross-attention`
5. 存在 `self-attention`
6. 存在 `concat / fusion / ratio / gating` 等融合逻辑
7. 这种结构通常不是一次性调用，而是逐层或重复地插入 policy block

因此，后续系统在代码里要找的不是：

- `bridge_attention` 这个词

而是这些结构角色：

- `query-like`
- `condition-kv-like`
- `cross-attention-like`
- `self-attention-like`
- `fusion-like`
- `repeated-block-like`

### 3.2 这类判据的泛化价值

这套方法不是只服务 `VLA-Adapter`。

类似地，后面还可以用在：

- `reasoning_tokens`
- `action_head`
- `visual-language bridge`
- `latent planner`
- `world model rollout`

这些概念在不同论文中经常是“论文名词统一，但代码命名不统一”。

---

## 4. second-pass 应该如何改

当前 second-pass 已经从“文件前缀 excerpt”升级到了“symbol-aware / concept-aware 片段抽取”。  
下一步还可以继续提升为“**结构问句驱动的片段抽取**”。

### 4.1 当前做法

当前更接近：

```text
focus concept
-> 在关键文件里抽和 concept/role/symbol 更相关的高分片段
-> Codex 基于这些片段推断结论
```

这已经比以前明显更好，但对 `bridge_attention` 这种概念仍然不够。

### 4.2 下一步做法

如果 focus 是 `bridge_attention`，本地 second-pass 不应该只找：

- `bridge`
- `attention`

而应该转成一组结构问句：

1. action query 在哪里定义？
2. condition / VLM 输出在哪里变成 `KV`？
3. cross-attention 在哪里发生？
4. self-attention 在哪里发生？
5. concat / fusion / ratio / gating 在哪里实现？
6. 这种结构是单点出现，还是逐层插入？

然后 second-pass 抽片段时优先补：

- 定义片段
- 使用片段
- 连接片段

而不是只补一个大文件。

---

## 5. 建议的输出口径

对于这类概念，后续输出最好不要只给一个简单的：

- `CONFIRMED`
- `INFERRED`

而应该在解释层明确分开“论文显式”和“代码落地”。

推荐的口径是：

### 5.1 论文层状态

- `EXPLICIT`
- `IMPLICIT`

### 5.2 代码层状态

- `DIRECTLY_CONFIRMED`
- `STRUCTURALLY_INFERRED`
- `WEAKLY_SUPPORTED`
- `MISSING`

例如 `VLA-Adapter` 的 `bridge_attention` 更合理的描述不是：

```text
INFERRED
```

而是：

```text
Paper side: EXPLICIT
Code side: STRUCTURALLY_INFERRED
```

这样信息量更高，也更符合研究实际。

---

## 6. 对 VLA-Adapter 的具体启发

如果后续再次分析 `VLA-Adapter`，并且 focus 中包含 `bridge_attention`，系统应该优先寻找：

1. policy/action query 的来源
2. VLM 输出如何变成可供 policy 读取的 condition features
3. 哪些模块在做 cross-attention
4. 哪些模块在做 self-attention
5. 融合逻辑是 concat、ratio，还是 gate
6. 这些结构是在单层出现，还是在多层重复出现

只有把这些结构证据拼起来，系统才能给出高质量结论：

- 论文里 `bridge_attention` 是显式概念
- 代码中未见同名模块
- 但从多个结构片段可以推断其实现已经隐式存在

这比“代码里没这个词，所以只能低置信 inferred”要强得多。

---

## 7. 对 P2.1 的建议

后续如果进入下一轮 second-pass 提升，建议明确增加这一项：

### P2.1: 论文显式概念的结构化判据追踪

目标：

- 对 `bridge_attention` 这类论文显式概念
- 不再只做词匹配
- 而是做“论文概念 -> 结构判据 -> 代码局部证据”的映射

优先实现内容：

1. 为部分高价值概念建立结构判据模板
2. second-pass 支持“结构问句驱动”的补片段
3. 输出层区分：
   - 论文显式性
   - 代码结构落地程度

第一批最值得支持的概念：

- `bridge_attention`
- `action_head`
- `reasoning_tokens`
- `visual-language bridge`

---

## 8. 当前结论

一句话总结：

**当论文里的概念是显式提出、但代码里没有同名 symbol 时，后续系统的提升方向不应该是“换更强的关键词”，而应该是“把论文概念翻译成结构判据，再去代码里找实现痕迹”。**

这会比继续加词表更稳，也更有泛化性。*** End Patch
---

## 补充：这个方向不应走成“概念模板库”

需要特别说明的是：

这里说的“结构判据”不是要把系统做成一个不断膨胀的全局 concept template 库。

如果后续路线变成：

- 给每篇论文都加几个新的 concept template
- 给每个 repo 都补一些专用匹配词

那很快就会失去泛化性。

更合理的实现方向应该是：

- 只保留少量通用的结构角色框架
  - query-like
  - kv-like
  - cross-attention-like
  - self-attention-like
  - fusion/gating-like
  - output-head-like
- 对于每篇论文，先由 paper-side understanding 生成这篇论文自己的“结构假设”
- 再让 second-pass 去代码里寻找这些结构角色的落点

也就是说：

```text
不是预制所有 concept template
而是每篇论文临时生成自己的结构分析任务
```

这样泛化性会比不断堆模板强很多。

---

## 补充：为什么需要 paper-side understanding

像 `bridge_attention` 这样的概念，真正的问题不是“代码里没这个词”，而是：

- 它在论文里是显式概念
- 它的实现线索往往更多藏在图和图注里
- 如果只靠 repo 端证据，很容易永远只能得到低质量 `INFERRED`

所以后续应该先增加一个轻量 `paper understanding pass`，先回答：

1. 这个概念在论文里是显式还是隐式？
2. 它在论文里承担什么结构角色？
3. 论文图示里有哪些关键模块和信息流？
4. 哪些地方最值得去代码里核验？

这样 second-pass 的问题就会从：

```text
代码里哪里有这个词？
```

升级成：

```text
论文里这个模块承担什么角色？
代码里哪些结构片段共同实现了这个角色？
```

---

## 补充：论文读取需要“双通道”

为了支撑这一点，论文读取后续不能只依赖 `pypdf`。

更合理的是双通道：

### 文本层

用于抽取：

- 标题
- 摘要
- 方法段落
- figure caption
- 概念定义句

这层 `pypdf` 仍然有价值。

### 图示层

用于理解：

- 模块框
- 箭头链路
- 分组
- 重复层结构
- query / kv / output 的位置关系

这层需要对关键页或图块截图，再做视觉理解。

OCR 只作为补充：

- 补图中的小字 label
- 提取 caption 里没覆盖的模块名
- 帮助对齐图中文字与结构说明

也就是说，后续应优先：

- 先截图
- 先理解图结构
- 必要时再补 OCR

而不是一上来就把图当成 OCR 问题处理。
