# Schema v1 设计草案

这份文档用于定义项目下一阶段的核心数据模型。目标不是一次性把所有字段定死，而是先稳定住三件事：

1. 系统里到底有哪些核心节点
2. 节点之间有哪些核心关系
3. 证据、状态、置信度应该挂在哪一层

这份 schema 将作为后续：

- `tree-sitter` 代码解析
- `Kuzu` 图构建与查询
- Graph RAG 检索
- 结构化记忆累积

的共同基础。

---

## 一、设计原则

### 1. 先稳定语义，再稳定存储

这一版 schema 先定义“系统里表达什么”，而不是先定义 “Kuzu 里具体建几张表”。

也就是说：

- 先定 node / edge 语义
- 再定 Kuzu 落地方式

### 2. 边比节点更重要

这个项目的核心价值在于关系，而不是对象列表。

例如真正重要的不是：

- 有一个 concept 节点
- 有一个 symbol 节点

而是：

- 这个 concept 是否被这个 symbol 实现
- 是直接实现还是结构支持
- 证据强度如何

因此，`status / confidence / reason / provenance` 应优先挂在边上。

### 3. 区分“概念本身”和“某次分析结论”

例如：

- `bridge_attention` 作为 concept，是一个相对稳定对象
- “在 VLA-Adapter 中，Figure 5 的 bridge attention 被哪些代码结构支持”
  则是一次具体分析结论

所以 schema 必须区分：

- 长期概念节点
- 具体 run 中产生的 alignment 结论

### 4. 不让 markdown 成为主存储

markdown 仍然保留，但它应该是展示层产物，不是核心知识载体。

核心知识载体应该是：

- 图节点
- 图边
- 结构化 evidence span

---

## 二、节点类型

建议先稳定以下节点类型。

## 1. `Paper`

表示一篇论文。

建议字段：

- `paper_id`
- `title`
- `source_path`
- `year`
- `authors`
- `venue`
- `paper_slug`
- `created_at`

## 2. `PaperSection`

表示论文中的章节或逻辑段。

建议字段：

- `section_id`
- `paper_id`
- `title`
- `order_index`
- `text_excerpt`

## 3. `PaperFigurePage`

表示关键图页或关键页渲染资产。

建议字段：

- `figure_page_id`
- `paper_id`
- `page_number`
- `image_path`
- `caption_excerpt`
- `render_status`

第一版先做到“页级图资产”，不强行要求自动裁图。

## 4. `PaperConcept`

表示论文侧的概念对象。

建议字段：

- `paper_concept_id`
- `paper_id`
- `name`
- `paper_status`
  - `paper_explicit`
  - `paper_implicit`
  - `user_defined`
- `summary`

说明：

- `PaperConcept` 是论文局部概念，不一定已经 canonicalize

## 5. `PaperClaim`

表示论文里的主张、方法断言或设计声明。

建议字段：

- `claim_id`
- `paper_id`
- `text`
- `claim_type`
  - `architecture`
  - `training`
  - `inference`
  - `performance`
- `support_excerpt`

## 6. `Repo`

表示一个代码仓库。

建议字段：

- `repo_id`
- `source`
- `local_path`
- `commit_hash`
- `framework`
- `language_set`

## 7. `File`

表示 repo 中的文件。

建议字段：

- `file_id`
- `repo_id`
- `path`
- `language`
- `file_role`
  - `train`
  - `config`
  - `architecture_entry`
  - `architecture_skeleton`
  - `architecture_component`
  - `deployment`
  - `docs`
  - `utils`

说明：

- `file_role` 可以保留多值或主值 + 次值
- 这会逐步替代当前 `RepoInfo` 中成批的 `*_candidates`

## 8. `Symbol`

表示 class / function / method / config symbol。

建议字段：

- `symbol_id`
- `file_id`
- `name`
- `kind`
  - `class`
  - `function`
  - `method`
  - `config_key`
- `line_start`
- `line_end`
- `signature_excerpt`

## 9. `CodeSpan`

表示局部证据片段。

建议字段：

- `span_id`
- `file_id`
- `symbol_id`
- `line_start`
- `line_end`
- `span_type`
  - `definition`
  - `usage`
  - `init_block`
  - `forward_path`
  - `loss_path`
  - `config_binding`
