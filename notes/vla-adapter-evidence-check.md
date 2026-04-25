# VLA-Adapter 代码分析：Action Head 与 Bridge Attention 架构学习笔记

## 1. 任务与输入

- Paper: `notes\VLA-Adapter-bridge-attention-code-analysis.md`
- Repository: `E:\my-embodied\.study-agent\repos\VLA-Adapter`
- Focus: `bridge attention`
- Analysis mode: `paper-aligned`
- Engine: `offline`

## 2. 论文核心概念解释

### bridge attention

- Summary: `bridge attention` appears in the paper material and should be treated as a primary reading target.
- Evidence: `CONFIRMED`

## 3. 仓库入口与主干候选

- Scanned files: `148`
- File groups:
  - `docs`: `README.md`, `pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b/README.md`, `experiments/robot/aloha/README.md`, `our_envs.txt`, `vla_adapter.egg-info/SOURCES.txt`
  - `train_scripts`: `experiments/robot/aloha/train_files/setup_training.sh`, `experiments/robot/aloha/train_files/train_aloha.sh`, `experiments/robot/aloha/train_files/download_models.sh`, `prismatic/training/train_utils.py`, `vla-scripts/train.py`
  - `inference_scripts`: `experiments/robot/aloha/eval_files/deploy_server.sh`, `experiments/robot/server_deploy/deploy.py`, `experiments/robot/aloha/eval_files/run_eval_client.sh`, `experiments/robot/aloha/eval_files/run_eval_client_fake.sh`, `vla-scripts/deploy.py`
  - `configs`: `pretrained_models/configs/config.json`, `pretrained_models/configs/tokenizer_config.json`, `pretrained_models/configs/processor_config.json`, `pretrained_models/configs/generation_config.json`, `pretrained_models/configs/preprocessor_config.json`
  - `core_model`: `prismatic/models/transformer_utils.py`, `prismatic/models/load.py`, `prismatic/models/registry.py`, `prismatic/models/projectors.py`, `prismatic/models/materialize.py`
  - `deployment_policy`: `experiments/robot/server_deploy/deploy.py`, `experiments/robot/aloha/eval_files/deploy_server.sh`, `vla-scripts/deploy.py`, `experiments/robot/aloha/run_cobot_client.py`, `experiments/robot/aloha/run_fake_cobot_client.py`
  - `model_policy`: `prismatic/models/transformer_utils.py`, `prismatic/models/load.py`, `prismatic/models/registry.py`, `prismatic/models/projectors.py`, `prismatic/models/materialize.py`
  - `data`: `prismatic/vla/action_tokenizer.py`, `pretrained_models/configs/tokenizer.json`, `pretrained_models/configs/tokenizer_config.json`, `pretrained_models/configs/processor_config.json`, `experiments/robot/libero/regenerate_libero_dataset.py`
  - `env_robot_interface`: `vla-scripts/calvin_env_wrapper.py`, `prismatic/models/film_vit_wrapper.py`, `experiments/robot/robot_utils.py`, `experiments/robot/openvla_utils.py`, `experiments/robot/aloha/README.md`
  - `utils`: `prismatic/util/nn_utils.py`, `prismatic/util/data_utils.py`, `prismatic/util/torch_utils.py`, `prismatic/util/batching_utils.py`, `experiments/robot/robot_utils.py`
- Core model candidates:
  - `prismatic/models/transformer_utils.py`
  - `prismatic/models/load.py`
  - `prismatic/models/registry.py`
  - `prismatic/models/projectors.py`
  - `prismatic/models/materialize.py`
  - `prismatic/models/action_heads.py`
  - `prismatic/models/film_vit_wrapper.py`
  - `prismatic/models/vlas/openvla.py`
- Deployment/client policy candidates:
  - `experiments/robot/server_deploy/deploy.py`
  - `experiments/robot/aloha/eval_files/deploy_server.sh`
  - `vla-scripts/deploy.py`
  - `experiments/robot/aloha/run_cobot_client.py`
  - `experiments/robot/aloha/run_fake_cobot_client.py`
  - `experiments/robot/aloha/eval_files/run_eval_client.sh`
  - `experiments/robot/aloha/eval_files/run_eval_client_fake.sh`
- Model candidates:
  - `prismatic/models/transformer_utils.py`
  - `prismatic/models/load.py`
  - `prismatic/models/registry.py`
  - `prismatic/models/projectors.py`
  - `prismatic/models/materialize.py`
  - `prismatic/models/action_heads.py`
  - `prismatic/models/film_vit_wrapper.py`
  - `prismatic/models/vlas/openvla.py`
