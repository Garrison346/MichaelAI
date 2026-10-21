# MichaelAI

Fire/smoke detection robot. YOLOv8 classification (fire/nofire) now; detection later.

## Environment
- Windows. Run everything from the repo root with `.venv` active.
- GPU: GTX 1650 (4 GB). Classifier training at 224px with batch 32 fits.
- Target device is a Raspberry Pi (CPU only), so inference defaults to `device="cpu"`.

## Conventions
- Keep changes minimal and non-invasive. Scripts use constants at the top
  (`ROOT`, `DATASET`, `RUN`), not argparse or config frameworks.
- `src/perception/classifier.py` (`FireClassifier`) reports probabilities only.
  On any inference failure it must raise, never return "nofire". Robot
  decisions belong to the control code.
- `dataset/` images and `runs/` are gitignored. Exceptions: the small `dataset/classification/test_hard/`
  set, and adopted models in `models/` (`fire_baseline.pt` + its `results.csv`), so a fresh
  clone can run the dashboard and tests without training. `runs/` is for experiments.
- Run `pytest` before committing.

## Workflows
- Training, evaluating or comparing classifier runs: use the
  `evaluate-fire-classifier` skill (`.claude/skills/`).
- Dashboard: `streamlit run dashboard/app.py`.
