
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset" / "classification"
RUN = "fire_baseline"  # Training run to evaluate
WEIGHTS = ROOT / "runs" / "classify" / RUN / "weights" / "best.pt"


def main():
    # Evaluate on held-out test images
    model = YOLO(str(WEIGHTS))

    metrics = model.val(
        data=str(DATASET),  # Classification dataset
        split="test",       # Held-out test split
        imgsz=224,          # Match training resolution
        batch=8,
        device="cpu",       # Portable; use 0 for local GPU
        project=str(ROOT / "runs" / "classify"),
        name=f"{RUN}_test",
        exist_ok=True,      # Reuse the run folder instead of <run>_test2, 3, ...
    )

    print(f"Test accuracy: {metrics.top1:.2%}")


if __name__ == "__main__":
    main()