- Train candidates:
  - `experiments/robot/aloha/train_files/setup_training.sh`
  - `experiments/robot/aloha/train_files/train_aloha.sh`
  - `experiments/robot/aloha/train_files/download_models.sh`
  - `prismatic/training/train_utils.py`
  - `vla-scripts/train.py`
  - `experiments/robot/aloha/train_files/qwen25.py`
  - `experiments/robot/aloha/train_files/materialize_local_vision.py`
  - `experiments/robot/aloha/train_files/dinosiglip_vit_local_vision.py`
- Inference candidates:
  - `experiments/robot/aloha/eval_files/deploy_server.sh`
  - `experiments/robot/server_deploy/deploy.py`
  - `experiments/robot/aloha/eval_files/run_eval_client.sh`
  - `experiments/robot/aloha/eval_files/run_eval_client_fake.sh`
  - `vla-scripts/deploy.py`
  - `experiments/robot/libero/run_libero_eval.py`
- Config candidates:
  - `pretrained_models/configs/config.json`
  - `pretrained_models/configs/tokenizer_config.json`
  - `pretrained_models/configs/processor_config.json`
  - `pretrained_models/configs/generation_config.json`
  - `pretrained_models/configs/preprocessor_config.json`
  - `.pre-commit-config.yaml`
  - `pretrained_models/configs/vocab.json`
  - `pretrained_models/configs/tokenizer.json`
- Data candidates:
  - `prismatic/vla/action_tokenizer.py`
  - `pretrained_models/configs/tokenizer.json`
  - `pretrained_models/configs/tokenizer_config.json`
  - `pretrained_models/configs/processor_config.json`
  - `experiments/robot/libero/regenerate_libero_dataset.py`
  - `prismatic/vla/datasets/rlds/dataset.py`
  - `prismatic/util/data_utils.py`
  - `prismatic/vla/datasets/rlds/utils/data_utils.py`
- Env candidates:
  - `vla-scripts/calvin_env_wrapper.py`
  - `prismatic/models/film_vit_wrapper.py`
  - `experiments/robot/robot_utils.py`
  - `experiments/robot/openvla_utils.py`
  - `experiments/robot/aloha/README.md`
  - `experiments/robot/libero/libero_utils.py`
  - `experiments/robot/server_deploy/deploy.py`
  - `experiments/robot/libero/run_libero_eval.py`
- Utils candidates:
  - `prismatic/util/nn_utils.py`
  - `prismatic/util/data_utils.py`
  - `prismatic/util/torch_utils.py`
  - `prismatic/util/batching_utils.py`
  - `experiments/robot/robot_utils.py`
  - `prismatic/training/train_utils.py`
  - `experiments/robot/openvla_utils.py`
  - `prismatic/models/transformer_utils.py`
- Docs candidates:
  - `README.md`
  - `pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b/README.md`
  - `experiments/robot/aloha/README.md`
  - `our_envs.txt`
  - `vla_adapter.egg-info/SOURCES.txt`
  - `vla_adapter.egg-info/requires.txt`
  - `vla_adapter.egg-info/top_level.txt`
  - `vla_adapter.egg-info/dependency_links.txt`
- Entry candidates:
  - Candidate 1: `pretrained_models/configs/modeling_prismatic.py:293 - class PrismaticPreTrainedModel`
    - Evidence: `class PrismaticPreTrainedModel(PreTrainedModel):`
  - Candidate 2: `pretrained_models/configs/modeling_prismatic.py:733 - class OpenVLAForActionPrediction`
    - Evidence: `class OpenVLAForActionPrediction(PrismaticForConditionalGeneration):`
  - Candidate 3: `prismatic/extern/hf/modeling_prismatic.py:293 - class PrismaticPreTrainedModel`
    - Evidence: `class PrismaticPreTrainedModel(PreTrainedModel):`
  - Candidate 4: `prismatic/extern/hf/modeling_prismatic.py:733 - class OpenVLAForActionPrediction`
    - Evidence: `class OpenVLAForActionPrediction(PrismaticForConditionalGeneration):`
  - Candidate 5: `pretrained_models/configs/modeling_prismatic.py:71 - class PrismaticVisionBackbone`
    - Evidence: `class PrismaticVisionBackbone(nn.Module):`
  - Candidate 6: `pretrained_models/configs/modeling_prismatic.py:242 - class PrismaticProjector`
    - Evidence: `class PrismaticProjector(nn.Module):`
  - Candidate 7: `pretrained_models/configs/modeling_prismatic.py:279 - class PrismaticCausalLMOutputWithPast`
    - Evidence: `class PrismaticCausalLMOutputWithPast(ModelOutput):`
  - Candidate 8: `pretrained_models/configs/modeling_prismatic.py:331 - class PrismaticForConditionalGeneration`
    - Evidence: `class PrismaticForConditionalGeneration(PrismaticPreTrainedModel):`

