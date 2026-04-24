# LeWorldModel 架构学习笔记

## 1. 任务与输入

- Repository: `https://github.com/lucas-maes/le-wm`
- Paper: `E:\zoteroData\storage\V8GL3AAQ\Maes 等 - 2026 - LeWorldModel Stable End-to-End Joint-Embedding Predictive Architecture from Pixels.pdf`
- Focus: `SIGReg`, `JEPA`
- Analysis mode: `paper-aligned`
- Source access note: 本次没有成功把仓库克隆到本地临时目录，代码分析基于 GitHub 在线源码页面与项目页面完成；论文术语对齐主要参考项目页与论文标题信息。`INFERRED`

## 2. 仓库入口与主干候选

- Candidate 1: `jepa.py` - `class JEPA`
  - 作用：这是 LeWorldModel 的主体封装，统一定义了编码、一步预测、自回归 rollout 和规划 cost 计算。
- Candidate 2: `module.py` - `class SIGReg`, `class ARPredictor`, `class Embedder`, `class Transformer`
  - 作用：这里放了论文里最核心的可学习模块，尤其是 `SIGReg` 正则器和 JEPA predictor 的实现。
- Candidate 3: `train.py` - `lejepa_forward`, `run`
  - 作用：这里把论文目标函数落地成训练图，并实例化 `ViT encoder + action encoder + autoregressive predictor + SIGReg`。
- Candidate 4: `config/train/lewm.yaml`
  - 作用：给出 LeWM 的关键超参，能帮助判断论文图中的模块规模和默认设置，例如 `history_size: 3`, `embed_dim: 192`, `predictor.depth: 6`, `loss.sigreg.weight: 0.09`。

## 3. 架构总览

LeWorldModel 的代码实现非常“扁平”：仓库并没有拆出很多层级深的 model 子目录，而是把主逻辑压缩进 `jepa.py`, `module.py`, `train.py` 三个文件中。项目页把论文结构总结为两个主体组件：`encoder` 与 `predictor`，即先把像素观测 `o_t` 编成 latent `z_t`，再结合动作 `a_t` 预测下一时刻 latent `\hat{z}_{t+1}`。这个高层结构与代码完全对齐。`CONFIRMED`

代码里的 LeWM 实际由四块组合而成：

- 图像编码器：`train.py` 中通过 `spt.backbone.utils.vit_hf(...)` 构造 ViT 编码器。
- 动作编码器：`module.py` 中的 `Embedder`，把动作序列变成与 latent 对齐的 action embedding。
- 动力学预测器：`module.py` 中的 `ARPredictor`，本质上是一个带 `ConditionalBlock` 的自回归 Transformer。
- 稳定性正则：`module.py` 中的 `SIGReg`，训练时和预测损失相加。

从代码视角看，论文中的 JEPA 并不是一个“复杂大框架名称”，而是这里的整体组合接口：`JEPA(encoder, predictor, action_encoder, projector, pred_proj)`。`train.py` 先组装各子模块，再把它们塞进 `class JEPA`，最后通过 `lejepa_forward` 把论文损失写成：

- `pred_loss`: next-embedding prediction loss
- `sigreg_loss`: `SIGReg(emb.transpose(0, 1))`
- `loss = pred_loss + lambda * sigreg_loss`

这和项目页给出的公式 `L_LeWM = L_pred + lambda * SIGReg(Z)` 一致。`CONFIRMED`

如果把论文图映射到代码，可以粗略对应为：

- Encoder: `train.py` - `encoder = spt.backbone.utils.vit_hf(...)`
- Latent projection: `train.py` - `projector = MLP(...)`
- Action-conditioned predictor: `module.py` - `ARPredictor`, `ConditionalBlock`, `Transformer`
- Prediction projection: `train.py` - `predictor_proj = MLP(...)`
- Gaussian regularizer: `module.py` - `SIGReg`
- Planning-time rollout and scoring: `jepa.py` - `rollout`, `criterion`, `get_cost`

