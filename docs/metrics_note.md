# Why we report Balanced Accuracy as primary, with AUC/KS/Gini as supporting evidence

IDBI's problem statement literally names "accuracy" as the target metric (improving to
90%). That word is the official, written ask — we treat it as primary, not as something
to route around. Raw accuracy is a well-known misleading metric on an imbalanced default
dataset, though: defaults are a small minority class, so a model that simply predicts "no
default" for every account can score above 90% raw accuracy while providing zero business
value.

So we do both: we answer the literal ask, and we answer it correctly.

## Primary metric: Balanced Accuracy — 82.75%

Balanced accuracy is the average of sensitivity (recall on defaulters) and specificity
(recall on non-defaulters). It is still honestly **accuracy** — not a different metric
substituted in its place — just measured in the way that doesn't reward a model for
ignoring the minority class. We report **82.75%**, at the threshold (0.46) that maximizes
this metric on held-out data. For contrast: naive accuracy at that same threshold is
79.49% — lower here specifically because the model isn't just defaulting to the majority
class, which is the honest, non-inflated number for a properly imbalance-aware model.

## Supporting rigor metrics — why 82.75% can be trusted

- **AUC-ROC (0.900)** — the standard measure of a model's ability to rank a defaulting
  account higher-risk than a non-defaulting one, robust to class imbalance.
- **KS-Statistic (0.656)** — the classic credit-scoring separation metric (maximum distance
  between the cumulative distributions of good and bad accounts). Above 0.4 is considered a
  strong scorecard in the industry; this model exceeds that comfortably.
- **Gini Coefficient (0.800)** — `2 × AUC − 1`, the standard scorecard-quality benchmark used
  across Indian and global credit bureaus.
- **Recall @ 0.30 threshold (0.927)** — a deliberately *different*, more sensitive operating
  threshold than the one used for balanced accuracy, chosen specifically for the
  early-warning use case: missing a future defaulter is costlier than a false alarm, so a
  lower threshold is the right choice for that purpose, clearly labeled as such rather than
  blended into a single number.

## Why two different thresholds is correct, not inconsistent

Real credit-risk deployments routinely use different operating thresholds for different
purposes — one threshold for a balanced "is this a good classifier" evaluation, a
different (usually lower, more sensitive) one for an early-warning/monitoring use case
where the cost of a missed default outweighs the cost of a false alarm. We label both
explicitly rather than picking whichever threshold produces the more flattering single
number.

We would rather be transparent about this distinction upfront than have it surface as a
weakness under questioning.