## 4. 论文模块 -> 代码模块映射

### bridge attention

- Explanation: `bridge attention` has no direct symbol hit yet; start from the strongest architecture entry candidates.
- Evidence: `INFERRED`
- Code: `pretrained_models/configs/modeling_prismatic.py:293 - class PrismaticPreTrainedModel`
- Code: `pretrained_models/configs/modeling_prismatic.py:733 - class OpenVLAForActionPrediction`
- Code: `prismatic/extern/hf/modeling_prismatic.py:293 - class PrismaticPreTrainedModel`

## 5. 训练/推理主路径

### Training

- `scripts/pretrain.py:49 - class PretrainConfig`
- `scripts/pretrain.py:118 - def pretrain`
- `vla-scripts/finetune.py:494 - def save_training_checkpoint`
- `vla-scripts/train.py:47 - class TrainConfig`
- `vla-scripts/train.py:107 - def train`
- `pretrained_models/configs/modeling_prismatic.py:293 - class PrismaticPreTrainedModel`
- `prismatic/conf/models.py:302 - class Exp_7B_Vicuna_No_Cotraining`
- `prismatic/conf/models.py:307 - class Exp_7B_Llama2_No_Cotraining`

### Inference

- `vla-scripts/evaluate_calvin.py:205 - def evaluate_policy`
- `vla-scripts/evaluate_calvin.py:250 - def evaluate_sequence`
- `vla-scripts/finetune.py:288 - def run_forward_pass`
- `vla-scripts/vla_evaluation.py:189 - class DualSystemCalvinEvaluation`
- `experiments/robot/aloha/run_cobot_client.py:423 - def run_inference_loop`
- `experiments/robot/aloha/run_fake_cobot_client.py:200 - def run_inference_loop`
- `experiments/robot/libero/run_libero_eval.py:480 - def eval_libero`
- `experiments/robot/aloha/train_files/dinosiglip_vit_local_vision.py:186 - def forward`

## 6. 关注点专项

### bridge attention

- No direct code hit yet; keep this as a manual reading target.
- Evidence: `INFERRED`

## 7. 建议阅读顺序

1. `pretrained_models/configs/modeling_prismatic.py:293 - class PrismaticPreTrainedModel`
2. `pretrained_models/configs/modeling_prismatic.py:733 - class OpenVLAForActionPrediction`
3. `prismatic/extern/hf/modeling_prismatic.py:293 - class PrismaticPreTrainedModel`
4. `prismatic/extern/hf/modeling_prismatic.py:733 - class OpenVLAForActionPrediction`
5. `pretrained_models/configs/modeling_prismatic.py:71 - class PrismaticVisionBackbone`
6. `pretrained_models/configs/modeling_prismatic.py:242 - class PrismaticProjector`
7. `pretrained_models/configs/modeling_prismatic.py:279 - class PrismaticCausalLMOutputWithPast`
8. `pretrained_models/configs/modeling_prismatic.py:331 - class PrismaticForConditionalGeneration`
9. `scripts/pretrain.py:49 - class PretrainConfig`
10. `scripts/pretrain.py:118 - def pretrain`
11. `vla-scripts/finetune.py:494 - def save_training_checkpoint`
12. `vla-scripts/train.py:47 - class TrainConfig`

## 8. 未确认点

- [Missing Evidence] All requested concepts are currently inferred rather than directly confirmed in code.
- [Missing Evidence] `bridge attention` needs manual confirmation because no direct code hit was found.
- [Missing Evidence] Deployment/client policy files found; treat them as inference wrappers unless paper evidence suggests otherwise.
- [Missing Evidence] Core model files found, but deployment/client wrappers are also prominent. Prioritize core_model candidates for architecture analysis.
- [Missing Evidence] No obvious standalone loss/objective file found.
- [Missing Evidence] Loss/objective may be implemented inline in model/trainer/algorithm files.
- [Missing Evidence] Utils/helper files exist, but no focused hits were found in them yet.
