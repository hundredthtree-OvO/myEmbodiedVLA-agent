# ACoT-VLA 架构学习笔记

## 1. 任务与输入

- Paper: `notes\ACoT-VLA-architecture-study.md`
- Repository: `E:\my-embodied\.study-agent\repos\ACoT-VLA`
- Focus: `architecture`
- Analysis mode: `paper-aligned`
- Engine: `offline`

## 2. 论文核心概念解释

### architecture

- Summary: `architecture` is user-specified or profile-prioritized; explain it by aligning paper claims with repository evidence.
- Evidence: `INFERRED`

## 3. 仓库入口与主干候选

- Scanned files: `117`
- File groups:
  - `docs`: `README.md`, `examples/ur5/README.md`, `examples/droid/README.md`, `examples/libero/README.md`, `examples/aloha_sim/README.md`
  - `train_scripts`: `scripts/train.sh`, `scripts/train.py`, `examples/droid/README_train.md`, `src/openpi/training/utils.py`, `src/openpi/training/config.py`
  - `inference_scripts`: `scripts/eval_on_libero.sh`, `scripts/eval_on_libero_plus.py`, `scripts/serve_policy.py`
  - `configs`: `.pre-commit-config.yaml`, `src/openpi/training/config.py`, `src/openpi/policies/policy_config.py`, `pyproject.toml`, `scripts/docker/compose.yml`
  - `core_model`: `src/openpi/models/vit.py`, `src/openpi/models/pi0.py`, `src/openpi/models/lora.py`, `src/openpi/models/model.py`, `src/openpi/models/gemma.py`
  - `deployment_policy`: `packages/openpi-client/src/openpi_client/websocket_client_policy.py`, `packages/openpi-client/src/openpi_client/runtime/agents/policy_agent.py`, `src/openpi/serving/websocket_policy_server.py`, `packages/openpi-client/src/openpi_client/runtime/agent.py`, `packages/openpi-client/src/openpi_client/runtime/runtime.py`
  - `model_policy`: `packages/openpi-client/src/openpi_client/runtime/agents/policy_agent.py`, `scripts/serve_policy.py`, `examples/policy_records.ipynb`, `src/openpi/policies/policy.py`, `src/openpi/policies/go2_policy.py`
  - `data`: `src/openpi/models/tokenizer.py`, `src/openpi/models/tokenizer_test.py`, `src/openpi/training/droid_rlds_dataset.py`, `src/openpi/training/data_loader.py`, `src/openpi/training/data_loader_test.py`
  - `env_robot_interface`: `examples/aloha_sim/env.py`, `examples/aloha_sim/main.py`, `examples/aloha_real/env.py`, `examples/aloha_sim/saver.py`, `examples/aloha_sim/README.md`
  - `utils`: `examples/aloha_real/robot_utils.py`, `src/openpi/training/utils.py`, `src/openpi/shared/nnx_utils.py`
- Core model candidates:
  - `src/openpi/models/vit.py`
  - `src/openpi/models/pi0.py`
  - `src/openpi/models/lora.py`
  - `src/openpi/models/model.py`
  - `src/openpi/models/gemma.py`
  - `src/openpi/models/siglip.py`
  - `src/openpi/models/pi0_test.py`
  - `src/openpi/models/pi0_fast.py`
- Deployment/client policy candidates:
  - `packages/openpi-client/src/openpi_client/websocket_client_policy.py`
  - `packages/openpi-client/src/openpi_client/runtime/agents/policy_agent.py`
  - `src/openpi/serving/websocket_policy_server.py`
  - `packages/openpi-client/src/openpi_client/runtime/agent.py`
  - `packages/openpi-client/src/openpi_client/runtime/runtime.py`
  - `packages/openpi-client/src/openpi_client/runtime/subscriber.py`
  - `packages/openpi-client/src/openpi_client/runtime/environment.py`
  - `packages/openpi-client/src/openpi_client/base_policy.py`
- Model candidates:
  - `src/openpi/models/vit.py`
  - `src/openpi/models/pi0.py`
  - `src/openpi/models/lora.py`
  - `src/openpi/models/model.py`
  - `src/openpi/models/gemma.py`
  - `src/openpi/models/siglip.py`
  - `src/openpi/models/pi0_test.py`
  - `src/openpi/models/pi0_fast.py`
- Train candidates:
  - `scripts/train.sh`
  - `scripts/train.py`
  - `examples/droid/README_train.md`
  - `src/openpi/training/utils.py`
  - `src/openpi/training/config.py`
  - `src/openpi/training/sampler.py`
  - `src/openpi/training/sharding.py`
  - `src/openpi/training/optimizer.py`
- Inference candidates:
  - `scripts/eval_on_libero.sh`
  - `scripts/eval_on_libero_plus.py`
  - `scripts/serve_policy.py`
- Config candidates:
  - `.pre-commit-config.yaml`
  - `src/openpi/training/config.py`
  - `src/openpi/policies/policy_config.py`
  - `pyproject.toml`
  - `scripts/docker/compose.yml`
  - `.github/workflows/test.yml`
  - `examples/libero/compose.yml`
  - `examples/aloha_sim/compose.yml`
- Data candidates:
  - `src/openpi/models/tokenizer.py`
  - `src/openpi/models/tokenizer_test.py`
  - `src/openpi/training/droid_rlds_dataset.py`
  - `src/openpi/training/data_loader.py`
  - `src/openpi/training/data_loader_test.py`
  - `examples/droid/convert_droid_data_to_lerobot.py`
  - `examples/libero/convert_libero_data_to_lerobot.py`
  - `examples/aloha_real/convert_aloha_data_to_lerobot.py`
