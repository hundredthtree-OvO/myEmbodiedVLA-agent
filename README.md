# VLA Study Agent

`study-agent` 是一个 Codex-first 的 VLA 论文-代码对齐 CLI。它面向个人研究工作流：输入论文来源、代码仓库、关注点和 taste profile，由本地规则层准备证据包，再交给 Codex 生成结构化 Markdown 学习笔记。

当前版本的定位是：**Codex-first 的论文-代码对齐研究副驾**。  
下一阶段的目标是：**从“笔记生成器”走向带学习闭环的研究学习型 Agent**。

当前项目 **专门针对Windows系统** ，旨在完善用户在Windows上的工作流。（其实是作者目前只有自己的小笔记本）

第一版重点解决两个问题：

- 读 VLA 论文时，新概念和新架构不够清晰
- 论文表述和代码实现很难在模块/函数级别对齐

## 功能概览

- `analyze`：分析论文与仓库，默认调用 Codex 生成结构化学习笔记
- `codex test`：测试本机 Codex auth 与 Codex Responses endpoint 是否可用
- `config set-model`：切换默认 Codex 模型，当前支持 `gpt-5.4` / `gpt-5.5`
- `profile show`：查看当前显式偏好配置
- `profile update`：应用预设偏好
- `feedback apply`：根据你的短反馈更新 taste profile
- `--zotero-title`：按题名从本地 Zotero 查找 PDF 附件
- `--engine codex`：默认主路径，使用 Codex Responses endpoint
- `--engine offline`：调试用 fallback，只输出规则模板结果
- `--cleanup`：分析结束后按需清理 PDF cache 或远程仓库 cache

## 环境

本项目使用 `uv` 管理运行环境。为了让缓存也留在工作区内，建议在 PowerShell 中先设置：

```powershell
$env:UV_CACHE_DIR='.tmp\uv-cache'
```

如果需要让测试直接导入 `src` 下的包：

```powershell
$env:PYTHONPATH='src'
```

## 快速开始

直接启动 PowerShell 向导页：

```powershell
uv run python study_agent_cli.py tui
```

或者直接运行启动脚本：

```powershell
.\start-study-agent.ps1
```

查看当前 profile：

```powershell
uv run python study_agent_cli.py profile show
```

测试 Codex 接入：

```powershell
uv run python study_agent_cli.py codex test
```

把默认模型切到 `gpt-5.4`：

```powershell
uv run python study_agent_cli.py config set-model gpt-5.4
```

单次分析临时改用 `gpt-5.4`：

```powershell
uv run python study_agent_cli.py analyze --zotero-title "World-Value-Action Model" --repo https://github.com/Win-commit/WAV --focus "Latent Planning and Iterative Inference" --out notes\WAV-latent-planning.md --model gpt-5.4
```

用 Zotero 题名生成一份学习笔记：

```powershell
uv run python study_agent_cli.py analyze --zotero-title "World-Value-Action Model" --repo https://github.com/Win-commit/WAV --focus "Latent Planning and Iterative Inference" --out notes\WAV-latent-planning.md
```

如果不想保留本次 PDF 临时缓存和远程 clone 的仓库副本：

```powershell
uv run python study_agent_cli.py analyze --zotero-title "World-Value-Action Model" --repo https://github.com/Win-commit/WAV --focus "Latent Planning and Iterative Inference" --out notes\WAV-latent-planning.md --cleanup all
```

离线调试 evidence/template：

```powershell
uv run python study_agent_cli.py analyze --paper notes\ACoT-VLA-architecture-study.md --repo . --focus EAR,IAR,kv_cache --out notes\demo-study-agent.md --engine offline
```

应用你的显式反馈：

```powershell
uv run python study_agent_cli.py feedback apply --from notes\demo-study-agent.md --note "more code-first, keep uncertainty labels"
```

## 命令说明

### analyze

```powershell
uv run python study_agent_cli.py analyze --paper <paper> --repo <repo> --focus <terms> --out <output.md> --engine offline
```

参数含义：

- `--paper`：论文 URL、本地 PDF、本地 Markdown 或文本文件
- `--zotero-title`：Zotero 题名模糊查询；如果找到 PDF 附件，会自动作为 paper 输入
- `--repo`：GitHub URL 或本地仓库路径
- `--focus`：逗号分隔的关注点，例如 `EAR,IAR,kv_cache`
- `--out`：Markdown 输出路径
- `--mode`：分析模式，默认 `paper-aligned`
- `--engine`：`codex` 或 `offline`
- `--model`：单次运行临时覆盖模型，支持 `gpt-5.4` / `gpt-5.5`
- `--cleanup`：`none`、`temp`、`repo` 或 `all`；默认 `none`

