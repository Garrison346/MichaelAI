from pathlib import Path
from collections import defaultdict
from PIL import Image
import hashlib

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset" / "classification"

SPLITS = ("train", "val", "test")
CLASSES = ("fire", "nofire")
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

NEAR_DUP_BITS = 4  # Max differing hash bits to count as a near-duplicate
SHOW_EXAMPLES = 5


def dhash(path, size=8):
    # Difference hash: compare each pixel to its right-hand neighbour
    with Image.open(path) as img:
        pixels = img.convert("L").resize((size + 1, size)).tobytes()

    bits = 0
    for row in range(size):
        for col in range(size):
            left = pixels[row * (size + 1) + col]
            right = pixels[row * (size + 1) + col + 1]
            bits = (bits << 1) | (left > right)
    return bits


def check_leakage():
    errors = []
    images = []

    # Gather all images
    for split in SPLITS:
        for cls in CLASSES:
            class_dir = DATASET / split / cls

            if not class_dir.is_dir():
                errors.append(f"Missing class directory: {class_dir}")
                continue

            paths = sorted(
                p for p in class_dir.iterdir()
                if p.is_file() and p.suffix.lower() in EXTENSIONS
            )
            print(f"{split}/{cls}: {len(paths)}")
            images += [(split, cls, p) for p in paths]

    # Roboflow augmentations share the name before ".rf."
    group_splits = defaultdict(set)
    hash_splits = defaultdict(set)
    hash_classes = defaultdict(set)
    hash_paths = defaultdict(list)

    for split, cls, path in images:
        group_splits[path.name.split(".rf.")[0]].add(split)

        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        hash_splits[file_hash].add(split)
        hash_classes[file_hash].add(cls)
        hash_paths[file_hash].append(path)

    print(f"\nImage groups: {len(group_splits)}")

    for group, splits in group_splits.items():
        if len(splits) > 1:
            errors.append(f"Group in multiple splits: {group} ({', '.join(sorted(splits))})")

    for file_hash, splits in hash_splits.items():
        if len(splits) > 1:
            paths = ", ".join(str(p) for p in hash_paths[file_hash])
            errors.append(f"Cross-split duplicate: {paths}")

    for file_hash, classes in hash_classes.items():
        if len(classes) > 1:
            paths = ", ".join(str(p) for p in hash_paths[file_hash])
            errors.append(f"Same image in both classes: {paths}")

    # Near-duplicates: visually similar images with different files
    print("\nNEAR-DUPLICATES OF TRAIN IMAGES")
    train_hashes = [dhash(p) for split, _, p in images if split == "train"]

    for split in SPLITS[1:]:
        matches = []
        split_paths = [p for s, _, p in images if s == split]

        for path in split_paths:
            image_hash = dhash(path)
            distance = min(
                (image_hash ^ train_hash).bit_count()
                for train_hash in train_hashes
            )
            if distance <= NEAR_DUP_BITS:
                matches.append(path.name)

        share = len(matches) / len(split_paths) if split_paths else 0
        print(f"  {split}: {len(matches)} of {len(split_paths)} ({share:.1%})")
        for name in matches[:SHOW_EXAMPLES]:
            print(f"    {name}")

    if errors:
        print("\nLEAKAGE CHECK FAILED")
        for error in errors:
            print(f"  - {error}")
        return False

    print("\nLeakage check passed!")
    return True


if __name__ == "__main__":
    if not check_leakage():
        raise SystemExit(1)