## 4. 核心执行路径

### 4.1 训练主路径

1. `train.py` - `run`
   - 先加载 HDF5 数据，再构造图像预处理和数值列标准化。
2. `train.py` - `encoder = spt.backbone.utils.vit_hf(...)`
   - 创建图像 backbone，默认不是预训练权重，说明这份实现强调从像素端到端训练。`CONFIRMED`
3. `train.py` - `predictor = ARPredictor(...)`
   - 创建 latent dynamics predictor。
4. `train.py` - `world_model = JEPA(...)`
   - 把 encoder、action encoder、predictor、projector、pred_proj 组装起来。
5. `train.py` - `lejepa_forward`
   - 调用 `self.model.encode(batch)` 先把像素和动作编码成 `emb` 与 `act_emb`。
6. `train.py` - `pred_emb = self.model.predict(ctx_emb, ctx_act)`
   - 用前 `history_size` 帧的 latent 和 action 预测未来 embedding。
7. `train.py` - `output["pred_loss"] = (pred_emb - tgt_emb).pow(2).mean()`
   - 计算论文里的 next-embedding prediction loss。
8. `train.py` - `output["sigreg_loss"] = self.sigreg(emb.transpose(0, 1))`
   - 对整段 latent 序列施加 Gaussian regularizer。
9. `train.py` - `output["loss"] = output["pred_loss"] + lambd * output["sigreg_loss"]`
   - 两项加权求和，得到最终训练目标。

### 4.2 规划/推理主路径

1. `jepa.py` - `get_cost`
   - 给定起始信息和候选动作序列，先把 goal 图像编码成 `goal_emb`。
2. `jepa.py` - `rollout`
   - 对每个候选动作序列做自回归 latent rollout。
3. `jepa.py` - `criterion`
   - 比较 rollout 后最后时刻的预测 embedding 与 goal embedding 的距离，作为规划 cost。

这意味着 LeWM 在规划时并不重建像素，也不在像素空间直接算 loss，而是完全在 latent space 中滚动预测和比较终点。这个实现与项目页 “plans purely from pixels ... picking those whose final embedding lands closest to the goal” 的描述一致。`CONFIRMED`

## 5. 核心模块深挖

### 5.1 `JEPA`

- 定位：`jepa.py` - `class JEPA`
- 角色：统一封装编码、一步预测、rollout、cost 计算，是整个 LeWM 的核心接口。
- 构造方式：
  - `encoder`
  - `predictor`
  - `action_encoder`
  - `projector`
  - `pred_proj`
- 输入输出：
  - `encode(info)` 输入像素与动作，输出 `emb` 和可选 `act_emb`
  - `predict(emb, act_emb)` 输出下一步 embedding 预测
  - `rollout(info, action_sequence)` 输出候选动作下的 latent rollout
  - `get_cost(info_dict, action_candidates)` 输出规划 cost
- 关键调用链：
  - `train.py` - `world_model = JEPA(...)`
  - `train.py` - `lejepa_forward -> self.model.encode -> self.model.predict`
  - `eval.py` / 规划策略 -> `get_cost`
- 证据等级：`CONFIRMED`

一个值得注意的实现选择是，`JEPA` 本身并不包含 loss 模块；loss 是在 `train.py` 的 `lejepa_forward` 里拼接的。这让 `JEPA` 更像一个“世界模型骨架”，而不是训练器。`CONFIRMED`

### 5.2 `ARPredictor`

- 定位：`module.py` - `class ARPredictor`
- 角色：实现论文里的 predictor，即根据历史 latent 与动作条件预测未来 latent。
- 构造方式：
  - `pos_embedding`
  - `Transformer(..., block_class=ConditionalBlock)`
- 输入输出：
  - 输入：`x` 为 latent 序列 `(B, T, d)`，`c` 为动作条件 `(B, T, act_dim)`
  - 输出：与 latent 同长度的预测序列
