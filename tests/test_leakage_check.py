import shutil

import pytest
from PIL import Image

import check_classification_leakage as leakage

SPLITS = ("train", "val", "test")
CLASSES = ("fire", "nofire")


def save_image(path, colour):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 16), colour).save(path)


@pytest.fixture
def dataset(tmp_path, monkeypatch):
    # Tiny clean dataset: unique names and a unique colour per image
    colour = 0
    for split in SPLITS:
        for cls in CLASSES:
            for i in range(2):
                colour += 10
                save_image(tmp_path / split / cls / f"{split}_{cls}_{i}.png", (colour, 0, 0))

    monkeypatch.setattr(leakage, "DATASET", tmp_path)
    return tmp_path


def test_clean_dataset_passes(dataset):
    assert leakage.check_leakage() is True


def test_cross_split_duplicate_fails(dataset):
    shutil.copy(dataset / "train" / "fire" / "train_fire_0.png", dataset / "test" / "fire" / "copy.png")

    assert leakage.check_leakage() is False


def test_same_image_in_both_classes_fails(dataset):
    shutil.copy(dataset / "train" / "fire" / "train_fire_0.png", dataset / "train" / "nofire" / "copy.png")

    assert leakage.check_leakage() is False


def test_roboflow_group_across_splits_fails(dataset):
    # Different pixels, same name before ".rf.", so only the group check catches it
    save_image(dataset / "train" / "fire" / "x_jpg.rf.a.png", (0, 200, 0))
    save_image(dataset / "val" / "fire" / "x_jpg.rf.b.png", (0, 0, 200))

    assert leakage.check_leakage() is False
