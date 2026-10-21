---
name: evaluate-fire-classifier
description: Train, evaluate, and report on the MichaelAI fire/nofire classifier. Use when training a new classifier run, evaluating weights on the test set, sweeping thresholds, or comparing a new model against the baseline.
---

# Evaluate the MichaelAI fire classifier

Run every model through the same steps so results stay comparable between
runs and between collaborators. Commands assume the repo root on Windows with
`.venv` active.

## Ground rules

- **Don't tune on the test set.** Pick the epoch from validation (`best.pt`
  does this) and the threshold from the sweep below, then report test numbers once.
- **Missed fires matter more than false alarms.** Always report the
  missed-fire count, not only accuracy.
- **Small sets are noisy.** With 213 fire test images, one miss moves recall
  by ~0.5%. Treat differences of 1-2% between runs as noise.
- **Never train on test images.** Anything collected to fix a failure case
  goes into `train/`, never into `test/`.

## Steps

### 1. Check the data (only if the dataset changed)

```
python scripts/check_classification_leakage.py
```

Stop if it fails. A failure means a Roboflow group or exact duplicate crosses
splits, or one image sits under both classes, and every downstream number
would be inflated. The near-duplicate count it prints is informational
(baseline: ~6% of test).

Don't use `scripts/check_dataset.py` here; it checks the detection dataset.

### 2. Train

Set `name=` in `scripts/train_classifier.py` to a new descriptive run name
(e.g. `fire_v2_hardneg`). The script uses `exist_ok=True`, so **reusing a
name overwrites that run**. Then:

```
python scripts/train_classifier.py
```

Run it in the background. `runs/classify/<name>/results.csv` gains one row per
epoch, so watch that for progress (and the log for `Traceback` / `out of memory`).
Training is finished only when the output prints
`Results saved to runs/classify/<name>`. Record the
`Best results observed at epoch N` line and the epoch it stopped at.
Don't evaluate `best.pt` before that, because it changes during training.

From `runs/classify/<name>/results.png`, note:
- whether train loss keeps falling while val loss and val accuracy plateau
  (expected; early stopping handles it)
- whether val loss rises steadily (overfitting; report it)
- ignore `accuracy_top5`; with 2 classes it is always 1.0

### 3. Test set + threshold sweep

Set `RUN = "<name>"` at the top of both scripts, then:

```
python scripts/evaluate_classifier.py
python scripts/sweep_threshold.py
```

`evaluate_classifier.py` prints test accuracy and saves the confusion matrix
to `runs/classify/<name>_test/`. `sweep_threshold.py` prints accuracy, fire
recall, missed fires and false alarms at 0.5 / 0.4 / 0.3, then lists the
missed fires and false alarms by filename.

Choose the highest threshold that has the lowest missed-fire count. Lowering
the threshold is only worth it if it catches more fires.

### 4. Look at the errors

Open every missed fire and the highest-probability false alarms from the sweep
output (`dataset/classification/test/<class>/<file>`). Note what they show
(sunset, haze, small flame, dark scene...). A false alarm above 0.9 can't be
fixed by thresholds; it needs more training data of that kind.

### 5. Compare against the baseline

Baseline `fire_baseline`: best.pt from epoch 22 (stopped early at 32),
threshold 0.5, test accuracy 98.80%, 213/213 fires caught, 5 false alarms
(sunset and cloud/haze scenes; worst `NF_126` at 0.987, `NF_496` at 0.973).

If the new model is adopted, update the README "Baseline Results" table and
`RUN_DIR` in `dashboard/app.py`.

## Report format

```
Run: <name>   Best epoch: N   Stopped early: yes/no (at epoch M)
Test (threshold T):  accuracy X%  |  fires caught A/B  |  false alarms C
Missed-fire rate: X%  (if 0 misses: <= 3/B, rule of three, 95%)
New failures vs baseline: <images that flipped the wrong way>
Fixed vs baseline:        <images that flipped the right way>
Verdict: better / same within noise / worse, and why
```

When there are zero missed fires, report the upper bound `3 / number of fire
images` (3/213 ≈ 1.4% for the current test set) rather than claiming a 0% miss rate.

If a hard-negative test set is added later, extend step 3 to evaluate it too.
