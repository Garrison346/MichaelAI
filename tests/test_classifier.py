from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from src.perception import classifier as classifier_module
from src.perception.classifier import FireClassifier

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "runs" / "classify" / "fire_baseline" / "weights" / "best.pt"
FIRE_IMAGES = ROOT / "dataset" / "classification" / "test" / "fire"


class FakeYOLO:
    # Stands in for ultralytics.YOLO inside classifier.py only
    def __init__(self, names, probs):
        self.names = names
        self.probs = probs

    def predict(self, **kwargs):
        probs = SimpleNamespace(data=torch.tensor(self.probs))
        return [SimpleNamespace(probs=probs)]


@pytest.fixture
def weights_file(tmp_path):
    path = tmp_path / "best.pt"
    path.touch()
    return path


def use_fake_model(monkeypatch, names, probs=(0.5, 0.5)):
    monkeypatch.setattr(
        classifier_module, "YOLO", lambda _: FakeYOLO(names, list(probs))
    )


def test_missing_weights_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        FireClassifier(tmp_path / "missing.pt")


def test_wrong_class_names_rejected(monkeypatch, weights_file):
    use_fake_model(monkeypatch, {0: "cat", 1: "fire"})

    with pytest.raises(ValueError):
        FireClassifier(weights_file)


def test_fire_probability_with_reversed_class_order(monkeypatch, weights_file):
    use_fake_model(monkeypatch, {0: "nofire", 1: "fire"}, probs=(0.1, 0.9))

    prediction = FireClassifier(weights_file).predict("image.jpg")

    assert prediction["fire_probability"] == pytest.approx(0.9)
    assert prediction["is_fire"] is True
    assert prediction["label"] == "fire"


@pytest.mark.skipif(not WEIGHTS.is_file(), reason="Trained weights not found")
def test_classifies_real_image():
    image = next(FIRE_IMAGES.iterdir())

    prediction = FireClassifier(WEIGHTS).predict(str(image))

    assert {"label", "fire_probability", "is_fire"} <= prediction.keys()
    assert 0 <= prediction["fire_probability"] <= 1
