
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset" / "classification"


'''
Dataset Split:
Training: ~87.3% 
Validation: ~8.5%
Test: ~4.2%     
'''

def main():
    model = YOLO("yolov8n-cls.pt")

    model.train(
        data=str(DATASET),  # Classification dataset
        epochs=40,          # Maximum training epochs
        imgsz=224,          # Image resolution (224x224)
        batch=32,           # Images per optimization step
        patience=10,        # Early stopping
        workers=2,          # Parallel data-loading processes
        seed=42,            # Reproducibility
        device=0,           # NVIDIA GTX 1650 (CUDA)
        project=str(ROOT / "runs" / "classify"),  # Output directory
        name="fire_baseline",  # Experiment name
        exist_ok=True,      # Reuse the run folder instead of fire_baseline2, 3, ...
    )


if __name__ == "__main__":
    main()
