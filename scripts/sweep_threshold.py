import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset" / "classification"
RUN = "fire_baseline"  # Training run to sweep
WEIGHTS = ROOT / "runs" / "classify" / RUN / "weights" / "best.pt"
THRESHOLDS = (0.5, 0.4, 0.3)

# Make src/ importable when run as `python scripts/sweep_threshold.py`
sys.path.insert(0, str(ROOT))
from src.perception.classifier import FireClassifier


def main():
    classifier = FireClassifier(WEIGHTS, device=0)

    # Predict once; thresholds only change how fire_probability is read
    samples = []
    for true_label in ("fire", "nofire"):
        for path in sorted((DATASET / "test" / true_label).glob("*.jpg")):
            fire_probability = classifier.predict(str(path))["fire_probability"]
            samples.append((true_label, fire_probability, path.name))

    n_fire = sum(label == "fire" for label, _, _ in samples)
    n_nofire = len(samples) - n_fire
    print(f"Run: {RUN}")
    print(f"Test images: {len(samples)} ({n_fire} fire, {n_nofire} nofire)\n")
    print(f"{'threshold':>9} | {'accuracy':>8} | {'fire recall':>11} | {'missed fires':>12} | {'false alarms':>12}")
    print("-" * 65)

    for threshold in THRESHOLDS:
        missed = sum(label == "fire" and p < threshold for label, p, _ in samples)
        false_alarms = sum(label == "nofire" and p >= threshold for label, p, _ in samples)
        accuracy = 1 - (missed + false_alarms) / len(samples)
        recall = 1 - missed / n_fire
        print(f"{threshold:>9.1f} | {accuracy:>8.2%} | {recall:>11.2%} | {missed:>12} | {false_alarms:>12}")

    # List the actual images behind the numbers
    lowest = min(THRESHOLDS)
    print(f"\nMissed fires at {max(THRESHOLDS)} (lowest fire probability first):")
    for label, p, name in sorted(samples, key=lambda s: s[1]):
        if label == "fire" and p < max(THRESHOLDS):
            print(f"  {p:.3f}  {name}")

    print(f"\nFalse alarms at {lowest} (highest fire probability first):")
    for label, p, name in sorted(samples, key=lambda s: -s[1]):
        if label == "nofire" and p >= lowest:
            print(f"  {p:.3f}  {name}")


if __name__ == "__main__":
    main()