- 关键调用链：
  - `train.py` - `predictor = ARPredictor(...)`
  - `jepa.py` - `predict -> self.predictor(emb, act_emb)`
- 证据等级：`CONFIRMED`

这部分是 LeWM 里最接近“动力学建模器”的主体。和很多 world model 里显式 RNN 或 latent diffusion 不同，这里使用的是动作条件化的自回归 Transformer。`CONFIRMED`

### 5.3 `ConditionalBlock` / `Transformer`

- 定位：`module.py` - `class ConditionalBlock`, `class Transformer`
- 角色：给 predictor 提供序列建模能力，其中动作条件不是直接拼接到 token 上，而是通过 `AdaLN-zero modulation` 注入。
- 构造方式：
  - `ConditionalBlock` 内有 `Attention`, `FeedForward`, `adaLN_modulation`
  - `adaLN_modulation(c).chunk(6, dim=-1)` 产生 `shift/scale/gate`
- 输入输出：
  - 输入：latent token `x` 与动作条件 `c`
  - 输出：被动作调制后的序列表示
- 关键调用链：
  - `ARPredictor.forward -> self.transformer(x, c)`
- 证据等级：`CONFIRMED`

论文高层描述里只说 predictor 接收 `z_t` 与 `a_t`，代码则更具体地表明：动作条件是通过 AdaLN-zero 风格的条件化 Transformer 注入进去的，而不是简单 concat。这个细节对理解实现很重要。`CONFIRMED`

### 5.4 `SIGReg`

- 定位：`module.py` - `class SIGReg`
- 角色：对 latent 分布施加 Gaussian regularization，避免 JEPA 训练中的 collapse 或结构退化。
- 构造方式：
  - 初始化 `t`, `phi`, `weights`
  - 前向时采样随机投影矩阵 `A`
  - 计算 Epps-Pulley 风格统计量
- 输入输出：
  - 输入：`proj`，注释标明形状为 `(T, B, D)`
  - 输出：一个标量 regularization loss
- 关键调用链：
  - `train.py` - `sigreg = SIGReg(**cfg.loss.sigreg.kwargs)`
  - `train.py` - `output["sigreg_loss"] = self.sigreg(emb.transpose(0, 1))`
- 证据等级：`CONFIRMED`

`SIGReg` 在代码里不是“普通的 L2 或 variance penalty”，而是通过随机投影和特征函数近似去约束 latent 接近各向同性高斯。这和项目页 “regularizer enforcing Gaussian-distributed latent embeddings” 的描述是对齐的。`CONFIRMED`

## 6. 关注点专项

### 6.1 `SIGReg`

- Direct symbol hit: `yes`
- Closest evidence: `module.py` - `class SIGReg`; `train.py` - `self.sigreg(emb.transpose(0, 1))`
- 解释：
  - 项目页明确说 LeWM 只使用两个 loss term，其中一个就是 `SIGReg`。
  - 代码里 `SIGReg.forward` 对 `(T, B, D)` latent 做随机投影，随后计算一类与高斯特征函数对齐的统计误差。
  - 这个正则不是作用在 predictor 输出上，而是作用在 `encode` 得到的整段 latent `emb` 上。
- 关键实现点：
  - `knots: 17`, `num_proj: 1024` 在 `config/train/lewm.yaml` 中给出
  - `weight: 0.09` 决定它在总 loss 中的权重
- 为什么重要：
  - LeWM 的论文卖点之一就是“从像素端到端稳定训练”，`SIGReg` 正是稳定性的核心机制。
- 证据等级：`CONFIRMED`

### 6.2 `JEPA`

