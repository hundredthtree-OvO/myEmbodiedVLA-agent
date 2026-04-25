# Create and activate conda environment 架构学习笔记

## 1. 任务与输入

- Paper: `.study-agent/repos/VLA-Adapter/README.md`
- Repository: `.study-agent/repos/VLA-Adapter`
- Focus: `architecture`
- Analysis mode: `paper-aligned`
- Engine: `offline`

## 2. 论文核心概念解释

### architecture

- Summary: `architecture` is user-specified or profile-prioritized; explain it by aligning paper claims with repository evidence.
- Evidence: `INFERRED`

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
- Architecture entry candidates:
  - `prismatic/models/vlms/base_vlm.py`
  - `prismatic/models/vlas/openvla.py`
  - `prismatic/models/vlms/prismatic.py`
  - `prismatic/models/load.py`
  - `prismatic/vla/constants.py`
  - `prismatic/vla/materialize.py`
  - `prismatic/models/registry.py`
  - `prismatic/models/projectors.py`
- Config entry candidates:
  - `prismatic/conf/vla.py`
  - `prismatic/conf/models.py`
  - `prismatic/conf/datasets.py`
  - `prismatic/conf/__init__.py`
  - `pyproject.toml`
  - `vla-scripts/enrich_lang_annotations.json`
  - `.pre-commit-config.yaml`
- Deployment entry candidates:
  - `experiments/robot/server_deploy/deploy.py`
  - `experiments/robot/aloha/eval_files/deploy_server.sh`
  - `vla-scripts/deploy.py`
  - `experiments/robot/aloha/run_cobot_client.py`
  - `experiments/robot/aloha/run_fake_cobot_client.py`
  - `experiments/robot/aloha/eval_files/run_eval_client.sh`
  - `experiments/robot/aloha/eval_files/run_eval_client_fake.sh`
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
  - Candidate 1: `prismatic/models/vlms/base_vlm.py:31 - class VLM`
    - Evidence: `class VLM(nn.Module, GenerationMixin, ABC):`
  - Candidate 2: `prismatic/models/vlas/openvla.py:24 - class OpenVLA`
    - Evidence: `class OpenVLA(PrismaticVLM):`
  - Candidate 3: `prismatic/models/vlms/prismatic.py:38 - class PrismaticVLM`
    - Evidence: `class PrismaticVLM(VLM):`
  - Candidate 4: `prismatic/models/load.py:33 - def available_models`
    - Evidence: `def available_models() -> List[str]:`
  - Candidate 5: `prismatic/vla/constants.py:19 - class NormalizationType`
    - Evidence: `class NormalizationType(str, Enum):`
  - Candidate 6: `prismatic/vla/materialize.py:21 - def get_vla_dataset_and_collator`
    - Evidence: `def get_vla_dataset_and_collator(`
  - Candidate 7: `prismatic/models/registry.py:4 - file registry`
    - Evidence: `Exhaustive list of pretrained VLMs (with full descriptions / links to corresponding names and sections of paper).`
  - Candidate 8: `prismatic/models/projectors.py:6 - class ProprioProjector`
    - Evidence: `class ProprioProjector(nn.Module):`
- Candidate reason debug:
  - `architecture_entry` :: `prismatic/models/vlms/base_vlm.py` => architecture_entry:core_model_group, architecture_entry:model_namespace, architecture_entry:vla_namespace, architecture_entry:assembly_filename, architecture_entry:assembly_token:vlm
  - `architecture_entry` :: `prismatic/models/vlas/openvla.py` => architecture_entry:core_model_group, architecture_entry:model_namespace, architecture_entry:vla_namespace
  - `architecture_entry` :: `prismatic/models/vlms/prismatic.py` => architecture_entry:core_model_group, architecture_entry:model_namespace, architecture_entry:vla_namespace
  - `config_entry` :: `prismatic/conf/vla.py` => architecture_entry:assembly_token:vla, architecture_entry:project_stem_match:vla, config_entry:conf_namespace
  - `config_entry` :: `prismatic/conf/models.py` => config_entry:conf_namespace
  - `config_entry` :: `prismatic/conf/datasets.py` => config_entry:conf_namespace
  - `deployment_entry` :: `experiments/robot/server_deploy/deploy.py` => deployment_entry:deployment_group, deployment_entry:deployment_token:deploy, deployment_entry:deployment_token:server
  - `deployment_entry` :: `experiments/robot/aloha/eval_files/deploy_server.sh` => deployment_entry:deployment_group, deployment_entry:deployment_token:deploy, deployment_entry:deployment_token:server
  - `deployment_entry` :: `vla-scripts/deploy.py` => architecture_entry:assembly_token:vla, architecture_entry:project_stem_match:vla, deployment_entry:deployment_group, deployment_entry:deployment_token:deploy

