# Roadmap

## P1: Workspace QA Stabilization

目标：把当前 CLI 工作流打磨成稳定的 repo QA 基础版。

重点：

- 提升 `ask` 的实现类回答质量
- 改善 symbol / span 检索
- 补充更多 `ModuleCard` / `QuestionCard` 模板
- 清理剩余旧链路残留

完成标准：

- 能稳定回答“某模块如何实现”
- 能在有论文时回答“为什么这样设计”
- 失败时明确输出 uncertainty，而不是编造

## P2: Better Tracing

目标：从“局部实现说明”升级到“关键路径追踪”。

重点：

- action generation trace
- loss trace
- inference trace
- config-to-module trace

完成标准：

- `ask` 对路径类问题能给出更连贯的调用链或配置链

## P3: Research Assets

目标：让问答结果沉淀成真正可复用的研究资产。

重点：

- `RepoCard`
- 更强的 `ModuleCard`
- question clustering
- export note 质量提升

完成标准：

- 一个 workspace 能持续积累可复用卡片，而不是只保存一次性 session

## P4: Multi-Language Parsing

目标：在保持 Python 质量的前提下，逐步接入更强的多语言解析。

重点：

- 引入 tree-sitter 风格 backend
- 扩展 JS / TS / Rust / C++ 最小支持
- 统一 symbol / relation schema

完成标准：

- 多语言 repo 不崩溃
- 非 Python 文件不再只是纯文本 fallback
