# ReconVLA: Reconstructive Vision-Language-Action Model as Effective Robot Perceiver 架构学习笔记

## 1. 任务与输入

- Paper: `E:\my-embodied\.study-agent\repos\ReconVLA\README.md`
- Repository: `E:\my-embodied\.study-agent\repos\ReconVLA`
- Focus: `architecture`
- Analysis mode: `paper-aligned`
- Engine: `offline`

## 2. 论文核心概念解释

### architecture

- Summary: `architecture` appears in the paper material and should be treated as a primary reading target.
- Evidence: `CONFIRMED`

## 3. 仓库入口与主干候选

- Scanned files: `55`
- File groups:
  - `docs`: `README.md`, `reconvla/scripts/helper/Readme.md`, `recon_requirements.txt`
  - `train_scripts`: `reconvla/scripts/train_vla/pretrain.sh`, `reconvla/scripts/train_vla/finetune.sh`, `reconvla/train_vla.py`, `reconvla/pre_train_vla_action.py`, `reconvla/recon/recon_trainer.py`
  - `inference_scripts`: `reconvla/serve/flask_server.py`
  - `configs`: `reconvla/statistics.yaml`, `evaluation/question.json`, `reconvla/scripts/zero3.json`, `reconvla/scripts/zero2.json`
  - `core_model`: `reconvla/recon/model/pixel_decoder/builder.py`, `reconvla/recon/model/pixel_decoder/flux_decoder.py`, `reconvla/recon/model/multimodal_encoder/builder.py`, `reconvla/recon/model/multimodal_encoder/clip_encoder.py`, `reconvla/recon/model/multimodal_encoder/siglip_encoder.py`
  - `deployment_policy`: `reconvla/serve/flask_server.py`, `reconvla/scripts/test_vla/start_multi_server.sh`
  - `model_policy`: `evaluation/evaluate_policy_singlestep.py`, `evaluation/evaluate_policy_multiserver.sh`, `evaluation/evaluate_policy_multiserver.py`, `reconvla/recon/model/pixel_decoder/builder.py`, `reconvla/recon/model/pixel_decoder/flux_decoder.py`
  - `data`: `reconvla/action_tokenizer.py`, `reconvla/recon/action_tokenizer.py`
  - `utils`: `evaluation/utils.py`, `reconvla/recon/utils.py`, `reconvla/recon/mm_utils.py`, `reconvla/recon/model/utils.py`, `reconvla/recon/model/multimodal_denoiser/diffusion_utils/respace.py`
- Core model candidates:
  - `reconvla/recon/model/pixel_decoder/builder.py`
  - `reconvla/recon/model/pixel_decoder/flux_decoder.py`
  - `reconvla/recon/model/multimodal_encoder/builder.py`
  - `reconvla/recon/model/multimodal_encoder/clip_encoder.py`
  - `reconvla/recon/model/multimodal_encoder/siglip_encoder.py`
  - `reconvla/recon/model/pixel_decoder/__init__.py`
- Deployment/client policy candidates:
  - `reconvla/serve/flask_server.py`
  - `reconvla/scripts/test_vla/start_multi_server.sh`
- Model candidates:
  - `reconvla/recon/model/pixel_decoder/builder.py`
  - `reconvla/recon/model/pixel_decoder/flux_decoder.py`
  - `reconvla/recon/model/multimodal_encoder/builder.py`
  - `reconvla/recon/model/multimodal_encoder/clip_encoder.py`
  - `reconvla/recon/model/multimodal_encoder/siglip_encoder.py`
  - `reconvla/recon/model/pixel_decoder/__init__.py`
  - `reconvla/serve/flask_server.py`
  - `reconvla/scripts/test_vla/start_multi_server.sh`
- Train candidates:
  - `reconvla/scripts/train_vla/pretrain.sh`
  - `reconvla/scripts/train_vla/finetune.sh`
  - `reconvla/train_vla.py`
  - `reconvla/pre_train_vla_action.py`
  - `reconvla/recon/recon_trainer.py`
- Inference candidates:
  - `reconvla/serve/flask_server.py`
- Config candidates:
  - `reconvla/statistics.yaml`
  - `evaluation/question.json`
  - `reconvla/scripts/zero3.json`
  - `reconvla/scripts/zero2.json`
- Data candidates:
  - `reconvla/action_tokenizer.py`
  - `reconvla/recon/action_tokenizer.py`
- Utils candidates:
  - `evaluation/utils.py`
  - `reconvla/recon/utils.py`
  - `reconvla/recon/mm_utils.py`
  - `reconvla/recon/model/utils.py`
  - `reconvla/recon/model/multimodal_denoiser/diffusion_utils/respace.py`
  - `reconvla/recon/model/multimodal_denoiser/diffusion_utils/diffusion_utils.py`
  - `reconvla/recon/model/multimodal_denoiser/diffusion_utils/gaussian_diffusion.py`
  - `reconvla/recon/model/multimodal_denoiser/diffusion_utils/__init__.py`
- Docs candidates:
  - `README.md`
  - `reconvla/scripts/helper/Readme.md`
  - `recon_requirements.txt`