- `excerpt`

说明：

- `CodeSpan` 会成为 second-pass 的核心对象
- 后续应逐步弱化“整文件 excerpt 优先”的做法

## 10. `RuntimeEntry`

表示训练、推理、评估入口。

建议字段：

- `runtime_entry_id`
- `repo_id`
- `kind`
  - `train`
  - `eval`
  - `rollout`
  - `serve`
- `path`
- `entry_symbol`

## 11. `CanonicalConcept`

表示跨论文累积后的规范概念。

建议字段：

- `canonical_concept_id`
- `name`
- `category`
  - `architecture_pattern`
  - `training_strategy`
  - `inference_mechanism`
  - `bridge_module`
  - `action_generation`
- `summary`

说明：

- `PaperConcept` 是论文局部概念
- `CanonicalConcept` 是跨论文复用概念

## 12. `Constraint`

表示模块、概念或机制的约束条件。

建议字段：

- `constraint_id`
- `name`
- `constraint_type`
  - `input_shape`
  - `tokenization`
  - `training_signal`
  - `runtime_dependency`
  - `backbone_coupling`
- `summary`

---

## 三、边类型

这一部分是 schema 的重点。

## 1. 论文侧边

- `Paper -[HAS_SECTION]-> PaperSection`
- `Paper -[HAS_FIGURE_PAGE]-> PaperFigurePage`
- `Paper -[MENTIONS_CONCEPT]-> PaperConcept`
- `Paper -[MAKES_CLAIM]-> PaperClaim`
- `PaperFigurePage -[ILLUSTRATES]-> PaperConcept`
- `PaperClaim -[RELATES_TO]-> PaperConcept`

## 2. 代码侧边

- `Repo -[CONTAINS]-> File`
- `File -[DEFINES]-> Symbol`
- `File -[HAS_SPAN]-> CodeSpan`
- `File -[IMPORTS]-> File`
- `Symbol -[CALLS]-> Symbol`
- `Symbol -[INSTANTIATES]-> Symbol`
- `Symbol -[CONTAINS_SPAN]-> CodeSpan`
- `RuntimeEntry -[USES_FILE]-> File`
- `RuntimeEntry -[USES_SYMBOL]-> Symbol`

## 3. 对齐侧边

- `PaperConcept -[IMPLEMENTED_BY]-> Symbol`
- `PaperConcept -[SUPPORTED_BY]-> CodeSpan`
- `PaperConcept -[STRUCTURALLY_SUPPORTED_BY]-> Symbol`
- `PaperClaim -[SUPPORTED_BY]-> CodeSpan`
- `PaperConcept -[MISSING_EVIDENCE_FOR]-> Repo`
- `PaperConcept -[CONTRADICTED_BY]-> CodeSpan`

这一层是整个项目最关键的图关系层。

## 4. 记忆侧边

- `PaperConcept -[CANONICALIZED_AS]-> CanonicalConcept`
- `CanonicalConcept -[VARIANT_OF]-> CanonicalConcept`
- `CanonicalConcept -[WORKS_WITH]-> CanonicalConcept`
- `CanonicalConcept -[CONFLICTS_WITH]-> Constraint`
- `CanonicalConcept -[BORROWING_CANDIDATE_FOR]-> CanonicalConcept`
- `Symbol -[SATISFIES]-> Constraint`
- `Symbol -[VIOLATES]-> Constraint`

---

## 四、边上必须保留的属性

建议对 alignment / memory 相关边统一保留这些字段：

- `status`
  - `CONFIRMED`
  - `INFERRED`
  - `MISSING`
- `confidence`
  - `high`
  - `medium`
  - `low`
- `reason`
- `evidence_span_id`
- `source_run_id`
- `created_at`

原因：

1. 同一 concept 到同一 symbol 的关系，不同 run 可能强度不同
2. 后续做长期记忆时，必须能回溯来源
3. 只存“是否连边”远远不够

---

## 五、第一版建议回答的核心查询

schema 设计应该服务查询，而不是相反。

建议先保证能回答这些问题：

