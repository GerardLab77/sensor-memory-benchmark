# Stage 2 protocol — fixed before new test evaluation

The executable specification is `stage2_config.json`. Freeze this document and
configuration in Git before running Stage 2. The original commit is `26706fa`.

Question: does sensor history reduce per-gas estimation errors across both UCI
322 mixtures and three chronological periods? Preserve current, summary and
sparse 10/30/120-second ridge families. No new model family or test-driven tuning.

Use the latest raw observation at or before each integer elapsed second, relative
to the first timestamp. Validate every raw row, not just a stride subset. This is
causal point sampling, not averaging or anti-alias filtering. Targets use the same
row as sensors. Log source age and raw gaps; do not interpolate future targets.
Abort if recordings do not cover all windows or any gas is constant within any
partition. Such a failure requires a documented protocol revision before fitting.

All intervals are half-open elapsed seconds:

| Fold | Train | Validation | Test |
|---|---|---|---|
| 1 | [600,18000) | [18600,21600) | [22200,28200) |
| 2 | [600,24000) | [24600,27600) | [28200,34200) |
| 3 | [600,30000) | [30600,33600) | [34200,40200) |

Initial 600 seconds warm up features. Gaps of 600 seconds are excluded from
fitting/scoring, while sensor-only state carries through them and all boundaries.
EWMAs start at the first reading and use `1-exp(-dt/tau)` for tau 5, 30, 120 seconds;
their infinite support means gaps do not create independent observations. Features
include current readings, one-second differences and three EWMAs (80 features).
Sparse lags retain the original five offsets, now explicitly in seconds (80
features), not all samples of a complete history buffer. Current uses 16 features.
All models have identical training, validation and test timestamps.

Fit StandardScaler and ridge coefficients on training only. Select alpha from
0.1, 1, 10, 100 independently for each gas using validation MAE, first candidate
on ties. No refit, clipping, label features, target scaling or test-based choices.
Changes from the exploratory run: full-stream point sampling, exact EWMA time
constants, per-target alpha selection and multiple fixed-time windows. Therefore
Stage 2 is not a controlled single-factor replication of the original numbers.

Report MAE and RMSE in ppm for every model/gas/fold. Pair temporal errors with
current errors from the same gas and fold: delta = temporal minus current;
percent delta = 100 * delta/current. Negative is improvement. With a zero current
error report null percentage and an explicit status, even if both errors are zero.
Report ranges, means, SDs, quantiles and number of unique targets in each partition.
No pooled score across unlike gases, significance tests or independent-fold CIs.
Training windows overlap; later training/validation may include earlier test
periods, as in an expanding-window deployment. Models are always trained afresh.

Save all predictions. Plot paired MAE and RMSE percentage changes separately by
mixture/gas; use fold 2's first 600 test seconds for representative predictions,
chosen in advance rather than selecting a favourable period. Record archive and
member SHA256, config/code hashes, Git revision, package versions and split times.
One scientific run; retries for infrastructure or code correctness must be logged,
never used to select favourable models/results.