- Entry candidates:
  - Candidate 1: `reconvla/pre_train_vla_action.py:97 - class ModelArguments`
    - Evidence: `class ModelArguments:`
  - Candidate 2: `reconvla/pre_train_vla_action.py:246 - def safe_save_model_for_hf_trainer`
    - Evidence: `def safe_save_model_for_hf_trainer(trainer: transformers.Trainer,`
  - Candidate 3: `reconvla/pre_train_vla_action.py:940 - def preprocess_qwen_2_vla`
    - Evidence: `def preprocess_qwen_2_vla(`
  - Candidate 4: `reconvla/recon/model/multimodal_denoiser/diffusion_utils/gaussian_diffusion.py:23 - class ModelMeanType`
    - Evidence: `class ModelMeanType(enum.Enum):`
  - Candidate 5: `reconvla/recon/model/multimodal_denoiser/diffusion_utils/gaussian_diffusion.py:33 - class ModelVarType`
    - Evidence: `class ModelVarType(enum.Enum):`
  - Candidate 6: `reconvla/train_vla.py:55 - class ModelArguments`
    - Evidence: `class ModelArguments:`
  - Candidate 7: `reconvla/train_vla.py:199 - def safe_save_model_for_hf_trainer`
    - Evidence: `def safe_save_model_for_hf_trainer(trainer: transformers.Trainer,`
  - Candidate 8: `reconvla/train_vla.py:896 - def preprocess_qwen_2_vla`
    - Evidence: `def preprocess_qwen_2_vla(`

## 4. 论文模块 -> 代码模块映射

### architecture

- Explanation: `architecture` has direct repository evidence in the files listed below.
- Evidence: `CONFIRMED`
- Code: `README.md:16 - - **Implicit Grounding Architecture**: Reconstructive VLA paradigm that aligns gaze regions with manipulated targets, enforcing precise visual attention and fine-grained representation learning.`
- Code: `evaluation/evaluate_policy_multiserver.py:80 - logger.warning("Please implement these methods as an interface to your custom model architecture.")`

## 5. 训练/推理主路径

### Training

- `reconvla/pre_train_vla_action.py:137 - class TrainingArguments`
- `reconvla/pre_train_vla_action.py:246 - def safe_save_model_for_hf_trainer`
- `reconvla/pre_train_vla_action.py:1346 - def train`
- `reconvla/train_vla.py:90 - class TrainingArguments`
- `reconvla/train_vla.py:199 - def safe_save_model_for_hf_trainer`
- `reconvla/train_vla.py:1219 - def train`
- `reconvla/recon/recon_trainer.py:150 - class ReconTrainer`
- `reconvla/recon/recon_trainer.py:152 - def _get_train_sampler`

### Inference

- `evaluation/evaluate_policy_multiserver.py:162 - def evaluate_policy`
- `evaluation/evaluate_policy_multiserver.py:220 - def evaluate_sequence`
- `evaluation/evaluate_policy_singlestep.py:14 - def evaluate_policy_singlestep`
- `reconvla/recon/recon_trainer.py:116 - class LengthGroupedSampler`
- `reconvla/recon/recon_trainer.py:152 - def _get_train_sampler`
- `reconvla/serve/flask_server.py:159 - def predict`
- `reconvla/recon/model/language_model/recon_qwen.py:48 - def forward`
- `reconvla/recon/model/language_model/recon_qwen.py:111 - def inner_forward`

## 6. 关注点专项

### architecture

- `README.md:16` - - **Implicit Grounding Architecture**: Reconstructive VLA paradigm that aligns gaze regions with manipulated targets, enforcing precise visual attention and fine-grained representation learning.
- `evaluation/evaluate_policy_multiserver.py:80` - logger.warning("Please implement these methods as an interface to your custom model architecture.")
- Evidence: `CONFIRMED`

## 7. 建议阅读顺序

1. `reconvla/pre_train_vla_action.py:97 - class ModelArguments`
2. `reconvla/pre_train_vla_action.py:246 - def safe_save_model_for_hf_trainer`
3. `reconvla/pre_train_vla_action.py:940 - def preprocess_qwen_2_vla`
4. `reconvla/recon/model/multimodal_denoiser/diffusion_utils/gaussian_diffusion.py:23 - class ModelMeanType`
5. `reconvla/recon/model/multimodal_denoiser/diffusion_utils/gaussian_diffusion.py:33 - class ModelVarType`
6. `reconvla/train_vla.py:55 - class ModelArguments`
7. `reconvla/train_vla.py:199 - def safe_save_model_for_hf_trainer`
8. `reconvla/train_vla.py:896 - def preprocess_qwen_2_vla`
9. `reconvla/pre_train_vla_action.py:137 - class TrainingArguments`
10. `reconvla/pre_train_vla_action.py:1346 - def train`
11. `reconvla/train_vla.py:90 - class TrainingArguments`
12. `reconvla/train_vla.py:1219 - def train`

## 8. 未确认点

- [Missing Evidence] Deployment/client policy files found; treat them as inference wrappers unless paper evidence suggests otherwise.
- [Missing Evidence] Core model files found, but deployment/client wrappers are also prominent. Prioritize core_model candidates for architecture analysis.
- [Missing Evidence] No obvious standalone loss/objective file found.
- [Missing Evidence] Loss/objective may be implemented inline in model/trainer/algorithm files.
- [Missing Evidence] No obvious standalone env/robot interface file found.
- [Missing Evidence] Environment integration may be implemented inline in deploy/wrapper/controller files.
