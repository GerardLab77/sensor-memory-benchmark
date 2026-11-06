# Sensor Memory Benchmark

If a gas sensor is still catching up to a change in concentration, can a few seconds of past readings help estimate what's happening?

I started this project to test that idea using recordings from a 16-channel gas sensor array. The data comes from UCI and contains two mixtures: carbon monoxide with ethylene, and methane with ethylene.

## What I tried

I compared five ridge-regression models. They use the same training data, but get different inputs:

- The latest sensor reading.
- The latest reading, its change from the previous second, and three exponentially weighted averages.
- Five readings spread across the past 10, 30 or 120 seconds.

The 10-second model uses readings from now, 1, 2, 5 and 10 seconds ago. The longer models also use five readings, with different spacing.

I sampled the recordings at 1 Hz and tested each model on three later periods in each recording. Training and validation always come before the test period. Scaling is fitted on training data, and validation error selects the regularisation strength separately for each gas.

## What I found

The 10-second model reduced both mean absolute error (MAE) and root mean squared error (RMSE) for both gases in every test period. Its MAE improvement over the latest-reading model ranged from about 0.9% to 19.3%.

Longer history wasn't always better. The averages gave the lowest methane MAE in all three periods, while the 10-second model did better than the averages on CO. That makes both worth keeping for the next comparison.

![Error changes compared with using the latest reading](results/stage2/comparison_mae.png)

The [Stage 2 report](reports/stage2_robustness.md) has the full results and explains the changes from the first experiment. The [tables](reports/stage2_tables.md) give the errors for every gas and period, and the [experiment plan](reports/stage2_protocol.md) records how the comparison was set up.

There are two important limits to the results. The labels are the lab equipment's concentration setpoints; I don't have a separate measurement of when the gas reached the sensors. Also, these are different periods from two recordings, with overlapping training data. Testing on another recording would tell me more about how well the result carries over.

## Streaming version

The Python streaming model takes one 16-channel reading each second and keeps an 11-reading ring buffer. It uses the same five lags as the batch model, with scaling folded into the weights.

The [saved replay report](results/streaming/replay_report.json) covers all six test periods and produced 72,000 individual gas estimates. The largest difference from the saved batch predictions was about 2.3e-12 ppm. To export the models and repeat the check:

```sh
python replay_streaming.py --out results/streaming_reproduction
```

This uses the saved Stage 2 results and the downloaded dataset. It writes the exported models and a replay report into a new directory.

## Run it

Use Python 3.12. From the repository root:

```sh
python -m pip install -r requirements-stage2.lock.txt
python -m unittest -v
python stage2.py --download --out results/stage2_reproduction
```

The download is about 352 MB. Raw data stays in the Git-ignored `data/` folder. Use a new output directory for each run.

The script saves predictions, error tables, plots, split boundaries, data checksums and environment details. The existing run is in [results/stage2](results/stage2).

The first experiment is still in `benchmark.py`, with its results directly under `results/`. It used one split of the CO/ethylene recording. Stage 2 changed the sampling, tuning and test periods; the report explains those differences.

## Next

The next step is to run the latest-reading, 10-second and average-based models on a Raspberry Pi Pico 2, check their outputs, and measure prediction time and memory use. Hardware measurements are still to come.

There is also later local work on errors after setpoint changes, a small RNN, and timing in the original 100 Hz data. Those scripts and results still need to be brought into this repository.

## Data and reading

- [UCI gas sensor dataset](https://archive.ics.uci.edu/dataset/322/gas+sensor+array+under+dynamic+gas+mixtures), DOI: 10.24432/C5WP4C. See the source for data-use terms.
- Fonollosa et al. (2015), [Reservoir computing compensates slow response of chemosensor arrays exposed to fast varying gas concentrations in continuous monitoring](https://doi.org/10.1016/j.snb.2015.03.028), the paper associated with the dataset.
