from pathlib import Path

from ultralytics import YOLO


class FireClassifier:
    def __init__(self, model_path: str, device="cpu", threshold=0.5):
        # Check that the model exists and the threshold is valid
        if not Path(model_path).is_file():
            raise FileNotFoundError(f"Model not found: {model_path}")
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")

        # Load the trained classification model
        self.model = YOLO(str(model_path))
        self.device = device
        self.threshold = threshold

        # Must be a fire/nofire model
        names = self.model.names
        if {name.lower() for name in names.values()} != {"fire", "nofire"}:
            raise ValueError("Expected fire and nofire classes")

        # Find the fire class index
        self.fire_id = next(
            class_id
            for class_id, name in names.items()
            if name.lower() == "fire"
        )

    def predict(self, image):
        # Run inference on an image path or camera frame
        # Bad or empty images raise here; never treat a failure as "nofire"
        result = self.model.predict(
            source=image,
            device=self.device,
            verbose=False,
        )[0]

        # Extract class probabilities
        probabilities = result.probs

        if probabilities is None:
            raise ValueError("Expected a YOLO classification model")

        fire_probability = float(
            probabilities.data[self.fire_id]
        )

        # Binary classification probabilities
        nofire_probability = 1.0 - fire_probability

        is_fire = fire_probability >= self.threshold

        return {
            "label": "fire" if is_fire else "nofire",
            "fire_probability": fire_probability,
            "nofire_probability": nofire_probability,
            "is_fire": is_fire,
        }
