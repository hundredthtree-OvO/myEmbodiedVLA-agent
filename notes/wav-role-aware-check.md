# World-Value-Action Model: Implicit Planning for Vision-Language-Action Systems 架构学习笔记

## 1. 任务与输入

- Paper: `.study-agent/repos/WAV/README.md`
- Repository: `.study-agent/repos/WAV`
- Focus: `architecture`
- Analysis mode: `paper-aligned`
- Engine: `offline`

## 2. 论文核心概念解释

### architecture

- Summary: `architecture` appears in the paper material and should be treated as a primary reading target.
- Evidence: `CONFIRMED`

## 3. 仓库入口与主干候选

- Scanned files: `74`
- File groups:
  - `docs`: `README.md`, `requirements.txt`
  - `train_scripts`: `scripts/train.sh`, `runner/trainer.py`
  - `inference_scripts`: `web_infer_scripts/real_deploy.sh`, `web_infer_scripts/run_server.sh`, `web_infer_utils/Real_deploy.py`, `scripts/infer.sh`, `web_infer_utils/server.py`
  - `configs`: `configs/ltx_model/libero/video_model_libero.yaml`, `configs/ltx_model/libero/value_model_libero.yaml`, `configs/ltx_model/libero/action_model_libero.yaml`, `configs/ltx_model/drawer_task/video_model_real.yaml`, `configs/ltx_model/drawer_task/value_model_real.yaml`
  - `core_model`: `models/action_patches/patches.py`, `models/pipeline/custom_pipeline.py`, `models/value_patches/value_patches.py`, `models/ltx_models/autoencoder_kl_ltx.py`, `models/ltx_models/ltx_attention_processor.py`
  - `deployment_policy`: `web_infer_utils/openpi_client/websocket_client_policy.py`, `web_infer_utils/openpi_client/runtime/agents/policy_agent.py`, `web_infer_utils/openpi_client/runtime/agent.py`, `web_infer_utils/openpi_client/runtime/runtime.py`, `web_infer_utils/openpi_client/runtime/subscriber.py`
  - `model_policy`: `web_infer_utils/openpi_client/runtime/agents/policy_agent.py`, `models/action_patches/patches.py`, `models/pipeline/custom_pipeline.py`, `models/value_patches/value_patches.py`, `web_infer_utils/openpi_client/base_policy.py`
  - `loss_objective`: `utils/dreamer_style_loss.py`
  - `data`: `data/libero_dataset.py`, `data/lerobot_like_dataset.py`, `models/ltx_models/ltx_attention_processor.py`, `utils/data_utils.py`, `data/utils/utils.py`
  - `env_robot_interface`: `utils/calvin_env_wrapper.py`, `utils/libero_sim_utils.py`, `web_infer_utils/openpi_client/runtime/environment.py`
  - `utils`: `utils/data_utils.py`, `utils/model_utils.py`, `utils/extra_utils.py`, `utils/memory_utils.py`, `utils/get_ray_maps.py`
- Architecture entry candidates:
  - `models/action_patches/patches.py`
  - `models/pipeline/custom_pipeline.py`
  - `models/value_patches/value_patches.py`
  - `models/ltx_models/autoencoder_kl_ltx.py`
  - `models/ltx_models/ltx_attention_processor.py`
  - `models/ltx_models/transformer_ltx_multiview.py`
  - `utils/model_utils.py`
  - `web_infer_utils/openpi_client/base_policy.py`
- Config entry candidates:
  - `configs/ltx_model/libero/video_model_libero.yaml`
  - `configs/ltx_model/libero/value_model_libero.yaml`
  - `configs/ltx_model/libero/action_model_libero.yaml`
  - `configs/ltx_model/drawer_task/video_model_real.yaml`
  - `configs/ltx_model/drawer_task/value_model_real.yaml`
  - `configs/ltx_model/flatten_towel/video_model_real.yaml`
  - `configs/ltx_model/flatten_towel/value_model_real.yaml`
  - `configs/ltx_model/orangize_bowls/video_model_real.yaml`
- Deployment entry candidates:
  - `web_infer_utils/openpi_client/runtime/subscriber.py`
  - `web_infer_utils/openpi_client/runtime/agent.py`
  - `web_infer_utils/openpi_client/runtime/runtime.py`
  - `web_infer_utils/openpi_client/runtime/environment.py`
  - `web_infer_utils/openpi_client/runtime/agents/policy_agent.py`
  - `web_infer_utils/openpi_client/websocket_client_policy.py`
  - `web_infer_utils/openpi_client/image_tools.py`
  - `web_infer_utils/openpi_client/base_policy.py`