- Env candidates:
  - `examples/aloha_sim/env.py`
  - `examples/aloha_sim/main.py`
  - `examples/aloha_real/env.py`
  - `examples/aloha_sim/saver.py`
  - `examples/aloha_sim/README.md`
  - `examples/aloha_sim/compose.yml`
  - `examples/aloha_real/real_env.py`
  - `examples/aloha_sim/requirements.txt`
- Utils candidates:
  - `examples/aloha_real/robot_utils.py`
  - `src/openpi/training/utils.py`
  - `src/openpi/shared/nnx_utils.py`
- Docs candidates:
  - `README.md`
  - `examples/ur5/README.md`
  - `examples/droid/README.md`
  - `examples/libero/README.md`
  - `examples/aloha_sim/README.md`
  - `examples/aloha_real/README.md`
  - `examples/droid/README_train.md`
  - `examples/simple_client/README.md`
- Entry candidates:
  - Candidate 1: `src/openpi/training/config.py:114 - class ModelTransformFactory`
    - Evidence: `class ModelTransformFactory(GroupFactory):`
  - Candidate 2: `src/openpi/training/config.py:408 - class LeRobotVLABenchDataConfig`
    - Evidence: `class LeRobotVLABenchDataConfig(DataConfigFactory):`
  - Candidate 3: `src/openpi/training/config.py:451 - class LeRobotACOTVLABenchDataConfig`
    - Evidence: `class LeRobotACOTVLABenchDataConfig(DataConfigFactory):`
  - Candidate 4: `src/openpi/training/config.py:43 - class AssetsConfig`
    - Evidence: `class AssetsConfig:`
  - Candidate 5: `src/openpi/training/config.py:70 - class DataConfig`
    - Evidence: `class DataConfig:`
  - Candidate 6: `src/openpi/training/config.py:108 - class GroupFactory`
    - Evidence: `class GroupFactory(Protocol):`
  - Candidate 7: `src/openpi/training/config.py:191 - class DataConfigFactory`
    - Evidence: `class DataConfigFactory(abc.ABC):`
  - Candidate 8: `src/openpi/training/config.py:254 - class FakeDataConfig`
    - Evidence: `class FakeDataConfig(DataConfigFactory):`

## 4. 论文模块 -> 代码模块映射

### architecture

- Explanation: `architecture` has no direct symbol hit yet; start from the strongest architecture entry candidates.
- Evidence: `INFERRED`
- Code: `src/openpi/training/config.py:114 - class ModelTransformFactory`
- Code: `src/openpi/training/config.py:408 - class LeRobotVLABenchDataConfig`
- Code: `src/openpi/training/config.py:451 - class LeRobotACOTVLABenchDataConfig`

## 5. 训练/推理主路径

### Training

- `scripts/train.py:85 - def init_train_state`
- `scripts/train.py:137 - def train_step`
- `scripts/train.py:147 - def loss_fn`
- `scripts/train.py:194 - def acot_train_step`
- `scripts/train.py:204 - def loss_fn`
- `src/openpi/models/acot_vla.py:695 - def compute_loss`
- `src/openpi/models/model.py:278 - def compute_loss`
- `src/openpi/models/pi0.py:292 - def compute_loss`

### Inference

- `scripts/eval_on_libero_plus.py:50 - def eval_libero`
- `examples/libero/main.py:54 - def eval_libero`
- `src/openpi/transforms.py:206 - class SubsampleActions`
- `src/openpi/models/acot_vla.py:156 - class DownsampleExtractor`
- `src/openpi/models/acot_vla.py:795 - def sample_actions`
- `src/openpi/models/gemma.py:300 - class FeedForward`
- `src/openpi/models/lora.py:88 - class FeedForward`
- `src/openpi/models/model.py:288 - def sample_actions`

## 6. 关注点专项

### architecture

- No direct code hit yet; keep this as a manual reading target.
- Evidence: `INFERRED`

## 7. 建议阅读顺序

1. `src/openpi/training/config.py:114 - class ModelTransformFactory`
2. `src/openpi/training/config.py:408 - class LeRobotVLABenchDataConfig`
3. `src/openpi/training/config.py:451 - class LeRobotACOTVLABenchDataConfig`
4. `src/openpi/training/config.py:43 - class AssetsConfig`
5. `src/openpi/training/config.py:70 - class DataConfig`
6. `src/openpi/training/config.py:108 - class GroupFactory`
7. `src/openpi/training/config.py:191 - class DataConfigFactory`
8. `src/openpi/training/config.py:254 - class FakeDataConfig`
9. `scripts/train.py:85 - def init_train_state`
10. `scripts/train.py:137 - def train_step`
11. `scripts/train.py:147 - def loss_fn`
12. `scripts/train.py:194 - def acot_train_step`

## 8. 未确认点

- [Missing Evidence] All requested concepts are currently inferred rather than directly confirmed in code.
- [Missing Evidence] `architecture` needs manual confirmation because no direct code hit was found.
- [Missing Evidence] Deployment/client policy files found; treat them as inference wrappers unless paper evidence suggests otherwise.
- [Missing Evidence] Core model files found, but deployment/client wrappers are also prominent. Prioritize core_model candidates for architecture analysis.
- [Missing Evidence] No obvious standalone loss/objective file found.
- [Missing Evidence] Loss/objective may be implemented inline in model/trainer/algorithm files.
- [Missing Evidence] Utils/helper files exist, but no focused hits were found in them yet.
