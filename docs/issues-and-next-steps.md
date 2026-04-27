# 当前问题与后续简要解法

这份文档整理当前项目里已经暴露出来、且值得进入后续迭代的问题。目标不是一次性定完完整方案，而是先把问题边界、风险和低成本解法写清楚。

## 一、对当前自查结论的判断

### 1. evidence quality gate 缺失

判断：正确。

当前系统确实是在调用 Codex 之后，才由输出里的 `[Missing Evidence]` 暴露质量不足。这会导致一次本可以避免的 Codex call。

简要解法：

- 在 `prompt_builder` 之前增加一个轻量 `evidence quality gate`
- 重点检查：
  - paper text 是否为空或极短
  - `architecture_entry + architecture_skeleton` 是否都为空
  - `repo.hits` / `code_map` 是否几乎全是 inferred
- 根据结果决定：
  - 直接报警并中止
  - 自动降级到 offline 模板
  - 或继续请求，但在 session 里显式记录“低证据运行”

### 2. taste profile 影响面太窄

判断：正确。

现在 `TasteProfile` 主要影响 prompt 组织和少量 `reading_order_style`，但还没有真正反向影响 evidence 准备阶段。

简要解法：

- 让 profile 参与 `build_reading_path()` 的路径偏置
- 进一步让 profile 参与第一遍候选排序的弱权重调节
- 例如：
  - `code-first`：提高 `architecture_entry / core_model / train path`
  - `paper-first`：提高 `concept-first` 阅读顺序与 config / docs 辅助证据
- 原则上只做“弱偏置”，不应推翻基于 repo 证据的主排序

### 3. `ingest_repo()` 正在走向上帝函数

判断：方向正确，但有一个口径需要纠正。

目前 `reading_path` 还不是在 `ingest_repo()` 里构建的，而是在 `pipeline -> build_reading_path()` 这一层完成。  
不过即便如此，`ingest_repo()` 现在也已经承担了过多职责：

- repo 准备
- 文件扫描
- 类型候选层
- 角色构建层
- AST 索引
- AST 重排

简要解法：

- 在 P1 结束后做一次结构性拆分
- 推荐边界：
  - `classify_files()`
  - `assign_roles()`
  - `build_ast_index()`
  - `rerank_role_candidates()`
  - `build_repo_info()`
- 后续 second-pass 的关键文件选择，不应再继续塞回 `ingest_repo()`

### 4. repo evidence 没有缓存

判断：正确，而且价值很高。

当前同一 repo 用不同 focus 反复分析时，文件扫描和 AST 索引会完全重跑。对于本地已 clone 的大仓库，这部分浪费明显。

简要解法：

- 给 `RepoInfo` 的前半段构建增加本地缓存
- 建议缓存粒度：
  - 文件扫描结果
  - 类型候选层
  - AST 索引
  - 角色层基础结果
- 失效策略可先做简单版：
  - 本地 repo 用 `HEAD commit hash`
  - 非 git 目录用文件时间戳 / 文件数摘要
- 建议目录：
  - `.study-agent/cache/repos/`

### 5. 单次大 prompt 的上下文压力

判断：正确，而且会随着 second-pass 扩大而更明显。

现在最终 prompt 已经包含：

- paper excerpt
- repo candidate layers
- reading_path
- diagnostics
- AST debug
- second-pass evidence

如果不做预算控制，后续只会继续膨胀。

简要解法：

- 在 `prompt_builder` 引入明确的 budget 概念
- 不只靠 `max_evidence_chars` 统一截断，而是分层配额
- 推荐优先级：
  - 保留 `architecture_entry`
  - 保留 `architecture_skeleton`
  - 保留 second-pass confirmed links
  - `component` 降级为文件名列表
  - debug 信息按预算裁剪

### 6. session 之间没有已分析 repo 的索引

判断：正确，而且对 P2 很有帮助。

当前 profile / session 已经在落盘，但没有一个“repo 级别的最近理解摘要”。

简要解法：

- 增加一个极轻量索引，例如：
  - `.study-agent/index.json`
- 先记录：
  - repo 标识
  - 上次分析时间
  - 关键 `architecture_entry / skeleton`
  - 最近一次 `concept2code` 摘要
  - session 路径
- 先作为 session 间导航和轻记忆，不急着做 retrieval

## 二、补充的其它问题

### 7. second-pass 的局部证据切片还太粗

判断：这是当前最直接影响质量的问题之一。

目前 second-pass 对大文件更像“截一段前缀 excerpt”，这会漏掉真正关键的后半段逻辑。`ACoT-VLA` 已经暴露出这个问题。

简要解法：

- 从“文件前缀 excerpt”升级到“symbol-aware / concept-aware 片段抽取”
- 对于大文件，优先抽：
  - 类定义附近
  - `forward / sample_actions / compute_loss`
  - `*_out_proj / *_reasoner / fusion` 等概念相关区域
- 如果 Round 1 / Round 2 反复点名同一文件，允许补读该文件的后续片段，而不是只补新文件

### 8. Concept2Code 还缺少概念规范化层

判断：这是进入长期记忆前需要补的一层。

现在 `concept2code.json` 已经有结构化字段，但 concept 本身仍然高度依赖当次 focus 词和 Codex 措辞。

风险：

- 同一个概念可能以多个名字落盘
- 不同 repo 的相近概念很难横向比较

简要解法：

- 增加轻量 `concept alias / canonical concept` 层
- 先不做完整 library，只做：
  - `raw_concept`
  - `canonical_concept`
  - `source`（paper / user focus / inferred）