## 4. 论文模块 -> 代码模块映射

### architecture

- Explanation: `architecture` has direct repository evidence in the files listed below.
- Evidence: `CONFIRMED`
- Code: `README.md:211 - We use the `Prismatic-VLMs` architecture. Since the file is large, please download it from [here](https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b). Then put it in the `/pretrained_models` folder. The file stru`
- Code: `README.md:242 - The VLM in the VLA-Adapter uses the Prismatic-VLMs architecture, with the LLM backbone being `Qwen2.5-0.5B`. You can download it from https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b and place it in `/pretraine`
- Code: `README.md:298 - The VLM in the VLA-Adapter uses the Prismatic-VLMs architecture, with the LLM backbone being `Qwen2.5-0.5B`. You can download it from https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b and place it in `/pretraine`
- Code: `README.md:358 - The VLM in the VLA-Adapter uses the Prismatic-VLMs architecture, with the LLM backbone being `Qwen2.5-0.5B`. You can download it from https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b and place it in `/pretraine`
- Code: `README.md:418 - The VLM in the VLA-Adapter uses the Prismatic-VLMs architecture, with the LLM backbone being `Qwen2.5-0.5B`. You can download it from https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b and place it in `/pretraine`

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

### architecture

- `README.md:211` - We use the `Prismatic-VLMs` architecture. Since the file is large, please download it from [here](https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b). Then put it in the `/pretrained_models` folder. The file stru
- `README.md:242` - The VLM in the VLA-Adapter uses the Prismatic-VLMs architecture, with the LLM backbone being `Qwen2.5-0.5B`. You can download it from https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b and place it in `/pretraine
- `README.md:298` - The VLM in the VLA-Adapter uses the Prismatic-VLMs architecture, with the LLM backbone being `Qwen2.5-0.5B`. You can download it from https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b and place it in `/pretraine
- `README.md:358` - The VLM in the VLA-Adapter uses the Prismatic-VLMs architecture, with the LLM backbone being `Qwen2.5-0.5B`. You can download it from https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b and place it in `/pretraine
- `README.md:418` - The VLM in the VLA-Adapter uses the Prismatic-VLMs architecture, with the LLM backbone being `Qwen2.5-0.5B`. You can download it from https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b and place it in `/pretraine
- Evidence: `CONFIRMED`

## 7. 建议阅读顺序

1. `prismatic/models/vlms/base_vlm.py:1 - file base_vlm`
2. `prismatic/models/vlas/openvla.py:1 - file openvla`
3. `prismatic/models/vlms/prismatic.py:1 - file prismatic`
4. `prismatic/models/load.py:33 - def available_models`
5. `prismatic/vla/constants.py:1 - file constants`
6. `prismatic/models/transformer_utils.py:33 - class RGBDFuser`
7. `prismatic/models/registry.py:1 - file registry`
8. `prismatic/models/projectors.py:6 - class ProprioProjector`
9. `prismatic/models/materialize.py:85 - def get_vision_backbone_and_transform`
10. `experiments/robot/aloha/train_files/setup_training.sh:1 - file setup_training`
11. `experiments/robot/aloha/train_files/train_aloha.sh:1 - file train_aloha`
12. `prismatic/conf/vla.py:21 - class VLAConfig`

## 8. 未确认点

- [Missing Evidence] Deployment/client policy files found; treat them as inference wrappers unless paper evidence suggests otherwise.
- [Missing Evidence] Core model files found, but deployment/client wrappers are also prominent. Prioritize core_model candidates for architecture analysis.
- [Missing Evidence] No obvious standalone loss/objective file found.
- [Missing Evidence] Loss/objective may be implemented inline in model/trainer/algorithm files.
- [Missing Evidence] Utils/helper files exist, but no focused hits were found in them yet.