- Core model candidates:
  - `models/action_patches/patches.py`
  - `models/pipeline/custom_pipeline.py`
  - `models/value_patches/value_patches.py`
  - `models/ltx_models/autoencoder_kl_ltx.py`
  - `models/ltx_models/ltx_attention_processor.py`
  - `models/ltx_models/transformer_ltx_multiview.py`
  - `models/value_patches/__init__.py`
  - `models/action_patches/__init__.py`
- Deployment/client policy candidates:
  - `web_infer_utils/openpi_client/websocket_client_policy.py`
  - `web_infer_utils/openpi_client/runtime/agents/policy_agent.py`
  - `web_infer_utils/openpi_client/runtime/agent.py`
  - `web_infer_utils/openpi_client/runtime/runtime.py`
  - `web_infer_utils/openpi_client/runtime/subscriber.py`
  - `web_infer_utils/openpi_client/runtime/environment.py`
  - `web_infer_utils/openpi_client/base_policy.py`
  - `web_infer_utils/openpi_client/image_tools.py`
- Model candidates:
  - `models/action_patches/patches.py`
  - `models/pipeline/custom_pipeline.py`
  - `models/value_patches/value_patches.py`
  - `models/ltx_models/autoencoder_kl_ltx.py`
  - `models/ltx_models/ltx_attention_processor.py`
  - `models/ltx_models/transformer_ltx_multiview.py`
  - `models/value_patches/__init__.py`
  - `models/action_patches/__init__.py`
- Train candidates:
  - `scripts/train.sh`
  - `runner/trainer.py`
- Inference candidates:
  - `web_infer_scripts/real_deploy.sh`
  - `web_infer_scripts/run_server.sh`
  - `web_infer_utils/Real_deploy.py`
  - `scripts/infer.sh`
  - `web_infer_utils/server.py`
  - `experiments/eval_libero.sh`
  - `web_infer_scripts/main_server.py`
  - `web_infer_scripts/run_simple_client.sh`
- Config candidates:
  - `configs/ltx_model/libero/video_model_libero.yaml`
  - `configs/ltx_model/libero/value_model_libero.yaml`
  - `configs/ltx_model/libero/action_model_libero.yaml`
  - `configs/ltx_model/drawer_task/video_model_real.yaml`
  - `configs/ltx_model/drawer_task/value_model_real.yaml`
  - `configs/ltx_model/flatten_towel/video_model_real.yaml`
  - `configs/ltx_model/flatten_towel/value_model_real.yaml`
  - `configs/ltx_model/orangize_bowls/video_model_real.yaml`
- Loss candidates:
  - `utils/dreamer_style_loss.py`
- Data candidates:
  - `data/libero_dataset.py`
  - `data/lerobot_like_dataset.py`
  - `models/ltx_models/ltx_attention_processor.py`
  - `utils/data_utils.py`
  - `data/utils/utils.py`
  - `data/utils/statistics.py`
  - `data/utils/get_actions.py`
  - `data/utils/domain_table.py`
- Env candidates:
  - `utils/calvin_env_wrapper.py`
  - `utils/libero_sim_utils.py`
  - `web_infer_utils/openpi_client/runtime/environment.py`
- Utils candidates:
  - `utils/data_utils.py`
  - `utils/model_utils.py`
  - `utils/extra_utils.py`
  - `utils/memory_utils.py`
  - `utils/get_ray_maps.py`
  - `utils/get_traj_maps.py`
  - `utils/geometry_utils.py`
  - `utils/optimizer_utils.py`
- Docs candidates:
  - `README.md`
  - `requirements.txt`
- Entry candidates:
  - Candidate 1: `models/action_patches/patches.py:12 - class ActionRotaryPosEmbed`
    - Evidence: `class ActionRotaryPosEmbed(nn.Module):`
  - Candidate 2: `models/pipeline/custom_pipeline.py:50 - class CustomPipelineOutput`
    - Evidence: `class CustomPipelineOutput(BaseOutput):`
  - Candidate 3: `models/value_patches/value_patches.py:13 - class ValueRotaryPosEmbed`
    - Evidence: `class ValueRotaryPosEmbed(nn.Module):`
  - Candidate 4: `models/ltx_models/autoencoder_kl_ltx.py:32 - class LTXVideoCausalConv3d`
    - Evidence: `class LTXVideoCausalConv3d(nn.Module):`
  - Candidate 5: `models/ltx_models/ltx_attention_processor.py:49 - class Attention`
    - Evidence: `class Attention(nn.Module):`
  - Candidate 6: `models/ltx_models/transformer_ltx_multiview.py:46 - class LTXVideoAttentionProcessor2_0`
    - Evidence: `class LTXVideoAttentionProcessor2_0:`
  - Candidate 7: `utils/model_utils.py:13 - def unwrap_model`
    - Evidence: `def unwrap_model(accelerator: Accelerator, model):`
  - Candidate 8: `web_infer_utils/openpi_client/base_policy.py:5 - class BasePolicy`
    - Evidence: `class BasePolicy(abc.ABC):`