1. 某个论文概念在当前 repo 中有哪些直接实现或结构支持？
2. 某个论文 claim 被哪些代码片段支持？
3. 当前 repo 的 action generation 主路径是什么？
4. 某个 canonical concept 在哪些论文和 repo 中出现过？
5. 某个 concept 的 borrowing candidate 有哪些？它们带什么约束？
6. 某个 second-pass unresolved concept 还缺哪些类型的证据？

如果 schema 支撑不了这些问题，那就说明还不够好。

---

## 六、和当前代码的映射关系

这一版 schema 不是凭空来的，它大致对应当前已有对象的升级方向。

### 当前可直接映射

- `PaperInfo` -> `Paper`
- `PaperSection` -> `PaperSection`
- `CodeSymbol` -> `Symbol`
- `CodeHit` / `SecondPassCodeSpan` -> `CodeSpan`
- `Concept2CodeLink` -> 对齐边上的属性集合

### 当前需要逐步弱化或替代

- `RepoInfo` 里大量并列的 `*_candidates`
  - 后续应更多变成图中 `File` 节点属性 + 查询结果
- `CodeMapItem`
  - 更适合变成 alignment 查询结果，而不是长期主抽象
- 大量 markdown-first 中间组织结构
  - 后续应降级成展示层

---

## 七、落地建议

建议分三步推进：

### Step 1

先把这版 schema 写成 Python 侧统一 dataclass / typed model。

### Step 2

定义 `GraphStore` 抽象接口：

- `upsert_paper(...)`
- `upsert_repo(...)`
- `upsert_symbol(...)`
- `upsert_span(...)`
- `link_alignment(...)`
- `link_memory(...)`
- `query_local_subgraph(...)`

### Step 3

再决定 Kuzu 的具体建模与落表方式。

---

## 八、一句话总结

这一版 schema 的核心思想是：

```text
把“论文对象”“代码对象”“对齐结论”“长期记忆”明确拆开，
并把状态、证据、置信度挂在关系上，
为 Kuzu + Graph RAG + 长期结构化积累提供稳定基础。
```

---

## 九、代码级接口草案

为了避免 schema 只停留在文档层，这里给出建议的代码接口边界。

### 1. `graph_models.py`

建议最小对象：

- `GraphNodeRef`
- `GraphNode`
- `GraphEdge`
- `GraphSubgraph`
- `GraphQueryResult`

设计意图：

- `GraphNodeRef` 作为统一节点引用
- `GraphEdge` 承载 `status / confidence / reason / provenance`
- `GraphSubgraph` 作为 Graph RAG 的最小检索单元

### 2. `graph_store.py`

建议先暴露一个统一 `GraphStore` 抽象：

- `upsert_node(node)`
- `upsert_edge(edge)`
- `get_node(ref)`
- `get_outgoing_edges(ref, edge_types=None)`
- `get_incoming_edges(ref, edge_types=None)`
- `query_local_subgraph(seeds, max_hops=2, edge_types=None)`

说明：

- 当前可先有内存实现用于原型和测试
- 目标后端应是 `Kuzu`
- 业务层不应直接依赖具体图库 API

### 3. `graph_query.py`

建议把系统级查询从存储层再抽一层：

- `local_subgraph_for_node(...)`
- `alignment_edges_for_concept(...)`

后续可以继续扩展：

- `action_generation_path_for_repo(...)`
- `borrowing_candidates_for_concept(...)`
- `supporting_spans_for_claim(...)`

### 4. `code_parser.py`

建议定义统一 `CodeParser` 抽象：

- `supports_language(language)`
- `parse_file(path, text)`

解析结果建议统一成：

- `ParsedCodeFile`
- `ParsedSymbol`
- `ParsedImport`
- `ParsedRelation`

当前可以保留一个 Python `ast` 兼容实现，但它只应作为过渡适配层；主路线应迁到 `tree-sitter`。

### 5. 业务层依赖关系

建议的调用关系是：

```text
Paper / Repo ingestion
-> CodeParser
-> GraphStore
-> GraphQueryService
-> AlignmentService
-> Codex reasoning
```

明确不建议：

- 业务直接调用 `Kuzu`
- 业务直接使用 `tree-sitter` 返回对象
- 业务直接操作大而全的 `RepoInfo` 聚合对象作为长期主抽象