### config

```powershell
uv run python study_agent_cli.py config show
uv run python study_agent_cli.py config set-model gpt-5.4
uv run python study_agent_cli.py config set-model gpt-5.5
```

说明：

- `config show`：查看当前配置，包括默认模型
- `config set-model`：持久修改 `.study-agent/config.json` 里的默认模型

### cleanup

```powershell
uv run python study_agent_cli.py cleanup --target temp
uv run python study_agent_cli.py cleanup --target all
```

清理范围：

- `temp`：删除 `.tmp/pdf-cache`
- `all`：删除 `.tmp/pdf-cache` 和 `.study-agent/repos`

清理命令只删除工作区内的受控缓存目录，不会碰 Zotero 数据目录、Codex auth 或输出笔记。

### profile

```powershell
uv run python study_agent_cli.py profile show
uv run python study_agent_cli.py profile update --preset concise-code-first
```

profile 默认存放在：

```text
.study-agent/profile.json
```

它记录你的显式偏好，例如章节顺序、关注重点、证据标签风格和默认分析粒度。

### feedback

```powershell
uv run python study_agent_cli.py feedback apply --from notes\demo-study-agent.md --note "少讲背景，多讲实现路径"
```

第一版不会做黑盒隐式学习，而是把你的短反馈转成可检查、可编辑的 profile 更新。

### tui

```powershell
uv run python study_agent_cli.py tui
```

向导页会自动：

- 在本次进程内设置 `UV_CACHE_DIR=.tmp\uv-cache`
- 在本次进程内补 `PYTHONPATH=src`
- 显示 workspace、Codex 状态、Zotero 数据目录、阶段列表
- 在分析和 `codex test` 前允许选择本次要用的模型
- 提供固定工作流和快捷动作

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

证据标签默认使用：

- `CONFIRMED`：在论文或代码中有直接证据
- `INFERRED`：由上下文推断，需要人工复核

## Codex 接入

默认使用本机 Codex 登录凭据：

```text
C:\path\of\user\.codex\auth.json
```

默认配置在：

```text
.study-agent/config.json
```

`analyze` 默认不静默回退到规则版。如果 Codex 不可用，会直接报错；需要规则调试时显式传 `--engine offline`。

## Zotero 联动

如果 Zotero 主库被锁定，程序会尝试读取 `.bak` 备份库。Zotero 数据库只读访问，不会写入或修改 Zotero 数据。

## 测试

```powershell
$env:UV_CACHE_DIR='.tmp\uv-cache'
$env:PYTHONPATH='src'
uv run python -m unittest discover -s tests
```

当前测试覆盖：

- profile preset 更新
- feedback 到 profile 的显式偏好更新
- 离线 paper/repo 分析到 Markdown 输出的完整链路

## TODO

当前 roadmap 采用 **Evidence First**：先把“论文细节 ↔ 代码实现”的对齐能力做强，再把“越用越聪明”的学习闭环接上。PowerShell/TUI 与 Zotero 继续保留，但降级为支撑能力，而不是主线。

### P0：Foundation Hardening

- [ ] 支持“已手动 clone 的本地仓库优先”：当 GitHub clone 失败时，提示用户改用 `--repo E:\path\to\repo`，并在错误信息里说明当前 Git 代理配置。
- [ ] 输出“证据不足”诊断区：当 repo 不是目标仓库或 clone 失败时，明确告诉用户本次代码对齐不可用。
- [ ] 增加更清楚的错误消息：把网络、代理、auth、PDF 抽取、Zotero locked 分成可读的用户提示。

### P1：Evidence Core

- [ ] 把 repo evidence pack 从简单关键词扫描升级到结构化分类：文件类型分组、入口文件、训练脚本、推理脚本、config/model/loss/data 候选。
- [ ] 增加 AST 级索引：class/function/import/call 的粗粒度索引，支撑比关键词更稳的候选定位。
- [ ] 增加 dependency/config 索引：识别 `transformers` / `timm` / Hugging Face 模型名、yaml/json/toml/Hydra/argparse 配置来源。
- [ ] 增加重点文件二次读取：先粗扫描，再让 Codex 选择 3-8 个关键文件，最后读取完整上下文后生成最终分析。
- [ ] 改进 PDF / paper focus 抽取：更稳定地定位用户指定 section，并优先抽取与 focus 强相关段落。
- [ ] 新增第一批研究模式：`loss-trace`、`module-trace`、`architecture-diff`。
- [ ] 输出目标从“找到相关文件”提升到“能解释 loss 实现、模块折叠位置和与主流 VLA 的差异”。

