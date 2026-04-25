# Li 等 - 2026 - World-Value-Action Model Implicit Planning for Vision-Language-Action Systems 架构学习笔记

## 1. 任务与输入

- Paper: `E:\zoteroData\storage\GUIZJK5Z\Li 等 - 2026 - World-Value-Action Model Implicit Planning for Vision-Language-Action Systems.pdf`
- Repository: `https://github.com/Win-commit/WAV`
- Focus: `Latent Planning and Iterative Inference`
- Analysis mode: `paper-aligned`
- Engine: `offline`

## 2. 论文核心概念解释

### Latent Planning and Iterative Inference

- Summary: `Latent Planning and Iterative Inference` is user-specified or profile-prioritized; explain it by aligning paper claims with repository evidence.
- Evidence: `INFERRED`

## 3. 仓库入口与主干候选

- Scanned files: `68`
- File groups:
  - `docs`: `README.md`, `requirements.txt`
  - `train_scripts`: `runner/trainer.py`
  - `inference_scripts`: `web_infer_utils/server.py`, `web_infer_utils/Real_deploy.py`, `web_infer_scripts/main_server.py`, `runner/inferencer.py`, `web_infer_utils/MVActor.py`
  - `configs`: `configs/ltx_model/libero/video_model_libero.yaml`, `configs/ltx_model/libero/value_model_libero.yaml`, `configs/ltx_model/libero/action_model_libero.yaml`, `configs/ltx_model/drawer_task/video_model_real.yaml`, `configs/ltx_model/drawer_task/value_model_real.yaml`
  - `model_policy`: `models/ltx_models/autoencoder_kl_ltx.py`, `models/__init__.py`, `models/ltx_models/__init__.py`, `models/value_patches/__init__.py`, `models/action_patches/patches.py`
  - `loss_objective`: `utils/dreamer_style_loss.py`
  - `data`: `data/libero_dataset.py`, `data/lerobot_like_dataset.py`, `data/__init__.py`, `utils/data_utils.py`, `data/utils/utils.py`
  - `env_robot_interface`: `utils/calvin_env_wrapper.py`, `web_infer_utils/openpi_client/runtime/environment.py`, `utils/libero_sim_utils.py`, `data/lerobot_like_dataset.py`, `web_infer_scripts/simple_client.py`
  - `utils`: `utils/__init__.py`, `utils/data_utils.py`, `utils/model_utils.py`, `utils/extra_utils.py`, `utils/memory_utils.py`
- Model candidates:
  - `models/ltx_models/autoencoder_kl_ltx.py`
  - `models/__init__.py`
  - `models/ltx_models/__init__.py`
  - `models/value_patches/__init__.py`
  - `models/action_patches/patches.py`
  - `models/action_patches/__init__.py`
  - `models/pipeline/custom_pipeline.py`
  - `models/value_patches/value_patches.py`
- Train candidates:
  - `runner/trainer.py`
- Inference candidates:
  - `web_infer_utils/server.py`
  - `web_infer_utils/Real_deploy.py`
  - `web_infer_scripts/main_server.py`
  - `runner/inferencer.py`
  - `web_infer_utils/MVActor.py`
  - `experiments/eval_libero.py`
  - `web_infer_utils/__init__.py`
  - `web_infer_scripts/simple_client.py`
- Config candidates:
  - `configs/ltx_model/libero/video_model_libero.yaml`
  - `configs/ltx_model/libero/value_model_libero.yaml`
  - `configs/ltx_model/libero/action_model_libero.yaml`
  - `configs/ltx_model/drawer_task/video_model_real.yaml`
  - `configs/ltx_model/drawer_task/value_model_real.yaml`
  - `configs/ltx_model/flatten_towel/video_model_real.yaml`
  - `configs/ltx_model/flatten_towel/value_model_real.yaml`
  - `configs/ltx_model/orangize_bowls/video_model_real.yaml`
- Data candidates:
  - `data/libero_dataset.py`
  - `data/lerobot_like_dataset.py`
  - `data/__init__.py`
  - `utils/data_utils.py`
  - `data/utils/utils.py`
  - `data/utils/__init__.py`
  - `data/utils/statistics.py`
  - `data/utils/get_actions.py`
- Entry candidates:
  - Candidate 1: `runner/trainer.py:282 - def prepare_models`
    - Evidence: `def prepare_models(self):`
  - Candidate 2: `runner/trainer.py:70 - class State`
    - Evidence: `class State:`
  - Candidate 3: `runner/trainer.py:91 - class Trainer`
    - Evidence: `class Trainer:`
  - Candidate 4: `runner/trainer.py:93 - def __init__`
    - Evidence: `def __init__(self, config_file, to_log=True, output_dir=None) -> None:`
  - Candidate 5: `runner/trainer.py:158 - def _init_distributed`
    - Evidence: `def _init_distributed(self):`
  - Candidate 6: `runner/trainer.py:210 - def _init_logging`
    - Evidence: `def _init_logging(self):`
  - Candidate 7: `runner/trainer.py:227 - def _init_directories_and_repositories`
    - Evidence: `def _init_directories_and_repositories(self):`
  - Candidate 8: `runner/trainer.py:234 - def prepare_dataset`
    - Evidence: `def prepare_dataset(self) -> None:`

## 4. 论文模块 -> 代码模块映射

### Latent Planning and Iterative Inference

- Explanation: `Latent Planning and Iterative Inference` has no direct symbol hit yet; start from the strongest architecture entry candidates.
- Evidence: `INFERRED`
- Code: `runner/trainer.py:282 - def prepare_models`
- Code: `runner/trainer.py:70 - class State`
- Code: `runner/trainer.py:91 - class Trainer`

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

### Latent Planning and Iterative Inference

- No direct code hit yet; keep this as a manual reading target.
- Evidence: `INFERRED`

## 7. 建议阅读顺序

1. `runner/trainer.py:282 - def prepare_models`
2. `runner/trainer.py:70 - class State`
3. `runner/trainer.py:91 - class Trainer`
4. `runner/trainer.py:93 - def __init__`
5. `runner/trainer.py:158 - def _init_distributed`
6. `runner/trainer.py:210 - def _init_logging`
7. `runner/trainer.py:227 - def _init_directories_and_repositories`
8. `runner/trainer.py:234 - def prepare_dataset`
9. `runner/trainer.py:358 - def prepare_trainable_parameters`
10. `runner/trainer.py:481 - def prepare_for_training`
11. `runner/trainer.py:493 - def train`
12. `utils/dreamer_style_loss.py:51 - def dreamer_twohot_loss`

## 8. 未确认点

- [Missing Evidence] All requested concepts are currently inferred rather than directly confirmed in code.
- [Missing Evidence] `Latent Planning and Iterative Inference` needs manual confirmation because no direct code hit was found.
