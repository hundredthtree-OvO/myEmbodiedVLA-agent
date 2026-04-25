# Detailed Roadmap

This file keeps the detailed roadmap, MVP scope, and implementation feedback.
`README.md` only keeps the high-level direction.

## Positioning

Current product:
- Codex-first paper-code alignment copilot
- Strong at generating structured study notes from paper + repo + focus
- Not yet a full research-learning agent

Next main goal:
- strengthen evidence quality first
- then add a lightweight learning loop

Core direction:

```text
paper concept -> code realization -> reusable research memory
```

## Current Status

Completed:
- P0 Foundation Hardening
- P1 Step 1: structured repo evidence pack
- `core_model` / `deployment_policy` split

Current gap:
- a single `entry_candidates` list is still too coarse
- architecture focus can still be disturbed by config/training/deployment files
- the system needs role-aware reading order, not only keyword/path scoring

## P1 MVP: Role-Aware Ranking

### Goal

Make `architecture / model / module` focus behave more like a human first-pass repo reading order.

### MVP Scope

First round only implements:
- `architecture_entry_candidates`
- `config_entry_candidates`
- `deployment_entry_candidates`

Keep old fields for compatibility:
- `core_model_candidates`
- `deployment_policy_candidates`
- `train_candidates`
- `inference_candidates`
- `config_candidates`
- `model_candidates`
- `entry_candidates`

### Design Rules

1. Use multi-role classification instead of forcing one file to have one role.

2. Use generalized signals for `architecture_entry`, not hardcoded filenames.

Useful signals:
- core model path
- assembly/skeleton filename tokens like `arch`, `builder`, `model`, `vla`, `vlm`, `policy`
- non-noise file
- lightweight project stem match

3. Keep reference centrality light in MVP.

The first round does not build a full import/call graph.

4. `candidate_reason` is a debug tool first.

It is mainly used to inspect whether the rule is generalizing or just overfitting.

## What Was Implemented

Implementation date:
- 2026-04-25

Implemented in code:
- `RepoInfo` now includes:
  - `architecture_entry_candidates`
  - `config_entry_candidates`
  - `deployment_entry_candidates`
  - `candidate_reasons`
- `ingest_repo()` now builds role-aware candidate lists
- `prompt_builder` exposes the new role-aware sections
- `composer` exposes the new role-aware sections in offline markdown
- `build_reading_path()` now uses focus-aware ordering for:
  - `architecture / model / module`
  - `training / loss / objective`
  - `inference / deploy / eval`
  - `config / hyperparameter`

Debug support:
- top role-aware candidates now include reason traces in offline/prompt output

Tests:
- unit tests updated for the new role-aware candidate lists
- architecture-focus reading order test added

Current automated test result:

```text
Ran 27 tests ... OK
```

## Validation Feedback

Validation method:
- run `offline` analysis on 4 real repos
- inspect:
  - `architecture_entry_candidates`
  - `config_entry_candidates`
  - `deployment_entry_candidates`
  - `reading_path`
  - `candidate_reason`

### WAV

Result:
- good separation between core model and deployment wrappers remains intact
- deployment wrappers do not steal the main model reading position
- role-aware output is stable

What worked:
- `deployment_entry_candidates` correctly isolate `openpi_client/runtime/*`
- reading order stays on model-side files first

Remaining issue:
- this repo has no single obvious architecture assembly file
- the top architecture candidates are still component-heavy:
  - `models/action_patches/patches.py`
  - `models/pipeline/custom_pipeline.py`
  - `models/value_patches/value_patches.py`

Assessment:
- good enough for MVP
- not yet assembly-aware for repos whose logic is spread across patches/pipeline/components

### VLA-Adapter

Result:
- clearly improved
- `prismatic.py` now rises into the architecture entry set
- `extern/hf/modeling_prismatic.py` no longer dominates the entry view

What worked:
- `architecture_entry_candidates` now include:
  - `prismatic/models/vlms/base_vlm.py`
  - `prismatic/models/vlas/openvla.py`
  - `prismatic/models/vlms/prismatic.py`
- `config_entry_candidates` now prefer:
  - `prismatic/conf/vla.py`
  - `prismatic/conf/models.py`
  - `prismatic/conf/datasets.py`

Remaining issue:
- `base_vlm.py` and `openvla.py` still rank ahead of `prismatic.py`
- for concept-focused reading such as bridge attention, this is still not enough by itself

Assessment:
- meaningful improvement
- architecture-first behavior is now much closer to the desired direction

### ACoT-VLA

Result:
- clearly improved
- the main architecture file is now correctly lifted

What worked:
- `architecture_entry_candidates` now start with:
  - `src/openpi/models/acot_vla.py`
  - `src/openpi/models/model.py`
  - `src/openpi/models/vit.py`
  - `src/openpi/models/pi0.py`
- `training/config.py` is no longer occupying the main architecture slot
- reading order is now much closer to a human first-pass order

Assessment:
- success case for the MVP

### ReconVLA

Result:
- improved, but not complete

What worked:
- `recon_arch.py` and `builder.py` are now lifted into architecture entry candidates
- training/config/deployment files do not dominate the architecture slot anymore

What is still missing:
- `recon_qwen.py` is still not stably lifted into the top architecture reading set
- pixel/multimodal builders are still stronger than the higher-level language-model assembly file

Assessment:
- partial success
- shows that the current MVP handles assembly files better than before
- but still needs stronger assembly-vs-component discrimination

## Overall MVP Judgment

This P1 MVP is worth keeping.

It already improves generalization in a useful way:
- the system is less dependent on a single mixed ranking list
- architecture focus is less likely to be hijacked by config/deployment noise
- the reading path is closer to manual repo reading on multiple real VLA repos

But it is still only a first MVP:
- strong on role-aware separation
- not yet strong enough on assembly-vs-component prioritization
- not yet concept-aware

## What Not To Do Yet

Do not jump to:
- full AST graph
- full CandidateInfo system everywhere
- complex retrieval/learning loop
- concept-aware second-pass reading

The single-analysis quality still needs one more tightening round first.

## Next Step

Recommended next step:
- keep P1 narrow
- do one more refinement focused on:

```text
assembly file vs component file discrimination
```

Priority items:
- lift architecture skeleton files more reliably
- reduce helper/component dominance in `architecture_entry_candidates`
- keep config/deployment as secondary under architecture focus

Examples of target improvements:
- ReconVLA:
  - lift `recon_qwen.py` more reliably
- WAV:
  - identify stronger architecture skeleton proxies if no single assembly file exists
- VLA-Adapter:
  - keep `prismatic.py` stable in the top architecture set

After that:
- move to "important file second-pass reading"

## Next Phase After MVP

After role-aware ranking is stable:
- second-pass reading of 3-8 key files
- stronger repo evidence for Concept2Code tracing
- then lightweight learning loop:
  - session reflection
  - skill memory
  - retrieval
