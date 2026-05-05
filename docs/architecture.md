# Architecture

## 产品心智

当前项目是一个 **code-first VLA research copilot**，默认围绕 repo 问答展开：

```text
repo -> workspace index -> code graph -> ask -> answer/session -> card -> export note
```

论文是可附加知识层：

```text
paper -> attach to workspace -> claims / concepts / rationales
```

它主要服务两类问题：

- 代码实现问题
- 设计动机 / paper-code alignment 问题

## 当前主模块

### CLI

- `index`
- `paper attach`
- `ask`
- `card build`
- `export note`
- `analyze` 仅作兼容 wrapper

### Workspace

- `workspace_store.py`
- `workspace_models.py`

职责：

- 管理 workspace manifest
- 管理 papers / sessions / cards / graph artifacts

### Parsing / Indexing

- `repo/ingest.py`
- `parser_backend.py`
- `repo/code_parser.py`

职责：

- 准备 repo
- 按统一 backend 接口解析文件
- 生成最小可用 graph artifact

### QA / Copilot

- `copilot.py`
- `qa_models.py`
- `card_models.py`

职责：

- 问题分类
- 证据检索
- 结构化回答
- 卡片生成

### Paper Attachment

- `paper/pdf.py`
- `paper/understanding.py`
- `paper/workspace.py`

职责：

- 读取 PDF / Markdown 论文
- 提取 claim、concept、design rationale
- 为 repo 问答提供附加解释层

## Graph Artifact

当前 graph 使用本地 `jsonl` artifact：

- `graph_nodes.jsonl`
- `graph_edges.jsonl`

最小节点类型：

- `File`
- `Class`
- `Function`
- `Config`
- `Concept`
- `PaperClaim`
- `EvidenceSpan`

最小边类型：

- `defines`
- `imports`
- `calls`
- `instantiates`
- `configured_by`
- `mentioned_in_paper`
- `supports_claim`

## 回答约束

### Implementation

必须优先返回：

- 文件
- 符号
- 局部代码证据

### Rationale

必须拆成两部分：

- 代码中能直接证明的事实
- 论文或附加材料支持的设计动机

如果没有 paper evidence，必须明确标成 code-only inference。
