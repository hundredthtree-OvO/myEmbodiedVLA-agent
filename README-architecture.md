# Study Agent 架构图

这份文档用来补充 [README.md](/E:/my-embodied/README.md) 的实现视角，重点说明当前 `study-agent` 的仓库分析链路、角色分层方式，以及下一步 planned `second-pass reading` 在整体中的位置。

## 1. 整体构建链路

```mermaid
flowchart TD
    A["输入: paper / repo / focus / taste"] --> B["ingest_paper() / ingest_repo()"]
    B --> C["文件扫描与 file_groups"]
    C --> C1["类型候选层<br/>train / inference / config / core_model / deployment / data / utils"]
    C1 --> D["角色构建层<br/>architecture_entry / skeleton / component<br/>config_entry / deployment_entry"]
    D --> E["轻量 Python AST 索引<br/>class / def / import / base / call / tags"]
    E --> F["AST 定向重排<br/>entry / skeleton / component"]
    F --> G["RepoInfo"]
    G --> H["reading_path 构建"]
    H --> I["prompt_builder / composer"]
    I --> J["结构化学习笔记 / offline markdown"]
    H --> K["下一阶段: second-pass reading"]
    K --> L["更强的 repo evidence"]
    L --> M["Concept2Code tracing"]
```

## 2. 当前仓库侧主数据流

```mermaid
flowchart LR
    A["repo files"] --> B["file_groups"]
    B --> B1["train_candidates"]
    B --> B2["inference_candidates"]
    B --> B3["config_candidates"]
    B --> B4["core_model_candidates"]
    B --> B5["deployment_policy_candidates"]
    B --> B6["data / loss / env / docs / utils"]

    B --> C["role candidates"]
    C --> C1["architecture_entry_candidates"]
    C --> C2["architecture_skeleton_candidates"]
    C --> C3["architecture_component_candidates"]
    C --> C4["config_entry_candidates"]
    C --> C5["deployment_entry_candidates"]

    A --> D["Python AST index"]
    D --> D1["tags<br/>concrete_model_like / skeleton_like / component_like / script_like / bridge_like"]
    D --> D2["signals<br/>forward / predict_action / sample_actions / encode / predict / rollout / get_cost"]

    C --> E["graph_rank"]
    D --> E
    B1 --> E
    B2 --> E
    C4 --> E
    C5 --> E

    E --> F["reranked architecture layers"]
    F --> G["RepoInfo"]
```

## 3. `reading_path` 当前逻辑

在 `architecture` focus 下，当前阅读顺序已经不是单一混排，而是：

```text
architecture_entry
-> architecture_skeleton
-> architecture_component
-> config_entry
-> deployment_entry
```

可以把它理解成“先找主装配，再看骨架，再看底层组件，最后补配置和部署”。

## 4. 两层结构怎么配合

### 类型候选层

这一层回答的是：

```text
这些文件大概属于什么类型？
```

例如：

- `train_candidates`
- `inference_candidates`
- `config_candidates`
- `core_model_candidates`
- `deployment_policy_candidates`
- `data_candidates`
- `loss_candidates`
- `env_candidates`
- `docs_candidates`
- `utils_candidates`

### 角色构建层

这一层建立在类型层之上，回答的是：

```text
在 architecture 理解链路里，这些文件扮演什么角色？
```

例如：

- `architecture_entry_candidates`
- `architecture_skeleton_candidates`
- `architecture_component_candidates`
- `config_entry_candidates`
- `deployment_entry_candidates`

当前真实流程不是两棵平行树，而是：

```text
类型候选层 -> 角色构建层 -> AST 重排层 -> reading_path
```

## 5. 当前 AST 在做什么

当前 AST 是“轻量、文件级、服务排序”的，不是 full graph analysis。

它主要提供这些能力：

- 识别 concrete model / abstract base
- 识别 skeleton_like / component_like / script_like
- 看 train/eval/config 是否直接 import 或实例化某个 repo 内类
- 给 architecture entry / skeleton / component 做候选池内重排

它**还没有**做这些事：

- 全仓调用图
- 通用 PageRank
- Tree-sitter 多语言解析
- second-pass 细粒度代码路径抽取

## 6. 当前阶段判断

当前已经完成的是：

- role-aware ranking MVP
- `entry / skeleton / component` layering
- 轻量 AST rerank

当前下一步主线是：

```text
important file second-pass reading
```

也就是：

1. 从第一遍排序结果中挑 3-8 个关键文件
2. 做更细的文件内证据抽取
3. 强化 `Concept2Code tracing`

## 7. 一句话理解当前系统

```text
先把 repo 里的“文件类型”分粗类，
再把 architecture 相关文件分成入口 / 骨架 / 组件，
再用轻量 AST 把顺序排得更像人第一次读代码的顺序，
最后把这条阅读链路交给后续 second-pass reading。
```