### 9. second-pass 输出协议仍然比较脆弱

判断：当前已经比单纯 markdown 好很多，但仍然依赖 Codex 输出结构化 JSON 的稳定性。

风险：

- 模型输出轻微偏离格式，就会影响解析
- fallback 还比较弱

简要解法：

- 强化 second-pass 的 JSON contract
- 对 parser 增加更稳的错误恢复和 schema 校验
- 在 session 中显式记录：
  - parse success / failure
  - fallback path

### 10. 缺少“分析质量”层面的观测指标

判断：现在更多是靠人工看 session 结果，很难比较一次改动到底有没有提升。

简要解法：

- 增加轻量 metrics，不一定要复杂监控
- 每次 analyze 可以记录：
  - evidence score
  - second-pass 选中文件数
  - round2 补读命中率
  - confirmed / inferred / missing 数量
  - 最终 prompt 大小
- 这些指标先写入 session json 即可

### 11. 当前 cache / session / memory 三层边界还不够清晰

判断：这是后续工程化时会碰到的问题。

现在已经出现三类本地状态：

- repo/cache
- session artifacts
- profile / taste memory

但它们各自的职责边界还没有完全定清楚。

简要解法：

- 明确区分：
  - `cache`：为加速而存，可失效重建
  - `session`：为复盘而存，保留单次运行细节
  - `memory/index`：为跨 session 复用而存，保留摘要化知识

## 三、优先级建议

如果按“投入小、回报高、对当前主线帮助大”的顺序，我会建议优先做：

1. `evidence quality gate`
2. second-pass 的 `symbol-aware / concept-aware` 片段抽取
3. prompt budget 与分层截断策略
4. repo evidence cache
5. repo 级轻量 index

之后再做：

6. `ingest_repo()` 结构拆分
7. profile 对 evidence/ranking 的弱偏置
8. concept canonicalization
9. second-pass schema / metrics / memory 边界收口

## 四、当前结论

你列的 6 条里，整体判断是：

- ① 对
- ② 对
- ③ 方向对，但需要修正一个细节：`reading_path` 目前不在 `ingest_repo()` 里
- ④ 对
- ⑤ 对
- ⑥ 对

也就是说，这 6 条不是“可能的问题”，而是已经足够进入后续路线图管理的问题。
---

## 补充：2026-04-27 新增问题整理

这一轮讨论里，又进一步暴露出几个值得正式纳入的问题。它们和前面的工程问题不是冲突关系，而是进入 P2 后会越来越重要的补充。

### 12. `focus-only` 的分析入口自由度不够

判断：正确，而且这是进入 P2 后会越来越明显的问题。

当前系统虽然已经支持：

- `focus`
- `taste`
- role-aware ranking
- second-pass

但整体入口仍然偏“给几个关键词，然后围绕这些词做分析”。

这会带来两个限制：

1. 用户必须一开始就知道自己想问什么
2. 系统缺少“先理解论文问题，再决定去代码里验证什么”的能力

简要解法：

- 引入一个轻量 `paper understanding pass`
- 先从论文中抽：
  - 核心主张
  - 显式模块
  - 关键待验证问题
  - 和用户 focus 对齐后的分析任务
- 让后续 repo tracing 同时受到两类输入驱动：
  - `user_focus`
  - `paper_questions`

也就是说，`focus` 以后更像“优先级引导”，而不是唯一入口。

### 13. 全局 `concept template` 不具备可扩展性

判断：正确。

如果把后续提升路线走成：

- 为每篇论文、每个概念不断补模板

那很快会走向不可维护，也不具备泛化性。

更合理的方向不是“给所有论文预制 concept template”，而是：

- 每篇论文先生成自己的结构假设
- 再用一套通用框架去代码中寻找这些结构角色

简要解法：

- 不维护大而全的 concept 词表
- 改为“论文内生结构假设”：
  - query 是什么
  - condition 是什么
  - output 是什么
  - 有没有 cross/self attention
  - 有没有 fusion/gating
- second-pass 再围绕这些结构角色补片段

### 14. 仅靠 `pypdf` 不足以支撑论文结构图理解

判断：正确，而且这会影响后续 paper-side understanding 的上限。

`pypdf` 适合做：

- 标题
- 摘要
- 方法段落
- figure caption

但它不适合直接理解：

- 模型结构图
- 箭头链路
- 颜色分组
- 模块位置关系

尤其像 `VLA-Adapter` Figure 5 这类图，真正关键的往往是视觉结构，而不是正文里是否完整复述。

简要解法：

- 论文读取后续拆成双通道：
  - 文本层：`pypdf`
  - 图示层：关键页截图 / 图块截图
- 图示层优先做结构理解：
  - 模块
  - 箭头
  - 重复块
  - 输入输出关系
- OCR 作为补充，而不是起点：
  - 用来补模块小字
  - 用来抽图中 label
  - 用来辅助 caption 对齐

### 15. 初次分析不能依赖“已有论文笔记”

判断：正确。

当前一些讨论里会把“论文笔记”当成输入来源之一，但这不能成为前提条件。

更合理的顺序应该是：

- 初次分析：
  - 直接读 PDF
  - 产出 paper understanding / study note
- 后续分析：
  - 如果已经存在笔记，再把它作为复用输入

简要解法：

- 明确区分：
  - `paper_source`：原始 PDF / 文本
  - `paper_notes`：历史派生产物
- 后续 pipeline 默认应当能够在“没有笔记”的情况下独立运行
