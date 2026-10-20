# Michael - Autonomous Fire Detection Robot 🤖🔥

Michael is an autonomous robotics project designed for real-time fire and smoke detection using computer vision, dual-model verification (object detection and classification), and edge computing.

---

## 🛠️ Tech Stack & Hardware

- **Hardware:** Raspberry Pi (8GB)
- **Computer Vision:** YOLOv8 (Ultralytics) for object detection and classification
- **Environment:** Python 3, OpenCV, PyTorch

---

## 📁 Repository Structure

```text
MichaelAI/
├── dashboard/
│   └── app.py                          # Streamlit dashboard (classify images, training metrics)
├── dataset/
│   ├── classification/
│   │   ├── train/  val/  test/         # fire/ and nofire/ images (local only, gitignored)
│   │   ├── README.dataset.txt          # Dataset source and license
│   │   └── README.roboflow.txt         # Roboflow export notes
│   └── detection/
│       ├── train/  valid/  test/       # images/ and labels/ (local only, gitignored)
│       └── README.roboflow.txt         # Roboflow export notes
├── docs/
│   └── dataset_sources.bib             # BibTeX citations for both datasets
├── runs/                               # Training and evaluation outputs (gitignored)
├── scripts/
│   ├── check_classification_leakage.py # Check classification splits for duplicates/leakage
│   ├── check_dataset.py                # Validate detection images and labels
│   ├── evaluate_classifier.py          # Evaluate the classifier on the test split
│   └── train_classifier.py             # Train the YOLOv8 fire classifier
├── src/
│   ├── __init__.py
│   └── perception/
│       ├── __init__.py
│       └── classifier.py               # FireClassifier inference wrapper
├── tests/
│   └── test_classifier.py              # FireClassifier tests
├── .gitignore                          # File exclusion rules
├── README.md                           # Project overview
├── requirements.txt                    # Python dependencies
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

Dataset files are excluded from Git where configured in `.gitignore`. Contributors should obtain the datasets from their original sources and follow the applicable licensing requirements.

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
| Run tests | `python -m pytest tests/` | |
| Dashboard | `streamlit run dashboard/app.py` | http://localhost:8501 |

### Baseline Results (YOLOv8n-cls, 224px, batch 32)

Early-stopped at epoch 32; best weights from epoch 22.

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