# Graph RAG 总体架构设想

这份文档用于收敛项目下一阶段的总体技术路线。它不讨论某一个局部功能怎么修，而是回答四个更大的问题：

1. 项目下一阶段的核心系统边界是什么
2. 除了 Graph RAG 之外，还需要哪些模块层
3. 推荐采用什么工具组合
4. 应该如何分阶段落地，避免前期做得太重、后期又难迁移

---

## 一、先给结论

项目下一阶段不应再被定义为“论文读码工具增强版”，而应被定义为：

```text
面向 VLA 研究的论文-代码-概念对齐系统
```

Graph RAG 会是核心骨架，但它本身还不够。更完整的系统至少需要四层图：

1. `Paper Graph`
2. `Code Graph`
3. `Alignment Graph`
4. `Memory Graph`

其中：

- `Paper Graph` 负责表达“论文自己在说什么”
- `Code Graph` 负责表达“代码实际上是什么结构”
- `Alignment Graph` 负责表达“论文概念如何在代码中落地”
- `Memory Graph` 负责表达“跨论文、跨 repo 之后，哪些概念和模块可以积累与复用”

项目当前已经具备一部分前置能力：

- 第一遍 repo evidence 构建
- role-aware + AST rerank
- second-pass reading
- paper workspace 与轻量 paper understanding

下一阶段的重点不再是继续堆 prompt 或局部排序规则，而是把这些能力组织成一个可持续扩展的图式系统。

---

## 二、为什么不只做 Graph RAG

如果只说“做 Graph RAG”，很容易停留在：

- 把节点和边建出来
- 检索一个局部子图
- 再交给模型解释

这对于问答型场景很有用，但对本项目的目标仍然偏窄。因为你的目标不是单次问答，而是：

- 先理解论文提出了什么
- 再验证代码是否真的这样实现
- 再把这些结论积累成可复用知识
- 最终支持你做自己的 VLA 架构设计判断

因此，Graph RAG 在这个项目里应该被理解为：

```text
图式知识组织与检索骨架
```

而不是系统的全部。

还必须补上的，是：

- 概念规范化层
- 约束与兼容性层
- 证据溯源层
- 用户意图层

这些层决定系统是否只是“会说”，还是“能积累、能复用、能支持设计判断”。

---

## 三、核心模块

### 1. Paper Workspace

职责：

- 为每篇论文创建稳定目录
- 保存 PDF、抽取文本、关键图页 PNG、论文理解结果、输出结果

当前方向已经基本确定：

```text
result/<paper_slug>/
  source/
  extracted/
  notes/
  outputs/
```

这一层是后续所有论文侧复用的基础。

### 2. Paper Understanding Engine

职责：

- 读论文文本与关键图页
- 形成 paper-side summary
- 提取：
  - 核心 claim
  - 显式 concept
  - 隐式结构假设
  - 待验证问题

这一层的输出不是最终答案，而是驱动后续代码验证的问题集合。

### 3. Code Understanding Engine

职责：

- 建立 file / class / function / span 层级结构
- 建立 AST / symbol / config / train / infer 关系
- 识别 architecture role
- 提供局部代码证据与结构关系

它是当前第一遍 evidence 和 second-pass 的自然升级版本。

### 4. Alignment Builder

职责：

- 把 paper concept 与 code symbol / span 对齐
- 区分：
  - 直接实现
  - 结构支持
  - 缺失证据
  - 相互矛盾

这层是整个系统的核心，因为它把“论文理解”和“代码理解”连接起来。

### 5. Graph Retrieval Layer

职责：

- 从多层图中检索局部相关子图
- 为模型准备高密度证据包

这一层后续应该代替“把大量文本直接塞进 prompt”的做法。

### 6. Codex Reasoning Layer

职责：

- 解释局部子图
- 合并 paper-side 与 code-side 证据
- 生成结构化结论，而不是只生成自然语言段落

模型在这里更像解释器和归纳器，而不是唯一真相源。

