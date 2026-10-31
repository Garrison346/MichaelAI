# Michael - Autonomous Fire Detection Robot 🤖🔥

Michael is an autonomous robotics project for fire and smoke detection, combining computer vision, autonomous navigation, SLAM, and edge computing.

The project currently includes a trained YOLOv8 fire/no-fire classifier and a ROS 2 simulation environment. Object detection, autonomous exploration, and physical rover integration are planned.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Computer vision | Python, YOLOv8, PyTorch, OpenCV |
| Robotics | ROS 2 Jazzy, Nav2, SLAM Toolbox |
| Simulation | Gazebo Harmonic, RViz2 |
| Development environments | Windows 11, Ubuntu 24.04 / WSL2 |
| Target hardware | Raspberry Pi (8GB), camera, mobile rover |

---

## 🚀 Getting Started

The Python fire-classification pipeline is tested on Windows with Python 3.12. The Linux steps below are the standard equivalents but haven't been tested yet. The robotics simulation targets Ubuntu 24.04 with ROS 2 Jazzy.

### 1. Clone the repository

```bash
git clone https://github.com/Garrison346/MichaelAI.git
cd MichaelAI
```

### 2. Set up Python

Use Python 3.12 and create a virtual environment.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**Linux (Ubuntu)**

```bash
sudo apt install python3-venv    # Ubuntu 24.04 doesn't ship it by default
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

> The Python ML environment is separate from ROS 2. Don't install `requirements.txt` into ROS 2's system Python.

### 3. Optional NVIDIA GPU support

CPU inference, the dashboard, and tests don't need an NVIDIA GPU.

On Windows, `requirements.txt` installs CPU-only PyTorch. For GPU training, install the CUDA build (tested on a GTX 1650):

```powershell
pip install torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cu126
```

On Linux, the default PyTorch wheel already includes CUDA support. For other setups, see the [official PyTorch installation guide](https://pytorch.org/get-started/locally/).

Check availability (should print `True`):

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

### 4. Verify installation

With the virtual environment active, run:

```bash
python -m pytest
```

All tests should pass. The committed baseline model in `models/` lets the classifier tests and dashboard run without retraining.

### 5. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Open [http://localhost:8501](http://localhost:8501). The server only accepts connections from this computer (`.streamlit/config.toml`).

### 6. Download the classification dataset (optional)

The dataset is needed for training and evaluation, but not for running inference with the committed baseline model.

Download the [Fire/No-Fire Classification Dataset](https://universe.roboflow.com/national-university-of-sciences-technology/fire-no-fire-classification) from Roboflow in *Folder Structure* format and unzip it so the layout is:

```text
dataset/classification/
├── train/
│   ├── fire/
│   └── nofire/
├── val/
│   ├── fire/
│   └── nofire/
└── test/
    ├── fire/
    └── nofire/
```

Rename `valid/` to `val/` if the export uses that name.

Verify dataset integrity (should print `Leakage check passed!`):

```bash
python scripts/check_classification_leakage.py
```

Using Claude Code? See `CLAUDE.md` for project conventions and `/evaluate-fire-classifier` for model evaluation workflows.

---

## 🤖 ROS 2 Simulation (Linux / WSL2)

The robotics workspace lives in `ros2_ws/`.

**Supported development environment:**
- Ubuntu 24.04, including WSL2 on Windows
- ROS 2 Jazzy
- Gazebo Harmonic
- Nav2 and SLAM Toolbox
- Colcon and rosdep

The project currently uses Nav2's TurtleBot3 reference simulation to validate SLAM, navigation, and autonomous movement. A custom rover isn't required at this stage.

### Build the workspace

Open an Ubuntu terminal, go to the repository (from WSL, a Windows checkout is under `/mnt/c/...`), and run:

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws

colcon build --symlink-install
source install/setup.bash
```

### Launch the simulator

```bash
ros2 launch rover_bringup sim.launch.py
```

The default launch opens Gazebo and RViz2 and enables SLAM. Add `headless:=True use_rviz:=False` to run without a GUI.

### Verify mapping

In another sourced Ubuntu terminal:

```bash
ros2 topic hz /scan    # ~5 Hz
ros2 topic hz /map     # one map every ~5 s
```

### Run the simulation baseline test

The integration test is opt-in and starts its own isolated simulation (about 35 s):

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash

launch_test src/rover_bringup/test/test_sim_baseline.launch.py
```

The baseline verifies sensor data, occupancy-grid mapping, coordinate transforms, Nav2 availability, navigation-goal completion, and map growth.

For complete installation instructions, ROS dependencies, test isolation, map saving, troubleshooting, and ROS interfaces, see the **[ROS 2 Workspace Guide](ros2_ws/README.md)**.

> ROS dependencies are declared in each package's `package.xml` and managed with rosdep/APT. They don't belong in the root Python `requirements.txt`.

---

## 📁 Repository Structure

```text
MichaelAI/
├── .claude/
│   └── skills/
│       └── evaluate-fire-classifier/   # Train/evaluate/report workflow (Claude Code skill)
├── .streamlit/
│   └── config.toml                     # Dashboard server settings (localhost only)
├── dashboard/
│   └── app.py                          # Streamlit dashboard
├── dataset/
│   ├── classification/                 # train/ val/ test/ local only; test_hard/ committed
│   └── detection/                      # images and labels local only
├── docs/
│   └── dataset_sources.bib             # BibTeX citations for both datasets
├── models/
│   ├── fire_baseline.pt                # Adopted classifier weights (committed)
│   └── fire_baseline_results.csv       # Its training history (dashboard metrics tab)
├── ros2_ws/
│   ├── README.md                       # ROS setup, run and test guide
│   └── src/
│       └── rover_bringup/
│           ├── launch/
│           │   └── sim.launch.py       # TurtleBot3 reference sim + SLAM
│           ├── test/
│           │   └── test_sim_baseline.launch.py  # Opt-in sim baseline test
│           ├── CMakeLists.txt
│           └── package.xml
├── runs/                               # Experiment outputs (gitignored)
├── scripts/
│   ├── check_classification_leakage.py # Check classification splits for duplicates/leakage
│   ├── check_dataset.py                # Validate detection images and labels
│   ├── evaluate_classifier.py          # Evaluate the classifier on the test split
│   ├── sweep_threshold.py              # Missed fires / false alarms at several thresholds
│   └── train_classifier.py             # Train the YOLOv8 fire classifier
├── src/
│   └── perception/
│       └── classifier.py               # FireClassifier inference wrapper
├── tests/                              # pytest suite (classifier, dashboard, leakage check)
├── .gitignore
├── CLAUDE.md                           # Project notes for Claude Code
├── pytest.ini
├── README.md
├── requirements.txt                    # Pinned Python dependencies
└── test_setup.py                       # Ultralytics install check
```

---

## 📚 Citation & Dataset Attribution

Michael uses publicly available datasets from Roboflow Universe for training and evaluating its computer vision models.

### 1. Fire/No-Fire Classification Dataset

**Source:** National University of Sciences Technology  
**Published:** March 2025  
**Purpose:** Binary classification of images as fire or no-fire.

[View Classification Dataset on Roboflow](https://universe.roboflow.com/national-university-of-sciences-technology/fire-no-fire-classification)

### 2. Fire Indoor Detection Dataset

**Source:** fire null  
**Published:** April 2024  
**Purpose:** Training the fire object detection model.

[View Detection Dataset on Roboflow](https://universe.roboflow.com/fire-null/fire-indoor-ghkgq)

### Dataset Usage

Dataset files are excluded from Git where configured in `.gitignore`, except the small hand-picked `dataset/classification/test_hard/` set. Contributors should obtain the datasets from their original sources and follow the applicable licensing requirements.

Both datasets were accessed on October 11, 2026.

### Classification Split

Uses Roboflow's original train/val/test split. Augmented copies exist only in train, and `scripts/check_classification_leakage.py` confirms no image group or exact duplicate crosses splits. About 6% of test images are near-duplicates of training images.

---

## 🔥 Fire Classifier

Run all commands from the repository root with the virtual environment active.

| Step | Command | Output |
|---|---|---|
| Check the split for leakage | `python scripts/check_classification_leakage.py` | Console report |
| Train (GPU, up to 40 epochs) | `python scripts/train_classifier.py` | `runs/classify/fire_baseline/` |
| Evaluate on the test split | `python scripts/evaluate_classifier.py` | `runs/classify/fire_baseline_test/` |
| Sweep thresholds (GPU) | `python scripts/sweep_threshold.py` | Console table + misclassified files |
| Run tests | `pytest` | |
| Dashboard | `streamlit run dashboard/app.py` | http://localhost:8501 |

### Baseline Results (YOLOv8n-cls, 224px, batch 32)

Early-stopped at epoch 32; best weights from epoch 22, committed as `models/fire_baseline.pt`.

| Metric | Test set (417 images) |
|---|---|
| Accuracy | 98.80% |
| Fire recall | 100% (0 of 213 fires missed) |
| False alarms | 5 of 204 no-fire images |

False alarms are fire-like scenes (sunsets, low cloud resembling smoke). The default threshold of 0.5 is kept: lowering it to 0.3 adds a false alarm without catching more fires.

---

## 📄 References

**Classification dataset:**

National University of Sciences Technology. (2025). *fire no fire classification Dataset*. Roboflow Universe. https://universe.roboflow.com/national-university-of-sciences-technology/fire-no-fire-classification

**Detection dataset:**

fire null. (2024). *fire-indoor Dataset*. Roboflow Universe. https://universe.roboflow.com/fire-null/fire-indoor-ghkgq