- Candidate reason debug:
  - `architecture_entry` :: `models/action_patches/patches.py` => architecture_entry:core_model_group, architecture_entry:model_namespace
  - `architecture_entry` :: `models/pipeline/custom_pipeline.py` => architecture_entry:core_model_group, architecture_entry:model_namespace
  - `architecture_entry` :: `models/value_patches/value_patches.py` => architecture_entry:core_model_group, architecture_entry:model_namespace
  - `config_entry` :: `configs/ltx_model/libero/video_model_libero.yaml` => architecture_entry:assembly_token:model, config_entry:config_group
  - `config_entry` :: `configs/ltx_model/libero/value_model_libero.yaml` => architecture_entry:assembly_token:model, config_entry:config_group
  - `config_entry` :: `configs/ltx_model/libero/action_model_libero.yaml` => architecture_entry:assembly_token:model, config_entry:config_group
  - `deployment_entry` :: `web_infer_utils/openpi_client/runtime/subscriber.py` => deployment_entry:deployment_group, deployment_entry:runtime_namespace, deployment_entry:deployment_token:client, deployment_entry:deployment_token:runtime, deployment_entry:deployment_token:subscriber
  - `deployment_entry` :: `web_infer_utils/openpi_client/runtime/agent.py` => deployment_entry:deployment_group, deployment_entry:runtime_namespace, deployment_entry:deployment_token:client, deployment_entry:deployment_token:runtime
  - `deployment_entry` :: `web_infer_utils/openpi_client/runtime/runtime.py` => deployment_entry:deployment_group, deployment_entry:runtime_namespace, deployment_entry:deployment_token:client, deployment_entry:deployment_token:runtime

## 4. 论文模块 -> 代码模块映射

### architecture

- Explanation: `architecture` has direct repository evidence in the files listed below.
- Evidence: `CONFIRMED`
- Code: `README.md:40 - ### Architecture`

## 5. 训练/推理主路径

### Training

- `runner/trainer.py:91 - class Trainer`
- `runner/trainer.py:358 - def prepare_trainable_parameters`
- `runner/trainer.py:481 - def prepare_for_training`
- `runner/trainer.py:493 - def train`
- `utils/dreamer_style_loss.py:51 - def dreamer_twohot_loss`

### Inference

- `experiments/eval_libero.py:69 - class InferenceLibero`
- `runner/inferencer.py:45 - class Inferencer`
- `utils/model_utils.py:163 - def forward_pass`
- `web_infer_utils/Real_deploy.py:98 - def predict`
- `web_infer_utils/Real_deploy.py:131 - def predict`
- `models/action_patches/patches.py:25 - def forward`
- `models/action_patches/patches.py:133 - def forward`
- `models/ltx_models/autoencoder_kl_ltx.py:68 - def forward`

## 6. 关注点专项

### architecture

- `README.md:40` - ### Architecture
- Evidence: `CONFIRMED`

## 7. 建议阅读顺序

1. `models/action_patches/patches.py:12 - class ActionRotaryPosEmbed`
2. `models/pipeline/custom_pipeline.py:50 - class CustomPipelineOutput`
3. `models/value_patches/value_patches.py:13 - class ValueRotaryPosEmbed`
4. `models/ltx_models/autoencoder_kl_ltx.py:32 - class LTXVideoCausalConv3d`
5. `models/ltx_models/ltx_attention_processor.py:49 - class Attention`
6. `scripts/train.sh:1 - file train`
7. `runner/trainer.py:70 - class State`
8. `configs/ltx_model/libero/video_model_libero.yaml:1 - file video_model_libero`
9. `configs/ltx_model/libero/value_model_libero.yaml:1 - file value_model_libero`
10. `web_infer_utils/openpi_client/runtime/subscriber.py:4 - class Subscriber`
11. `web_infer_utils/openpi_client/runtime/agent.py:4 - class Agent`

## 8. 未确认点

- [Missing Evidence] Deployment/client policy files found; treat them as inference wrappers unless paper evidence suggests otherwise.
- [Missing Evidence] Core model files found, but deployment/client wrappers are also prominent. Prioritize core_model candidates for architecture analysis.
- [Missing Evidence] Utils/helper files exist, but no focused hits were found in them yet.
