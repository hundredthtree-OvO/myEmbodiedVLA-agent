# VLA Study Agent

`study-agent` 是一个 Codex-first 的 VLA 论文-代码对齐 CLI。它面向个人研究工作流：输入论文来源、代码仓库、关注点和 taste/profile，由本地 evidence 层准备证据，再交给 Codex 生成结构化 Markdown 学习笔记。

当前版本定位是：
- Codex-first 的论文-代码对齐研究副驾
- 面向 Windows + PowerShell 工作流

当前第一版主要解决两类问题：
- 阅读 VLA 论文时，新概念和新架构不够清晰
- 论文表述和代码实现很难在模块/函数级别对齐

## 功能概览

- `analyze`：分析论文与仓库，默认调用 Codex 生成结构化学习笔记
- `codex test`：测试本机 Codex auth 与 Codex Responses endpoint 是否可用
- `config set-model`：切换默认 Codex 模型，当前支持 `gpt-5.4` / `gpt-5.5`
- `profile show` / `profile update`：管理显式 taste profile
- `feedback apply`：根据短反馈更新 taste/profile
- `--zotero-title`：按标题从本地 Zotero 查找 PDF 附件
- `--engine offline`：调试 evidence pack 与离线模板输出
- `--cleanup`：按需清理 PDF cache 或远程 repo cache
- `tui`：PowerShell 向导式启动页

## 环境

推荐在 PowerShell 中先设置：

```powershell
$env:UV_CACHE_DIR='.tmp\uv-cache'
$env:PYTHONPATH='src'
```

这样 `uv` 缓存和运行时导入都会留在工作区内。

## 快速开始

启动 PowerShell 向导页：

```powershell
uv run python study_agent_cli.py tui
```

或者：

```powershell
.\start-study-agent.ps1
```

测试 Codex 接入：

```powershell
uv run python study_agent_cli.py codex test
```

切换默认模型：

```powershell
uv run python study_agent_cli.py config set-model gpt-5.4
uv run python study_agent_cli.py config set-model gpt-5.5
```

用 Zotero 标题生成一份学习笔记：

```powershell
uv run python study_agent_cli.py analyze --zotero-title "World-Value-Action Model" --repo https://github.com/Win-commit/WAV --focus "Latent Planning and Iterative Inference" --out notes\WAV-latent-planning.md
```

如果远程仓库已手动 clone 到本地：

```powershell
uv run python study_agent_cli.py analyze --zotero-title "World-Value-Action Model" --repo E:\path\to\WAV --focus "Latent Planning and Iterative Inference" --out notes\WAV-latent-planning.md
```

离线调试 evidence/template：

```powershell
uv run python study_agent_cli.py analyze --paper notes\ACoT-VLA-architecture-study.md --repo . --focus EAR,IAR,kv_cache --out notes\demo-study-agent.md --engine offline
```

应用短反馈：

```powershell
uv run python study_agent_cli.py feedback apply --from notes\demo-study-agent.md --note "more code-first, keep uncertainty labels"
```

## 常用命令

### analyze

```powershell
uv run python study_agent_cli.py analyze --paper <paper> --repo <repo> --focus <terms> --out <output.md>
```

常用参数：
- `--paper`：论文 URL、本地 PDF、本地 Markdown 或文本
- `--zotero-title`：按 Zotero 标题模糊查询
- `--repo`：GitHub URL 或本地仓库路径
- `--focus`：逗号分隔关注点
- `--out`：Markdown 输出路径
- `--engine`：`codex` 或 `offline`
- `--model`：单次覆盖模型，支持 `gpt-5.4` / `gpt-5.5`
- `--cleanup`：`none`、`temp`、`repo` 或 `all`

失败时的默认行为：
- 远程 clone 失败会提示改用本地 `--repo E:\path\to\repo`
- 错误信息会尽量区分 `Zotero`、`PDF`、`repo`、`Codex auth/request`
- 低证据分析会显式输出 `[Missing Evidence]`

### config

```powershell
uv run python study_agent_cli.py config show
uv run python study_agent_cli.py config set-model gpt-5.4
```

### profile

```powershell
uv run python study_agent_cli.py profile show
uv run python study_agent_cli.py profile update --preset concise-code-first
```

profile 默认位置：

```text
.study-agent/profile.json
```

### cleanup

```powershell
uv run python study_agent_cli.py cleanup --target temp
uv run python study_agent_cli.py cleanup --target all
```

清理只作用于工作区内受控缓存目录，不会碰 Zotero 数据、Codex auth 或输出笔记。

## 输出结构

默认生成的 Markdown 包含：
- 任务与输入
- 论文核心概念解释
- 仓库入口与主干候选
- 论文模块 -> 代码模块映射
- 训练/推理主路径
- 关注点专项
- 建议阅读顺序
- 未确认点

默认证据标签：
- `CONFIRMED`
- `INFERRED`
- `[Missing Evidence]`

## Codex 与 Zotero

默认使用本机 Codex 登录凭据：

```text
C:\Users\name\.codex\auth.json
```

默认配置文件：

```text
.study-agent/config.json
```

Zotero 仅做只读访问；主库被锁时会尝试读取 `.bak` 备份库。

## 测试

自动测试：

```powershell
$env:UV_CACHE_DIR='.tmp\uv-cache'
$env:PYTHONPATH='src'
uv run python -m unittest discover -s tests
```

可选真实仓库验收：

```powershell
uv run python study_agent_cli.py github test --repo-url https://github.com/Win-commit/WAV
uv run python study_agent_cli.py analyze --zotero-title "World-Value-Action Model" --repo https://github.com/Win-commit/WAV --focus "Latent Planning and Iterative Inference" --out notes\wav-evidence-check.md --engine offline
```

## TODO

当前 roadmap 采用 **Evidence First**：先把“论文细节 -> 代码实现”的对齐能力做强，再把“越用越聪明”的学习闭环接上。详细实施拆解、MVP 范围和阶段计划见 [docs/roadmap-detailed.md](docs/roadmap-detailed.md)。

### P0：Foundation Hardening

- [x] 远程仓库 fallback、代理诊断、错误消息分层
- [x] `Missing Evidence` 与低证据提示

### P1：Evidence Core

- [x] Repo evidence pack 结构化分类
- [x] Role-aware ranking MVP：已完成 `entry / skeleton / component` 分层与轻量 AST rerank
- [ ] 重点文件二次读取（important file second-pass reading）
- [x] Lightweight Python AST / config 索引（仅用于 architecture sorting），full dependency graph 暂未引入

### P2：Learning Loop

- [ ] session reflection、skill memory、retrieval
- [ ] 更结构化的 taste/profile patch 与 few-shot taste 示例

### P3：Concept Library 与研究输出升级

- [ ] concept alias registry 与 concept library
- [ ] Concept-Code Mapping Cards、Novelty Implementation Cards、My VLA Borrowing Plan
- [ ] shape / 变量流、多论文对比、复现导向输出

### P4：PowerShell/TUI 与 Zotero 支撑项

- [x] TUI、session 浏览、基础 cleanup / codex test / profile 动作
- [ ] 最近输入复用、状态区增强、GitHub probe 前置检查
- [ ] 更深的 Zotero metadata / annotation / 候选列表支持

### P5：工程化与发布

- [ ] 可安装 CLI、配置命令补齐、缓存与测试体系加固