### 7. Structured Evidence Store

职责：

- 保存 confirmed / inferred / missing 结论
- 保存 evidence span、confidence、reason、来源
- 为 memory consolidation 提供输入

这层必须支持长期复用，而不只是 session 临时输出。

### 8. Memory / Design Space Layer

职责：

- 跨论文累积 canonical concept
- 保存模块变体与兼容性信息
- 支持 borrowing candidate 与设计空间导航

这是项目从“分析工具”走向“研究副驾”的关键层。

---

## 四、数据流

建议的主数据流如下：

```text
用户意图
-> Paper Workspace
-> Paper Understanding
-> Paper Graph
-> Code Understanding
-> Code Graph
-> Alignment Builder
-> Alignment Graph
-> Graph Retrieval
-> Codex Reasoning
-> Structured Evidence
-> Memory Graph
-> 研究笔记 / 借鉴建议 / 设计判断
```

更细一点可以拆成：

### 阶段 1：论文侧

1. 输入 PDF
2. 建立 `result/<paper_slug>/`
3. 提取文本
4. 渲染关键图页
5. 形成 paper understanding
6. 写入 `Paper Graph`

### 阶段 2：代码侧

1. 扫描 repo
2. 建 AST / symbol / span 结构
3. 建 config / train / infer 关系
4. 形成 `Code Graph`

### 阶段 3：对齐侧

1. 将 paper concept 转成待验证问题
2. 到 `Code Graph` 中找支持路径
3. 形成 `Alignment Graph`
4. 再用局部子图和关键 span 触发 Codex 解释

### 阶段 4：积累侧

1. 把 confirmed / inferred / missing 结构化落盘
2. 规范化 concept
3. 建立跨论文 memory links

---

## 五、推荐工具与选型建议

### 1. 论文解析

#### 当前建议

- 文本层：
  - `pypdf`
- 图示层：
  - PDF 页渲染成 PNG

#### 中期建议

- 文本层增强：
  - `PyMuPDF`
- 更强论文结构化：
  - `GROBID`（如果后续对论文结构化需求明显上升）

#### 当前明确不做

- OCR 前置
- 自动精确裁图前置

理由：

- 当前更需要“稳定页级图示资产”
- 不是先解决小字识别问题

### 2. 代码解析

#### 当前建议

- Python：
  - 标准库 `ast`

#### 中期建议

- 多语言支持：
  - `tree-sitter`

#### 原则

- 不让上层业务直接依赖具体解析库
- 抽象成统一的 code node / edge / span 生产接口

### 3. 图构建与查询

这是当前最关键的技术路线选择之一。

你已经明确后续会做：

- 跨论文累积
- 大量局部子图查询
- 持久化图分析
- 图关系驱动 retrieval

在这种前提下，我的建议是：

#### 不推荐长期停留在纯 `networkx`

`networkx` 适合：

- 早期 schema 验证
- 小规模原型
- 本地图结构调试

但对于你接下来明确会做的四类需求，它不是终局方案。

#### 推荐尽早前置图数据库思维

优先建议两条路线：

1. `Kuzu`
2. `Neo4j`

其中我更推荐：

### 首选：`Kuzu`

理由：

- 嵌入式，适合本地研究项目
- 比 `Neo4j` 更轻
- 比 `networkx` 更接近最终图查询形态
- 更适合作为“可持续原型”而不是一次性实验

### 备选：`Neo4j`

适合：

- 你后面需要更成熟的图生态
- 更重的图查询与可视化
- 更明显的多人协作场景

但对当前单机研究工具来说，接入与运维心智更重。

#### 建议原则

无论选哪一个，都要做到：

- 业务层只依赖 `GraphStore / GraphQueryService`
- 不把某个具体图库的 API 写死到系统各处

### 4. 向量检索

Graph RAG 不应只靠图关系，也应该保留 embedding 检索层。

推荐：

- 前期：
  - `LanceDB` 或 `FAISS`
