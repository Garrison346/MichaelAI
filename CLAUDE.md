# MichaelAI

Fire/smoke detection robot. YOLOv8 classification (fire/nofire) now; detection later.

## Environment
- Windows. Run everything from the repo root with `.venv` active.
- GPU: GTX 1650 (4 GB). Classifier training at 224px with batch 32 fits.
- Target device is a Raspberry Pi (CPU only), so inference defaults to `device="cpu"`.
- ROS 2 Jazzy runs in WSL Ubuntu 24.04. The workspace is `ros2_ws/` (build there with colcon);
  the Python ML code stays outside it. ROS deps go in `package.xml`, not `requirements.txt`.

## Conventions
- Keep changes minimal and non-invasive. Scripts use constants at the top
  (`ROOT`, `DATASET`, `RUN`), not argparse or config frameworks.
- `src/perception/classifier.py` (`FireClassifier`) reports probabilities only.
  On any inference failure it must raise, never return "nofire". Robot
  decisions belong to the control code.
- `dataset/` images and `runs/` are gitignored. Exceptions: the small `dataset/classification/test_hard/`
  set, and adopted models in `models/` (`fire_baseline.pt` + its `results.csv`), so a fresh
  clone can run the dashboard and tests without training. `runs/` is for experiments.
- Run `pytest` before committing. If `ros2_ws/` changed, also run the opt-in sim test in WSL
  (`launch_test src/rover_bringup/test/test_sim_baseline.launch.py`, see `ros2_ws/README.md`).

## Evidence-first
- Inspect the repo and installed ROS packages/configs (`/opt/ros/jazzy/share/...`, `ros2 topic info -v`)
  before planning; don't assume an API, topic, QoS or parameter exists because an example uses it.
- Label material claims as verified, inferred or unknown. A build, a topic in `ros2 topic list` or an
  active Nav2 server doesn't prove runtime behavior; report only the level of testing actually done.
- Prefer the smallest conventional fix; reuse Nav2/SLAM Toolbox; no speculative abstractions or deps.
- When an assumption fails, stop and find the cause. Don't retry blindly, add arbitrary delays or
  loosen checks to get a pass. Measure (e.g. startup time) before setting timeouts.
- Report exactly which tests ran and their results; ask before widening the agreed scope.

## Workflows
- Training, evaluating or comparing classifier runs: use the
  `evaluate-fire-classifier` skill (`.claude/skills/`).
- Dashboard: `streamlit run dashboard/app.py`.
- ROS build, sim test or sim/Nav2 debugging: use the `validate-ros-stack` skill.
