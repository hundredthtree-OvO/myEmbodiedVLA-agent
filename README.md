# my-embodied

`study-agent` 现在定位为一个 **code-first 的 VLA research copilot**。

它不再以“输入 paper + repo + focus，生成一篇长 Markdown”作为主产品心智，而是以 **workspace + repo 问答 + 卡片资产** 为核心：

1. 导入并索引 repo
2. 可选绑定论文
3. 围绕代码库提问
4. 将高价值回答沉淀为卡片和研究笔记

## 当前主命令

```powershell
uv run python study_agent_cli.py index --repo <repo_path_or_url> --workspace <name>
uv run python study_agent_cli.py paper attach --workspace <name> --paper <paper.pdf|paper.md>
uv run python study_agent_cli.py ask --workspace <name> --question "How is Implicit Action Reasoner implemented?"
uv run python study_agent_cli.py card build --workspace <name> --topic "Implicit Action Reasoner"
uv run python study_agent_cli.py export note --workspace <name> --out notes\my-note.md
```

## 快速开始

推荐先在 PowerShell 中设置：

```powershell
$env:UV_CACHE_DIR='.tmp\uv-cache'
$env:PYTHONPATH='src'
```

安装依赖：

```powershell
uv sync
```

索引一个本地 repo：

```powershell
uv run python study_agent_cli.py index --repo E:\path\to\repo --workspace acot-vla
```

绑定论文：

```powershell
uv run python study_agent_cli.py paper attach --workspace acot-vla --paper E:\path\to\paper.pdf
```

提问：

```powershell
uv run python study_agent_cli.py ask --workspace acot-vla --question "Explain the implementation of Implicit Action Reasoner."
uv run python study_agent_cli.py ask --workspace acot-vla --question "Why is the Implicit Action Reasoner designed this way?"
```

生成卡片和导出笔记：

```powershell
uv run python study_agent_cli.py card build --workspace acot-vla --topic "Implicit Action Reasoner"
uv run python study_agent_cli.py export note --workspace acot-vla --out notes\acot-vla-note.md
```

## 工作区产物

每个 workspace 会落盘到：

```text
.study-agent/workspaces/<workspace_id>/
  manifest.json
  repo_index.json
  graph_nodes.jsonl
  graph_edges.jsonl
  papers/
  sessions/
  cards/
```

其中：

- `graph_nodes.jsonl` / `graph_edges.jsonl` 是本地 code graph artifact
- `papers/` 保存附加论文及其理解产物
- `sessions/` 保存单问单答结果
- `cards/` 保存可复用卡片

## 兼容说明

`analyze` 还保留为一个 **deprecated wrapper**，它现在只是：

1. `index`
2. 可选 `paper attach`
3. 自动问一个 overview 问题
4. `export note`

也就是说，旧的 `paper + repo + focus -> second-pass -> markdown` 链路已经不再是主实现。

## 当前实现边界

- 主交互形态是 CLI 单问单答，不是持久聊天 UI
- 代码理解主干是本地索引 + graph artifact + 结构化问答
- 论文是可附加解释层，不是默认上游
- 多语言扩展按接口设计预留，但第一版生产级解析只保证 Python

## 相关文档

- [docs/README.md](docs/README.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/roadmap.md](docs/roadmap.md)
