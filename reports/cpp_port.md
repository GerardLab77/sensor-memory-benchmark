# Python to C++: current readings and ten seconds of history

The first C++ version keeps the two existing ridge models and changes how predictions are calculated. Training still happens in Python. The C++ code only needs the fitted weights and incoming readings.

## The calculation

For one output gas, Python's fitted model calculates:

```text
prediction = intercept + sum(coefficient[i] * (feature[i] - mean[i]) / scale[i])
```

We can rearrange that once when exporting the model:

```text
weight[i] = coefficient[i] / scale[i]
bias = intercept - sum(mean[i] * weight[i])
prediction = bias + sum(feature[i] * weight[i])
```

That removes the separate scaling step during inference. Each gas has its own weights and bias. The current-reading model has 16 features and 32 weights in total. The lag model has 80 features and 160 weights.

The exporter refits using the existing training and validation settings, then checks those predictions against the saved Stage 2 predictions before using its weights.

## Why eleven buffer slots?

At one reading per second, the lag model uses five vectors: now, one, two, five and ten seconds ago. To have the ten-second-old vector available on every update, the ring buffer holds eleven vectors.

Each update moves the write position forward by one, wrapping back to zero at the end. A lag is found by counting backwards from that position. Nothing needs to be shifted through memory.

At startup, the buffer repeats the first reading, matching the Python convention. For the recorded test periods, ten preceding readings fill the buffer before scoring starts. Calling `reset()` returns to the startup behaviour.

Both models expect 16 finite values in the dataset's channel order. They assume calls are one second apart; they do not infer elapsed time from a timestamp. Invalid input returns `false` without changing the output or history. A caller must handle a missed second explicitly: resample upstream as the dataset loader does, or reset and treat the next ten seconds as startup. Simply skipping a missing second would make the lag ages wrong.

## Files

- [sensor_model.hpp](../cpp/sensor_model.hpp): the prediction code, using fixed-size arrays and no heap allocation.
- [replay.cpp](../cpp/replay.cpp): a desktop adapter that reads model parameters and readings from text files.
- [test_sensor_model.cpp](../cpp/test_sensor_model.cpp): small checks for known outputs, startup, repeated wraparound, reset and invalid input.
- [check_cpp.py](../check_cpp.py): builds both precisions, exports fitted parameters, runs the recorded inputs and compares results.

The parameter arrays must outlive the model instance. The header uses references so weights are not copied into each instance. A Pico program can keep these parameters in constant storage and call the same update function.

The text replay format is just for desktop checking. Model files contain weights in lag/channel/gas order followed by the two biases. Input files begin with a reading count, then one row of 16 values per update. Exported NPZ files retain the parameter arrays and gas names, and the JSON report records the selected alphas and source hashes.

## Run the comparison

Install the Python dependencies from the repository README and download the dataset first. Use a GCC- or Clang-compatible C++ compiler:

```sh
python check_cpp.py --compiler g++ --out work/cpp_check
```

For a portable Zig compiler on Windows, its C++ driver also works:

```powershell
python check_cpp.py --compiler C:/path/to/zig.exe c++ --out work/cpp_check
```

Use a new output folder each time. The script builds the C++ tests and replay programs, then checks current and lag models for both mixtures and all three periods. Each precision produces 144,000 scored gas estimates: two models times six periods times 6,000 readings times two gases. Ten priming updates per model/period are checked separately from the scored outputs.

The output includes `report.json`, parameters, input fixtures and prediction comparisons. Builds and fixtures belong in the ignored `work/` directory; a compact report can be kept under `results/cpp/`.

## What counts as agreement?

The checks use two builds:

1. **Float64:** compare the C++ calculation with the saved Python predictions. The absolute tolerance is 1e-8 ppm. This checks the formula and feature alignment without introducing float32 conversion.
2. **Float32:** convert inputs and parameters to the precision intended for the board. Compare against both the original predictions and a separate Python calculation that performs the multiply/add operations in the same order.

The limits were set before running the C++ comparison:

- Maximum float32 disagreement with saved Python predictions: 0.01 ppm.
- Absolute change in MAE: at most 0.1% of the original MAE, for every gas/model/period.
- Maximum disagreement with the ordered Python float32 calculation: 1e-6 ppm.

These are numerical checks for the port, not requirements for a gas-monitoring application. RMSE and maximum pointwise differences are also saved. The compiler flags disable fast-math and fused multiply-add contraction to make the desktop arithmetic comparison easier to inspect.

## What is left for the board?

The float32 history array contains 11 x 16 floats: 704 bytes. Current-model parameters contain 34 floats (136 bytes); lag-model parameters contain 162 floats (648 bytes). These counts exclude the object bookkeeping, stack, input/output buffers and firmware.

Desktop agreement checks the implementation. Prediction time, total RAM and behaviour with the Pico compiler still need to be measured on the board.


## Desktop result

The comparison passed on Windows with Zig 0.15.2's Clang 20.1.2 C++ driver. The full [report](../results/cpp/report.json) records the compiler flags and source hashes.

| Model | Largest float32 difference from Python (ppm) | Largest absolute relative MAE change (%) |
|---|---:|---:|
| Latest reading | 0.00095324 | 0.00008695 |
| 10-second history | 0.00213705 | 0.00020853 |

Both precisions replayed 144,000 scored gas estimates. The largest float64 disagreement with saved Python predictions was 3.98e-12 ppm. C++ float32 matched the ordered Python float32 calculation exactly, including startup updates. All C++ state checks and the existing 15 Python tests passed.
