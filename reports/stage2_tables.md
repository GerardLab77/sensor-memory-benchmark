# Stage 2 complete result tables

Rendered from `results/stage2/metrics.json` and `distributions.csv`. All errors and absolute deltas are in ppm. Negative deltas mean lower error than current on the same gas/period. Percentages are not pooled. Full precision remains in the source files.

## Per-gas, per-model, per-period errors and paired changes

| Mixture / gas | Fold | Model | Alpha | MAE | MAE delta | MAE change % | RMSE | RMSE delta | RMSE change % |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| ethylene_CO / CO | 1 | current | 1.0 | 51.2894 | 0.0000 | 0.0000 | 79.4255 | 0.0000 | 0.0000 |
| ethylene_CO / ethylene | 1 | current | 0.1 | 2.4031 | 0.0000 | 0.0000 | 3.3173 | 0.0000 | 0.0000 |
| ethylene_CO / CO | 1 | summary | 100.0 | 43.9239 | -7.3655 | -14.3607 | 76.2565 | -3.1690 | -3.9899 |
| ethylene_CO / ethylene | 1 | summary | 100.0 | 2.2581 | -0.1450 | -6.0341 | 3.2785 | -0.0388 | -1.1697 |
| ethylene_CO / CO | 1 | lags_10s | 10.0 | 41.3804 | -9.9090 | -19.3198 | 74.3821 | -5.0434 | -6.3499 |
| ethylene_CO / ethylene | 1 | lags_10s | 0.1 | 2.2695 | -0.1336 | -5.5591 | 3.1740 | -0.1433 | -4.3207 |
| ethylene_CO / CO | 1 | lags_30s | 10.0 | 42.5449 | -8.7445 | -17.0493 | 74.4350 | -4.9905 | -6.2833 |
| ethylene_CO / ethylene | 1 | lags_30s | 0.1 | 2.4035 | 0.0004 | 0.0182 | 3.2846 | -0.0327 | -0.9851 |
| ethylene_CO / CO | 1 | lags_120s | 10.0 | 46.6327 | -4.6567 | -9.0793 | 75.3865 | -4.0390 | -5.0852 |
| ethylene_CO / ethylene | 1 | lags_120s | 100.0 | 2.5520 | 0.1489 | 6.1961 | 3.4263 | 0.1090 | 3.2846 |
| ethylene_CO / CO | 2 | current | 10.0 | 69.7451 | 0.0000 | 0.0000 | 111.2411 | 0.0000 | 0.0000 |
| ethylene_CO / ethylene | 2 | current | 0.1 | 1.9589 | 0.0000 | 0.0000 | 3.1999 | 0.0000 | 0.0000 |
| ethylene_CO / CO | 2 | summary | 100.0 | 64.0417 | -5.7034 | -8.1774 | 109.5543 | -1.6868 | -1.5164 |
| ethylene_CO / ethylene | 2 | summary | 0.1 | 1.9401 | -0.0188 | -0.9596 | 3.0497 | -0.1502 | -4.6936 |
| ethylene_CO / CO | 2 | lags_10s | 10.0 | 60.1540 | -9.5911 | -13.7517 | 107.0959 | -4.1452 | -3.7263 |
| ethylene_CO / ethylene | 2 | lags_10s | 0.1 | 1.9412 | -0.0177 | -0.9037 | 3.0394 | -0.1606 | -5.0180 |
| ethylene_CO / CO | 2 | lags_30s | 100.0 | 61.7363 | -8.0088 | -11.4829 | 109.7093 | -1.5318 | -1.3770 |
| ethylene_CO / ethylene | 2 | lags_30s | 0.1 | 1.9029 | -0.0561 | -2.8630 | 3.0051 | -0.1949 | -6.0893 |
| ethylene_CO / CO | 2 | lags_120s | 100.0 | 63.4785 | -6.2667 | -8.9851 | 106.5284 | -4.7127 | -4.2364 |
| ethylene_CO / ethylene | 2 | lags_120s | 0.1 | 2.1019 | 0.1429 | 7.2969 | 3.1797 | -0.0202 | -0.6312 |
| ethylene_CO / CO | 3 | current | 100.0 | 44.0361 | 0.0000 | 0.0000 | 71.6032 | 0.0000 | 0.0000 |
| ethylene_CO / ethylene | 3 | current | 10.0 | 2.2364 | 0.0000 | 0.0000 | 3.1619 | 0.0000 | 0.0000 |
| ethylene_CO / CO | 3 | summary | 0.1 | 43.3494 | -0.6867 | -1.5593 | 68.0460 | -3.5572 | -4.9679 |
| ethylene_CO / ethylene | 3 | summary | 0.1 | 1.9114 | -0.3250 | -14.5336 | 2.8374 | -0.3245 | -10.2613 |
| ethylene_CO / CO | 3 | lags_10s | 10.0 | 42.8942 | -1.1419 | -2.5930 | 70.6260 | -0.9772 | -1.3647 |
| ethylene_CO / ethylene | 3 | lags_10s | 0.1 | 1.9958 | -0.2406 | -10.7583 | 2.9432 | -0.2187 | -6.9153 |
| ethylene_CO / CO | 3 | lags_30s | 100.0 | 38.0660 | -5.9701 | -13.5572 | 69.1003 | -2.5029 | -3.4955 |
| ethylene_CO / ethylene | 3 | lags_30s | 0.1 | 1.9717 | -0.2647 | -11.8343 | 2.9144 | -0.2475 | -7.8280 |
| ethylene_CO / CO | 3 | lags_120s | 100.0 | 42.2229 | -1.8132 | -4.1175 | 71.6114 | 0.0082 | 0.0114 |
| ethylene_CO / ethylene | 3 | lags_120s | 10.0 | 1.9536 | -0.2828 | -12.6439 | 2.8877 | -0.2742 | -8.6706 |
| ethylene_methane / methane | 1 | current | 1.0 | 24.5769 | 0.0000 | 0.0000 | 51.1125 | 0.0000 | 0.0000 |
| ethylene_methane / ethylene | 1 | current | 1.0 | 2.3043 | 0.0000 | 0.0000 | 3.5048 | 0.0000 | 0.0000 |
| ethylene_methane / methane | 1 | summary | 100.0 | 22.4747 | -2.1022 | -8.5536 | 47.9433 | -3.1692 | -6.2004 |
| ethylene_methane / ethylene | 1 | summary | 100.0 | 2.0997 | -0.2046 | -8.8791 | 3.2308 | -0.2741 | -7.8194 |
| ethylene_methane / methane | 1 | lags_10s | 100.0 | 23.2034 | -1.3736 | -5.5889 | 50.2059 | -0.9066 | -1.7737 |
| ethylene_methane / ethylene | 1 | lags_10s | 10.0 | 2.1376 | -0.1667 | -7.2347 | 3.3057 | -0.1991 | -5.6805 |
| ethylene_methane / methane | 1 | lags_30s | 100.0 | 23.3846 | -1.1923 | -4.8514 | 50.1244 | -0.9881 | -1.9331 |
| ethylene_methane / ethylene | 1 | lags_30s | 1.0 | 2.0989 | -0.2054 | -8.9123 | 3.2366 | -0.2682 | -7.6530 |
| ethylene_methane / methane | 1 | lags_120s | 1.0 | 22.6592 | -1.9178 | -7.8031 | 44.9486 | -6.1638 | -12.0594 |
| ethylene_methane / ethylene | 1 | lags_120s | 1.0 | 2.0188 | -0.2855 | -12.3887 | 3.0855 | -0.4193 | -11.9647 |
| ethylene_methane / methane | 2 | current | 10.0 | 24.2935 | 0.0000 | 0.0000 | 43.8030 | 0.0000 | 0.0000 |
| ethylene_methane / ethylene | 2 | current | 0.1 | 1.9542 | 0.0000 | 0.0000 | 3.2382 | 0.0000 | 0.0000 |
| ethylene_methane / methane | 2 | summary | 1.0 | 18.9203 | -5.3732 | -22.1180 | 39.8828 | -3.9202 | -8.9496 |
| ethylene_methane / ethylene | 2 | summary | 1.0 | 1.9927 | 0.0385 | 1.9720 | 3.1306 | -0.1077 | -3.3249 |
| ethylene_methane / methane | 2 | lags_10s | 10.0 | 21.2562 | -3.0374 | -12.5027 | 41.7314 | -2.0716 | -4.7294 |
| ethylene_methane / ethylene | 2 | lags_10s | 0.1 | 1.8599 | -0.0942 | -4.8213 | 3.0499 | -0.1884 | -5.8171 |
| ethylene_methane / methane | 2 | lags_30s | 10.0 | 20.6322 | -3.6614 | -15.0714 | 41.2079 | -2.5950 | -5.9243 |
| ethylene_methane / ethylene | 2 | lags_30s | 1.0 | 1.9564 | 0.0023 | 0.1170 | 3.0999 | -0.1384 | -4.2724 |
| ethylene_methane / methane | 2 | lags_120s | 10.0 | 21.1076 | -3.1859 | -13.1144 | 39.4267 | -4.3763 | -9.9909 |
| ethylene_methane / ethylene | 2 | lags_120s | 0.1 | 1.9738 | 0.0196 | 1.0035 | 3.1198 | -0.1184 | -3.6567 |
| ethylene_methane / methane | 3 | current | 0.1 | 17.0178 | 0.0000 | 0.0000 | 32.0200 | 0.0000 | 0.0000 |
| ethylene_methane / ethylene | 3 | current | 1.0 | 2.2113 | 0.0000 | 0.0000 | 3.5672 | 0.0000 | 0.0000 |
| ethylene_methane / methane | 3 | summary | 10.0 | 14.0727 | -2.9451 | -17.3058 | 29.2158 | -2.8042 | -8.7576 |
| ethylene_methane / ethylene | 3 | summary | 0.1 | 2.1116 | -0.0997 | -4.5106 | 3.3929 | -0.1743 | -4.8863 |
| ethylene_methane / methane | 3 | lags_10s | 0.1 | 15.9440 | -1.0738 | -6.3100 | 29.4797 | -2.5404 | -7.9337 |
| ethylene_methane / ethylene | 3 | lags_10s | 1.0 | 2.0190 | -0.1923 | -8.6956 | 3.3424 | -0.2248 | -6.3024 |
| ethylene_methane / methane | 3 | lags_30s | 1.0 | 15.0762 | -1.9416 | -11.4092 | 28.8587 | -3.1613 | -9.8729 |
| ethylene_methane / ethylene | 3 | lags_30s | 1.0 | 2.0808 | -0.1305 | -5.9018 | 3.3723 | -0.1949 | -5.4639 |
| ethylene_methane / methane | 3 | lags_120s | 1.0 | 15.0451 | -1.9727 | -11.5920 | 28.1884 | -3.8316 | -11.9663 |
| ethylene_methane / ethylene | 3 | lags_120s | 0.1 | 2.0251 | -0.1863 | -8.4232 | 3.2894 | -0.2779 | -7.7890 |