- 存储对象：
  - concept description
  - code span
  - claim / caption
  - figure summary

建议和图层分开：

- graph store 管结构
- vector store 管语义近邻

### 5. 结构化存储

推荐分三层：

1. `artifact store`
   - markdown
   - json
   - png
2. `graph store`
   - paper/code/alignment/memory nodes and edges
3. `vector store`
   - concept / span embeddings

不要把三层混成一层。

---

## 六、必须先定义清楚的数据模型

在具体工具之前，更重要的是先稳定 schema。

至少建议先定义这些对象：

### 1. PaperNode

例如：

- paper
- section
- figure
- concept
- claim

### 2. CodeNode

例如：

- repo
- file
- class
- function
- method
- span
- config key

### 3. AlignmentEdge

至少要支持：

- `implemented_by`
- `supported_by`
- `consistent_with`
- `missing_evidence_for`
- `contradicted_by`

### 4. MemoryRecord

至少要带：

- canonical concept
- paper term
- repo symbol
- status
- evidence
- confidence
- source paper
- source repo
- constraints

如果这些 schema 不稳定，那么不管你用 `networkx` 还是 `Kuzu`，后面迁移都会痛。

---

## 七、推荐的分阶段落地路线

### Phase A：图式 schema 与抽象层先落地

目标：

- 定义 node / edge schema
- 定义 `GraphStore` 抽象接口
- 定义 `GraphQueryService` 抽象接口

建议：

- 这一阶段就开始按图数据库思维设计
- 即使暂时还没全面切入，也不要让业务直接绑死 `networkx`

### Phase B：Paper Graph + Code Graph 落地

目标：

- 把当前 paper workspace / paper understanding 接到 `Paper Graph`
- 把当前 first-pass / second-pass / AST evidence 接到 `Code Graph`

产出：

- 基础图构建能力
- 可持久化节点和边

### Phase C：Alignment Graph 落地

目标：

- 把 concept2code 从 JSON 提升为图关系
- 支持 confirmed / inferred / missing 三类边
- 支持局部子图解释

这是 Graph RAG 真正开始有价值的阶段。

### Phase D：Graph Retrieval + Hybrid Retrieval

目标：

- 局部子图检索
- span 检索
- vector + graph 混合检索

这一步开始替代“把大量 evidence 硬塞给 Codex”的做法。

### Phase E：Memory Graph 与设计空间支持

目标：

- 跨论文概念规范化
- 保存约束与兼容性
- 支持 borrowing candidate
- 支持设计空间导航

这一步之后，项目才真正接近“研究副驾”。

---

## 八、当前技术路线建议

结合你已经明确的目标，我给出的推荐路线是：

```text
不是“先 networkx，后面再说”，
而是“从第一天就按图数据库抽象设计，并尽早考虑以 Kuzu 为目标形态”。
```

更具体一点：

1. 现在先做统一 schema 和抽象接口
2. 允许早期局部实现仍用轻量内存图做原型验证
3. 但中期尽早切到 `Kuzu` 这类可持久化、可查询的图后端
4. 向量检索层与图层分开设计

这样做的好处是：

- 不会一开始就背上很重运维负担
- 也不会把系统写成只适合一次性原型的形态
- 和你明确的长期目标是同方向的

---

## 九、当前不建议做的事

1. 不建议先做全自动架构生成
2. 不建议先做巨大的 concept template 库
3. 不建议把 Graph RAG 理解成“把所有 chunk 接成图”
4. 不建议把图、向量、session、artifact 混在一个存储里
5. 不建议让业务代码直接依赖某个底层图库 API

---

## 十、一句话总结

如果把项目下一阶段的核心方向说得最简洁一些，我会这样概括：

```text
以 Paper Graph + Code Graph + Alignment Graph + Memory Graph 为核心，
用 Graph RAG 组织局部证据检索与模型推理，
最终把项目从“论文读码工具”推进到“可积累、可复用、可支持 VLA 架构设计判断的研究系统”。
```
