
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset" / "detection" / "data.yaml"


def main():
    # Load a pretrained YOLOv8 nano object detection model
    model = YOLO("yolov8n.pt")

    model.train(
        data=str(DATASET),  # Object detection dataset YAML
        epochs=50,           # Maximum training epochs
        imgsz=640,            # Image resolution
        batch=8,              # Images per optimization step
        patience=10,           # Early stopping
        workers=2,             # Parallel data-loading processes
        seed=42,               # Reproducibility
        device="cpu",              # Use CPU for training
        project=str(ROOT / "runs" / "detect"),
        name="fire_detector_baseline",
        exist_ok=True,
    )


if __name__ == "__main__":
    main()