## Train, validation and test target distributions

All concentration statistics are in ppm; SD is population SD. These are target summaries, not a full sensor-domain shift analysis.

| Mixture / gas | Fold | Partition | N | Min | Max | Mean | SD | Q05 | Median | Q95 | Unique |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ethylene_CO / CO | 1 | train | 17400 | 0.000 | 533.330 | 148.079 | 163.445 | 0.000 | 0.000 | 360.000 | 17 |
| ethylene_CO / ethylene | 1 | train | 17400 | 0.000 | 20.000 | 5.360 | 5.337 | 0.000 | 6.670 | 16.670 | 9 |
| ethylene_CO / CO | 1 | validation | 3000 | 0.000 | 386.670 | 114.468 | 153.789 | 0.000 | 0.000 | 346.670 | 5 |
| ethylene_CO / ethylene | 1 | validation | 3000 | 0.000 | 18.330 | 4.262 | 6.176 | 0.000 | 0.000 | 18.330 | 7 |
| ethylene_CO / CO | 1 | test | 6000 | 0.000 | 533.330 | 120.102 | 146.366 | 0.000 | 0.000 | 333.330 | 12 |
| ethylene_CO / ethylene | 1 | test | 6000 | 0.000 | 18.330 | 7.292 | 5.509 | 0.000 | 10.000 | 11.670 | 7 |
| ethylene_CO / CO | 2 | train | 23400 | 0.000 | 533.330 | 145.182 | 158.861 | 0.000 | 0.000 | 346.670 | 18 |
| ethylene_CO / ethylene | 2 | train | 23400 | 0.000 | 20.000 | 5.441 | 5.465 | 0.000 | 6.670 | 15.000 | 9 |
| ethylene_CO / CO | 2 | validation | 3000 | 0.000 | 533.330 | 83.915 | 138.422 | 0.000 | 0.000 | 333.330 | 9 |
| ethylene_CO / ethylene | 2 | validation | 3000 | 0.000 | 18.330 | 6.120 | 5.906 | 0.000 | 6.670 | 16.670 | 7 |
| ethylene_CO / CO | 2 | test | 6000 | 0.000 | 533.330 | 119.007 | 183.072 | 0.000 | 0.000 | 520.000 | 12 |
| ethylene_CO / ethylene | 2 | test | 6000 | 0.000 | 18.330 | 3.488 | 5.637 | 0.000 | 0.000 | 15.000 | 8 |
| ethylene_CO / CO | 3 | train | 29400 | 0.000 | 533.330 | 139.258 | 162.674 | 0.000 | 0.000 | 360.000 | 19 |
| ethylene_CO / ethylene | 3 | train | 29400 | 0.000 | 20.000 | 5.307 | 5.547 | 0.000 | 6.670 | 15.000 | 9 |
| ethylene_CO / CO | 3 | validation | 3000 | 0.000 | 520.000 | 64.347 | 148.640 | 0.000 | 0.000 | 466.670 | 5 |
| ethylene_CO / ethylene | 3 | validation | 3000 | 0.000 | 18.330 | 5.088 | 6.829 | 0.000 | 0.000 | 18.330 | 8 |
| ethylene_CO / CO | 3 | test | 6000 | 0.000 | 346.670 | 99.990 | 127.664 | 0.000 | 0.000 | 306.670 | 12 |
| ethylene_CO / ethylene | 3 | test | 6000 | 0.000 | 20.000 | 6.833 | 5.054 | 0.000 | 8.330 | 13.330 | 8 |
| ethylene_methane / methane | 1 | train | 17400 | 0.000 | 296.670 | 68.915 | 80.882 | 0.000 | 66.670 | 240.000 | 29 |
| ethylene_methane / ethylene | 1 | train | 17400 | 0.000 | 18.330 | 3.937 | 5.053 | 0.000 | 0.000 | 13.330 | 8 |
| ethylene_methane / methane | 1 | validation | 3000 | 0.000 | 233.330 | 61.837 | 73.153 | 0.000 | 0.000 | 180.000 | 14 |
| ethylene_methane / ethylene | 1 | validation | 3000 | 0.000 | 20.000 | 4.505 | 5.509 | 0.000 | 3.335 | 18.330 | 6 |
| ethylene_methane / methane | 1 | test | 6000 | 0.000 | 296.670 | 59.842 | 84.158 | 0.000 | 0.000 | 233.330 | 17 |
| ethylene_methane / ethylene | 1 | test | 6000 | 0.000 | 20.000 | 5.444 | 6.088 | 0.000 | 6.670 | 16.670 | 9 |
| ethylene_methane / methane | 2 | train | 23400 | 0.000 | 296.670 | 65.715 | 81.060 | 0.000 | 0.000 | 240.000 | 38 |
| ethylene_methane / ethylene | 2 | train | 23400 | 0.000 | 20.000 | 4.301 | 5.426 | 0.000 | 0.000 | 16.670 | 9 |
| ethylene_methane / methane | 2 | validation | 3000 | 0.000 | 233.330 | 64.323 | 69.452 | 0.000 | 80.000 | 183.330 | 9 |
| ethylene_methane / ethylene | 2 | validation | 3000 | 0.000 | 16.670 | 4.489 | 5.147 | 0.000 | 0.000 | 11.670 | 6 |
| ethylene_methane / methane | 2 | test | 6000 | 0.000 | 280.000 | 56.133 | 73.253 | 0.000 | 0.000 | 220.000 | 13 |
| ethylene_methane / ethylene | 2 | test | 6000 | 0.000 | 18.330 | 2.994 | 5.236 | 0.000 | 0.000 | 15.000 | 9 |
| ethylene_methane / methane | 3 | train | 29400 | 0.000 | 296.670 | 65.371 | 80.565 | 0.000 | 0.000 | 233.330 | 45 |
| ethylene_methane / ethylene | 3 | train | 29400 | 0.000 | 20.000 | 4.173 | 5.329 | 0.000 | 0.000 | 16.670 | 9 |
| ethylene_methane / methane | 3 | validation | 3000 | 0.000 | 243.330 | 46.221 | 68.495 | 0.000 | 0.000 | 220.000 | 6 |
| ethylene_methane / ethylene | 3 | validation | 3000 | 0.000 | 18.330 | 3.167 | 5.103 | 0.000 | 0.000 | 15.000 | 6 |
| ethylene_methane / methane | 3 | test | 6000 | 0.000 | 233.330 | 35.613 | 54.982 | 0.000 | 0.000 | 143.330 | 14 |
| ethylene_methane / ethylene | 3 | test | 6000 | 0.000 | 18.330 | 6.192 | 5.684 | 0.000 | 10.000 | 16.670 | 9 |
