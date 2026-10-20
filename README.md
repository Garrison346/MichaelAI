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
├── dataset/             # Dataset configuration, detection, and classification trees
├── docs/                # Hardware diagrams and documentation
├── scripts/             # Utility and training scripts
├── src/                 # Main robot scripts (vision & control)
├── tests/               # Test suites and setup checks
├── .gitignore           # File exclusion rules
├── README.md            # Project overview
└── requirements.txt     # Python dependencies
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

## 📄 References

**Classification dataset:**

National University of Sciences Technology. (2025). *fire no fire classification Dataset*. Roboflow Universe. https://universe.roboflow.com/national-university-of-sciences-technology/fire-no-fire-classification

**Detection dataset:**

fire null. (2024). *fire-indoor Dataset*. Roboflow Universe. https://universe.roboflow.com/fire-null/fire-indoor-ghkgq