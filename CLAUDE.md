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
- `dataset/` images and `runs/` are gitignored; only scripts, docs and READMEs are committed.
- Run `pytest` before committing. The real-model tests skip when
  `runs/classify/fire_baseline/weights/best.pt` is missing.

## Workflows
- Training, evaluating or comparing classifier runs: use the
  `evaluate-fire-classifier` skill (`.claude/skills/`).
- Dashboard: `streamlit run dashboard/app.py`.