- Direct symbol hit: `yes`
- Closest evidence: `jepa.py` - `class JEPA`; `train.py` - `world_model = JEPA(...)`
- 解释：
  - 论文里的 JEPA 在代码里不是抽象口号，而是一个非常具体的组合对象：`encoder + predictor + action_encoder + projector + pred_proj`。
  - `encode` 负责把像素帧编码成 CLS-based latent embedding；`predict` 负责一步 latent 预测；`rollout` 负责规划时的多步 latent rollout；`get_cost` 负责和目标 embedding 做距离比较。
  - 因此从实现上看，LeWM 的 JEPA 是一个“用于训练和规划共享的 latent world model interface”。
- 关键实现点：
  - `encoder` 使用 `vit_hf(... pretrained=False)`
  - `projector` 和 `pred_proj` 都是额外的 `MLP`
  - `action_encoder` 与 `predictor` 分离，使动作条件有单独的编码流
- 证据等级：`CONFIRMED`

### 6.3 `JEPA` 在 LeWM 中的具体形态

- Direct symbol hit: `partial`
- Closest evidence:
  - 项目页 - “Encoder + Predictor”
  - `jepa.py` - `encode`, `predict`, `rollout`, `get_cost`
  - `train.py` - `pred_loss + lambda * sigreg_loss`
- 解释：
  - 标准 JEPA 常见描述是“上下文编码 + target 预测 + latent 对齐”，而 LeWM 的实现更偏向 world model：它把历史帧编码成 compact latent，再在 latent 空间做动作条件化的 autoregressive rollout。
  - 换句话说，LeWM 不是“通用表征学习 JEPA”的直接复刻，而是把 JEPA 改造成了 planning-oriented world model。
- 证据等级：`INFERRED`

## 7. 非核心层与暂不展开部分

- `eval.py` - 主要负责环境、数据集、策略封装和评估流程，不是 LeWM 结构本体。
- `utils.py` - 主要是图像预处理、数值列标准化和 checkpoint object dump，属于训练支撑层。
- `config/eval/*` 与 `config/train/data/*` - 影响实验设置，但不改变 JEPA/SIGReg 的核心结构。
- 外部依赖 `stable_worldmodel` 与 `stable_pretraining`
  - 负责环境管理、ViT backbone 构造、训练管理等；这部分不是当前仓库内可直接展开的核心实现。

## 8. 建议阅读顺序

1. 先看 `README.md`，建立论文目标和“只用 prediction loss + SIGReg”的整体印象。
2. 再看 `config/train/lewm.yaml`，记住默认设置：`history_size=3`, `embed_dim=192`, `predictor.depth=6`, `sigreg.weight=0.09`。
3. 然后看 `train.py` 的 `lejepa_forward`，先把训练目标串起来。
4. 接着看 `train.py` 里 `encoder`, `ARPredictor`, `Embedder`, `projector`, `pred_proj`, `JEPA` 的组装逻辑。
5. 再读 `jepa.py` 的 `encode` 和 `predict`，理解像素到 latent、latent 到未来 latent 的主路径。
6. 接着读 `module.py` 的 `ARPredictor`, `ConditionalBlock`, `Transformer`，理解 predictor 内部是怎么把动作作为条件注入的。
7. 最后读 `module.py` 的 `SIGReg`，理解 LeWM 稳定性的真正来源。
8. 如果你想看规划，再回头看 `jepa.py` 的 `rollout`, `criterion`, `get_cost`。

## 9. 未确认点

- 论文 PDF 本地文件虽然存在，但本机 PDF 文本提取工具没有成功完成抽取，所以术语对齐主要依赖项目页与在线源码，而不是逐段核对论文正文。`INFERRED`
- 图像 encoder 的具体实现来自外部依赖 `stable_pretraining`，当前仓库只看得到它是 `vit_hf(... pretrained=False)`，但看不到更细的 ViT 实现细节。`INFERRED`
- `SIGReg` 的理论细节在代码里可读到实现，但更完整的数学动机来自其引用的 LeJEPA；如果你后面要深挖它为什么能稳定 JEPA，建议继续看 LeJEPA 原论文。`INFERRED`