### P2：Learning Loop

- [ ] 每次任务保存更完整的 trace：request、focus、evidence、output、失败点、用户反馈。
- [ ] 新增 session reflection：总结这次什么分析方式有效、哪些证据不足、下次该优先读哪些类型的文件。
- [ ] 把 `feedback apply` 产生的 taste memory 做成结构化 patch，而不是只追加 Markdown。
- [ ] 区分低风险偏好和高风险偏好：详略、章节顺序可自动合并；删除章节、改变证据规则需要确认。
- [ ] 增加可复用的 skill memory：先用 Markdown/JSON 卡片沉淀分析能力，例如 `analyze_loss_design`、`map_action_head_to_code`、`detect_siglip_usage`、`identify_training_inference_path`。
- [ ] 根据 focus / repo 命中自动召回相关 skill，把 taste/profile 变成 learning loop 的一部分，而不是唯一记忆。
- [ ] prompt 中加入最近 2-3 次高质量输出片段，作为 few-shot taste 示例。
- [ ] 增加 `profile diff`，显示本次反馈会如何改变 profile。

### P3：Concept Library 与研究输出升级

- [ ] 增加轻量 concept cards / alias cards：先覆盖高频概念，例如 `SigLIP`、`DINOv2`、`JEPA`、`world model`、`bridge attention`、`action head`。
- [ ] 在输出中新增固定研究章节：论文属于哪类架构、与主流 VLA 的结构差异、Novelty Implementation Cards、Loss Trace、My VLA Borrowing Plan。
- [ ] 支持 shape / 变量流深挖模式：对指定函数输出张量形状、数据流和论文公式对应关系。
- [ ] 支持多论文对比：例如把 WAV、ACoT-VLA、VLA-Adapter 的 planning/reasoning/action head 对齐成表。
- [ ] 支持图表生成：把论文模块与代码调用链生成 Mermaid 图。
- [ ] 支持“复现导向输出”：除了学习笔记，还生成最小复现阅读路线和实验入口清单。

### P4：PowerShell/TUI 与 Zotero 支撑项

- [x] 新增交互式入口，例如 `uv run python study_agent_cli.py tui`。
- [x] 页面启动后提供固定工作流：选择 Zotero 论文、输入/选择 repo、输入 focus、选择 cleanup 策略、运行分析。
- [x] 增加运行状态显示：Zotero 查询、PDF 抽取、repo 准备、Codex 调用、session 保存。
- [x] 增加历史 session 浏览：列出 `.study-agent/sessions`，可打开上次 evidence/output。
- [x] 增加快捷动作：`codex test`、`cleanup temp`、`cleanup all`、`profile show`。
- [ ] 如果 `repo` 是 GitHub URL，在正式分析前自动做一次 clone probe；失败时提前报错，并显示代理配置与“改用本地仓库路径”的提示。
- [ ] 补全“最近使用”输入复用：最近的 Zotero title、repo、focus、cleanup 策略都能直接回填。
- [ ] 把运行状态区再做清楚一点：区分 `current stage`、`last message` 和 `assistant output preview`，增强“正在工作”的可感知性。
- [ ] 在 TUI 中增加专门的 GitHub probe cache 清理入口，便于清掉 clone test 的残留探针目录。
- [ ] 改进 `Open Last Session`：支持更明确地打开或预览 `request.json`、`evidence.md`、`output.md`。
- [ ] 支持列出 Zotero 搜索候选，而不是只取第一个模糊匹配结果。
- [ ] 读取 Zotero metadata：作者、年份、会议/期刊、DOI、abstract、tags、collections。
- [ ] 支持从 Zotero item key 或 attachment key 精确定位论文。
- [ ] 支持读取 Zotero note/annotation，把用户已有批注放入 Codex prompt。
- [ ] 避免依赖 `.bak` 的新鲜度：主库 locked 时可复制一份只读临时 sqlite 再查询。

### P5：工程化与发布

- [ ] 把当前非打包模式升级为可安装 CLI：`uv run study-agent ...`。
- [ ] 增加 `.gitignore`，忽略 `.tmp/`、`.venv/`、`__pycache__/`、session 输出和 repo cache。
- [ ] 增加配置命令：`config show`、`config set zotero_data_dir ...` 等剩余配置项管理。
- [ ] 增加更细的测试：Codex streaming event 变体、Zotero locked fallback、PDF 抽取 fallback、cleanup 安全边界。
