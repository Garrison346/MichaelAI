from pathlib import Path
from types import SimpleNamespace

import cv2
import pytest
import torch

from src.perception import classifier as classifier_module
from src.perception.classifier import FireClassifier

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "models" / "fire_baseline.pt"
# Committed images, so real-model tests run on a fresh clone without the dataset
SAMPLE_IMAGES = ROOT / "dataset" / "classification" / "test_hard"


class FakeYOLO:
    # Stands in for ultralytics.YOLO inside classifier.py only
    def __init__(self, names, probs):
        self.names = names
        self.probs = probs

    def predict(self, **kwargs):
        # probs=None mimics a model that returns no class probabilities
        probs = None if self.probs is None else SimpleNamespace(data=torch.tensor(self.probs))
        return [SimpleNamespace(probs=probs)]


@pytest.fixture
def weights_file(tmp_path):
    path = tmp_path / "best.pt"
    path.touch()
    return path


def use_fake_model(monkeypatch, names, probs=(0.5, 0.5)):
    monkeypatch.setattr(
        classifier_module, "YOLO",
        lambda _: FakeYOLO(names, None if probs is None else list(probs)),
    )


def sample_image():
    return next(SAMPLE_IMAGES.glob("*/*.jpg"))


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


def test_no_probabilities_raises(monkeypatch, weights_file):
    # A failed prediction must raise, never come back as "nofire"
    use_fake_model(monkeypatch, {0: "fire", 1: "nofire"}, probs=None)

    with pytest.raises(ValueError):
        FireClassifier(weights_file).predict("image.jpg")


@pytest.mark.parametrize("threshold", [-0.1, 1.5])
def test_threshold_out_of_range_rejected(monkeypatch, weights_file, threshold):
    use_fake_model(monkeypatch, {0: "fire", 1: "nofire"})

    with pytest.raises(ValueError):
        FireClassifier(weights_file, threshold=threshold)


def test_threshold_boundary_counts_as_fire(monkeypatch, weights_file):
    # 0.25 is exact in float32, so this pins >= rather than >
    use_fake_model(monkeypatch, {0: "fire", 1: "nofire"}, probs=(0.25, 0.75))

    prediction = FireClassifier(weights_file, threshold=0.25).predict("image.jpg")

    assert prediction["is_fire"] is True
    assert prediction["label"] == "fire"
    assert prediction["nofire_probability"] == pytest.approx(0.75)


@pytest.mark.skipif(not WEIGHTS.is_file(), reason="Trained weights not found")
def test_classifies_real_image():
    image = sample_image()

    prediction = FireClassifier(WEIGHTS).predict(str(image))

    assert {"label", "fire_probability", "is_fire"} <= prediction.keys()
    assert 0 <= prediction["fire_probability"] <= 1


@pytest.mark.skipif(not WEIGHTS.is_file(), reason="Trained weights not found")
def test_classifies_camera_frame():
    # The robot passes OpenCV frames (numpy BGR arrays), not file paths
    frame = cv2.imread(str(sample_image()))

    prediction = FireClassifier(WEIGHTS).predict(frame)

    assert 0 <= prediction["fire_probability"] <= 1
