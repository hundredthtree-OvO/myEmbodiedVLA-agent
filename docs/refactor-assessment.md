# 现有代码重构评估

这份文档用于回答一个现实问题：

```text
如果项目下一阶段转向 tree-sitter + Kuzu + Graph RAG，
当前代码哪些应该保留，哪些应该重写，哪些应该准备退役？
```

目标不是“全盘否定现有工作”，而是避免把原型阶段的局部抽象继续无限叠加，最后变成难以迁移的系统。

---

## 一、评估原则

### 1. 保留基础设施，不保留阶段性抽象

如果某段代码解决的是：

- 路径管理
- session 落盘
- 配置读取
- 环境兼容

那通常值得保留。

如果某段代码解决的是：

- 当前版本的候选层组织方式
- 当前 prompt 时代的中间结构
- 当前 second-pass 的文件级补读形态

那就要谨慎，很多会在图系统里失去主导地位。

### 2. 不为了“兼容旧字段”无限背历史包袱

当前很多字段保留是为了兼容旧逻辑和早期输出形态。  
进入下一阶段后，需要接受一个现实：

- 有些东西应该被正式降级
- 有些东西应该被迁移而不是继续长期共存

### 3. 以“是否适合图系统”为标准评估

判断某段代码是否该保留时，我建议问：

1. 它是否能自然映射到 `Paper Graph / Code Graph / Alignment Graph / Memory Graph`
2. 它是否能被 `tree-sitter + Kuzu` 时代继续使用
3. 它是否只是 markdown/prompt 时代的临时组织方式

---

## 二、建议保留的模块

这些模块主要属于基础设施层，建议保留并做适配。

## 1. `paper_workspace.py`

建议：

- 保留
- 继续作为论文侧资产根目录管理器

原因：

- `result/<paper_slug>/...` 的方向是对的
- 后续图资产、图页、理解结果、输出结果都还需要这个目录层

## 2. `session_store.py`

建议：

- 保留
- 但逐步从“主知识载体”降级为“run artifact 管理器”

原因：

- session 仍然对调试、追溯和离线回看有价值
- 但长期记忆应逐步迁入图与结构化 evidence

## 3. `config.py`

建议：

- 保留
- 后续增加 graph/backend/parser 等配置项

原因：

- 当前环境路径、auth、Zotero、second-pass 开关都已经沉淀在这里
- 配置入口没有必要重来

## 4. `codex_client.py`

建议：

- 保留
- 作为模型调用适配层继续使用

原因：

- 后面不管 prompt 如何变化，调用接口层仍然需要

## 5. `cleanup.py`

建议：

- 保留

原因：

- `.tmp`、缓存、测试产物清理逻辑仍然有价值
- 和图系统主抽象没有冲突

---

## 三、建议保留文件名，但重写内部的模块

这些模块建议继续存在，但不适合原样延续当前内部逻辑。

## 1. `pipeline.py`

建议：

- 保留入口文件名
- 重写为更清晰的 orchestrator

原因：

- 当前 `execute_analysis()` 仍然是“原型阶段总线”
- 后续应拆成：
  - paper workspace
  - paper understanding
  - code graph build
  - alignment build
  - graph retrieval
  - codex reasoning
  - memory consolidation

结论：

- 文件可保留
- 流程必须重构

## 2. `paper_understanding.py`

建议：

- 保留模块名
- 重写其核心逻辑

原因：

- 当前还是 `focus_terms` 驱动
- `ROLE_HINTS / ROLE_QUESTIONS` 更像临时启发式
- 后续应转向：
  - claim extraction
  - concept extraction
  - figure-aware understanding
  - paper-side question generation

## 3. `pdf.py`

建议：

- 保留模块名
- 重构 PDF 文本层与图页层接口

原因：

- 当前全文抽取和逐页抽取后端不一致
- 这是“有文本、没图页”的直接原因之一
- 后续需要统一抽象成：
  - `extract_text`
  - `extract_page_texts`
  - `render_pages`

## 4. `second_pass.py`

建议：

- 保留模块名
- 重构 second-pass 对象

原因：

- 当前 second-pass 已经有价值
- 但它还是围绕：
  - 文件
  - excerpt
  - span 列表
 组织
- 后续更适合转成：
  - 子图
  - symbol chain
  - span evidence bundle

