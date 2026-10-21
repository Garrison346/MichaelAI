# Michael - Autonomous Fire Detection Robot 🤖🔥

Michael is an autonomous robotics project designed for real-time fire and smoke detection using computer vision, dual-model verification (object detection and classification), and edge computing.

---

## 🛠️ Tech Stack & Hardware

- **Hardware:** Raspberry Pi (8GB)
- **Computer Vision:** YOLOv8 (Ultralytics) for object detection and classification
- **Environment:** Python 3, OpenCV, PyTorch

---

## 🚀 Getting Started

Tested on Windows with Python 3.12.

1. **Create the environment**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Enable GPU training (NVIDIA only, optional).** `requirements.txt` installs CPU-only PyTorch; inference, the dashboard and tests work without this.
   ```powershell
   pip install torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cu126
   python -c "import torch; print(torch.cuda.is_available())"   # should print True
   ```
3. **Check the install:** `pytest` should report all tests passing. The trained model is committed in `models/`, so the real-model tests run immediately.
4. **Try the dashboard:** `streamlit run dashboard/app.py`
5. **Download the classification dataset (needed only to train or evaluate).** Export the [Roboflow dataset](https://universe.roboflow.com/national-university-of-sciences-technology/fire-no-fire-classification) in *Folder Structure* format and unzip it so the layout is:
   ```text
   dataset/classification/
   ├── train/  fire/  nofire/
   ├── val/    fire/  nofire/     # rename valid/ to val/ if the export uses that name
   └── test/   fire/  nofire/
   ```
   Then run `python scripts/check_classification_leakage.py`; it should print `Leakage check passed!`

Using Claude Code? `CLAUDE.md` holds the project conventions, and `/evaluate-fire-classifier` walks through training and comparing a new model.

---

## 📁 Repository Structure

```text
MichaelAI/
├── .claude/
│   └── skills/
│       └── evaluate-fire-classifier/
│           └── SKILL.md                # Train/evaluate/report workflow (Claude Code skill)
├── .streamlit/
│   └── config.toml                     # Dashboard server settings (localhost only)
├── dashboard/
│   └── app.py                          # Streamlit dashboard (classify images, training metrics)
├── dataset/
│   ├── classification/
│   │   ├── train/  val/  test/         # fire/ and nofire/ images (local only, gitignored)
│   │   ├── test_hard/                  # Hand-picked hard cases (committed)
│   │   ├── README.dataset.txt          # Dataset source and license
│   │   └── README.roboflow.txt         # Roboflow export notes
│   └── detection/
│       ├── train/  valid/  test/       # images/ and labels/ (local only, gitignored)
│       └── README.roboflow.txt         # Roboflow export notes
├── docs/
│   └── dataset_sources.bib             # BibTeX citations for both datasets
├── models/
│   ├── fire_baseline.pt                # Adopted classifier weights (committed)
│   └── fire_baseline_results.csv       # Its training history (dashboard metrics tab)
├── runs/                               # Experiment outputs from training/evaluation (gitignored)
├── scripts/
│   ├── check_classification_leakage.py # Check classification splits for duplicates/leakage
│   ├── check_dataset.py                # Validate detection images and labels
│   ├── evaluate_classifier.py          # Evaluate the classifier on the test split
│   ├── sweep_threshold.py              # Missed fires / false alarms at several thresholds
│   └── train_classifier.py             # Train the YOLOv8 fire classifier
├── src/
│   ├── __init__.py
│   └── perception/
│       ├── __init__.py
│       └── classifier.py               # FireClassifier inference wrapper
├── tests/
│   ├── test_classifier.py              # FireClassifier tests
│   ├── test_dashboard.py               # Dashboard startup smoke test
│   └── test_leakage_check.py           # Leakage check tests
├── .gitignore                          # File exclusion rules
├── CLAUDE.md                           # Project notes for Claude Code
├── pytest.ini                          # Test configuration
├── README.md                           # Project overview
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