# Sensor Memory Benchmark

Gas sensors take a while to catch up when the concentration changes. I wanted to see if keeping a few old readings would help work out what was happening.

I used two recordings from a 16-channel sensor array, one with carbon monoxide and ethylene and one with methane and ethylene. I tried ridge regression with just the latest reading, with some moving averages and a one-second difference, and with five readings spread over 10, 30 or 120 seconds.

The 10-second version uses readings from now and from 1, 2, 5 and 10 seconds ago. It beat the latest-reading model on both MAE and RMSE in all six test periods. The MAE improvement was about 0.9% to 19.3%. I thought a longer history might help more, but it depended on the gas. The version with averages had the lowest methane MAE in all three periods.

![Error changes compared with using the latest reading](results/stage2/comparison_mae.png)

The targets are the lab's gas setpoints. The recordings don't say exactly when the gas reached the sensors. There are three test periods per recording, and the training windows overlap. The [experiment write-up](reports/stage2_robustness.md) and [full tables](reports/stage2_tables.md) have the details.

I also wanted to try making predictions one reading at a time. The Python version keeps the current reading and the last ten in a ring buffer. I replayed all six periods and got the same predictions as the batch model up to rounding. The biggest difference was about 2.3e-12 ppm. [Python replay results](results/streaming/replay_report.json)

The latest-reading and 10-second models now run in C++ too. Python still fits the models and exports the weights. In the desktop replay, the biggest float32 differences from Python were 0.00095 ppm for the latest reading and 0.00214 ppm for the history model. The next thing I want to try is running them on a Pico 2 and measuring how long a prediction takes and how much RAM it uses. [C++ notes](reports/cpp_port.md) · [Comparison results](results/cpp/report.json)

To try it, run these from the repo with Python 3.12. The data download is about 352 MB and stays in `data/`.

```sh
python -m pip install -r requirements-stage2.lock.txt
python -m unittest -v
python stage2.py --download --out results/stage2_reproduction
python replay_streaming.py --out results/streaming_reproduction
python check_cpp.py --compiler g++ --out work/cpp_check
```

Use a fresh output folder each time. The C++ check needs a compiler. The [C++ notes](reports/cpp_port.md) have the command for Zig on Windows. The first experiment is still in `benchmark.py`.

[UCI gas sensor dataset](https://archive.ics.uci.edu/dataset/322/gas+sensor+array+under+dynamic+gas+mixtures) · [Paper that goes with the dataset](https://doi.org/10.1016/j.snb.2015.03.028)