## 5. `prompt_builder.py`

建议：

- 保留模块名
- 大幅重构内部输入对象

原因：

- 当前还是 evidence pack / markdown 时代的组织方式
- 后续 prompt 应更多面向：
  - graph summary
  - local subgraph
  - structured evidence bundle

## 6. `models.py`

建议：

- 保留文件
- 但拆分模型层级

原因：

- 当前把：
  - request model
  - paper model
  - repo model
  - second-pass model
  - artifact model
 统统放在一个文件里
- 后续图系统下会越来越臃肿

建议后续拆成：

- `request_models.py`
- `paper_models.py`
- `code_models.py`
- `graph_models.py`
- `artifact_models.py`

---

## 四、建议逐步退役或明显降级的部分

这些不是“现在立刻删文件”，而是应该在下一阶段开始后，有计划地退出核心路径。

## 1. `RepoInfo` 的大而全候选字段集合

当前 `RepoInfo` 同时保留了：

- 类型候选层
- 角色候选层
- AST debug
- symbol/hit 列表
- path 列表

问题：

- 它是一个典型的“原型阶段聚合对象”
- 在图系统下，它会越来越像历史包袱

建议：

- 逐步把 `RepoInfo` 从主知识对象降级为：
  - 一次扫描的中间结果
  - 或兼容层

## 2. 当前大量 `*_candidates` 并列字段

例如：

- `train_candidates`
- `config_candidates`
- `architecture_entry_candidates`
- `architecture_skeleton_candidates`
- `architecture_component_candidates`

问题：

- 它们适合当前排序系统
- 但不适合长期作为主存储接口

建议：

- 图系统上线后，将它们更多转成：
  - `File.file_role`
  - 图查询结果
  - 调试输出

## 3. `CodeMapItem`

问题：

- 它是 markdown 汇总时代很自然的结构
- 但对长期知识积累来说太粗

建议：

- 降级为最终展示层中间结构
- 不再作为主抽象继续扩展

## 4. 当前 `paper_understanding` 的 token-hint 驱动方式

问题：

- `ROLE_HINTS`
- `ROLE_QUESTIONS`
- `focus_terms -> paper_status`

这些都适合作为轻启发式，但不适合继续当主干。

建议：

- 后续只保留为 fallback
- 主路径迁到更结构化的 paper graph 生成逻辑

## 5. second-pass 的“按文件补读”主思路

问题：

- 当前已经比以前强
- 但还是残留“补文件”思路

建议：

- 逐步切到“补子图 / 补 symbol chain / 补 span bundle”

---

## 五、建议新增的核心抽象层

如果要系统性转向新架构，建议尽早新增这些抽象，而不是继续堆函数。

## 1. `GraphStore`

职责：

- 抽象底层 Kuzu 读写

业务层不应直接依赖 Kuzu 查询语法。

## 2. `GraphQueryService`

职责：

- 提供系统级查询接口

例如：

- 查询某个 concept 的局部支持子图
- 查询某个 repo 的 action generation path
- 查询某个 canonical concept 的所有案例

## 3. `CodeParser`

职责：

- 抽象 `tree-sitter` 解析结果

避免业务直接绑死具体 parser API。

## 4. `AlignmentService`

职责：

- 统一生成 paper-code 对齐关系

这会比把 alignment 逻辑散落在 second-pass、prompt 和 markdown 里更稳。

## 5. `MemoryService`

职责：

- 负责 canonicalization
- 负责跨论文累积
- 负责 borrowing candidate 组织

---

## 六、建议的重构顺序

### 第一步

先定 schema v1 与抽象接口：

- `GraphStore`
- `GraphQueryService`
- `CodeParser`

### 第二步

先把论文侧和代码侧各自接入图：

- `Paper Graph`
- `Code Graph`

### 第三步

再迁移当前 second-pass 与 concept2code：

- 从 JSON-first
- 迁到 alignment graph first

### 第四步

最后清退旧的候选字段中心化路径：

- `RepoInfo` 降级
- `CodeMapItem` 降级
- prompt-first 中间对象降级

---

## 七、一句话总结

这次重构不该是“继续在原型上补洞”，而应该是：

```text
保留基础设施，
替换核心抽象，
清退原型遗留，
把项目重心从 markdown-first 流程迁移到 graph-first 流程。
```
