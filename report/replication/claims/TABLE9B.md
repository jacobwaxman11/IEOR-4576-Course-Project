# Table 9B: high-volume short recalls

Sample: full 474-cohort build, 474 reporting months.
Source universe: `vol_common`; exclude constant histories: True.
No-recall control: 474/474 identical trade logs; maximum monthly difference 0; 0 missing months.

The 18-month threshold follows the paper's stated formation-plus-trading window. It uses future trading-period volumes and is a retrospective robustness test, not a deployable forecasting rule. `rearm_form12` estimates its threshold from the 12 formation months only. Missing volume cannot trigger a recall; it is not evidence that a recall would not have occurred. The sample cutoff truncates 5 cohort windows: their threshold uses the available formation-plus-trading dates, not a complete 18 months. Extending those retrospective thresholds past the sample cutoff is a separate unvalidated interpretation.

All variants retain the same source pairs, returns and accounting. Re-entry after a recall is unspecified in the paper: `rearm` waits for the spread to return inside the threshold; `immediate` permits another entry on a continuing divergence; `lock` stops trading that pair for the rest of its cohort.

## Mean returns and the recall effect

All levels are monthly percent; declines are basis points, no-recall minus recall.

| Variant | Capital | Portfolio | Our no recall (%) | Our recall (%) | Paper no recall (%) | Paper recall (%) | Our decline (bp) | Paper decline (bp) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| rearm | mean | top5 | 0.7848 | 0.8565 | 0.7450 | 0.6190 | -7.17 | +12.60 |
| rearm | mean | top20 | 0.9598 | 1.1428 | 0.8950 | 0.8540 | -18.30 | +4.10 |
| rearm | mean | 101-120 | 0.8210 | 0.9654 | 0.7950 | 0.6650 | -14.43 | +13.00 |
| rearm | mean | all | 0.7973 | 1.2864 | 0.7150 | 0.5850 | -48.92 | +13.00 |
| rearm | committed_mean | top5 | 0.4709 | 0.3613 | 0.4630 | 0.3040 | +10.96 | +15.90 |
| rearm | committed_mean | top20 | 0.5672 | 0.4091 | 0.5200 | 0.3470 | +15.82 | +17.30 |
| rearm | committed_mean | 101-120 | 0.5092 | 0.3191 | 0.5030 | 0.2960 | +19.01 | +20.70 |
| rearm | committed_mean | all | 0.4162 | 0.3885 | 0.3960 | 0.2020 | +2.77 | +19.40 |
| immediate | mean | top5 | 0.7848 | 0.8153 | 0.7450 | 0.6190 | -3.05 | +12.60 |
| immediate | mean | top20 | 0.9598 | 1.0571 | 0.8950 | 0.8540 | -9.73 | +4.10 |
| immediate | mean | 101-120 | 0.8210 | 0.9213 | 0.7950 | 0.6650 | -10.02 | +13.00 |
| immediate | mean | all | 0.7973 | 0.9457 | 0.7150 | 0.5850 | -14.84 | +13.00 |
| immediate | committed_mean | top5 | 0.4709 | 0.4452 | 0.4630 | 0.3040 | +2.57 | +15.90 |
| immediate | committed_mean | top20 | 0.5672 | 0.5478 | 0.5200 | 0.3470 | +1.94 | +17.30 |
| immediate | committed_mean | 101-120 | 0.5092 | 0.5098 | 0.5030 | 0.2960 | -0.05 | +20.70 |
| immediate | committed_mean | all | 0.4162 | 0.4468 | 0.3960 | 0.2020 | -3.06 | +19.40 |
| lock | mean | top5 | 0.7848 | 0.5723 | 0.7450 | 0.6190 | +21.25 | +12.60 |
| lock | mean | top20 | 0.9598 | 1.0494 | 0.8950 | 0.8540 | -8.96 | +4.10 |
| lock | mean | 101-120 | 0.8210 | 0.8224 | 0.7950 | 0.6650 | -0.14 | +13.00 |
| lock | mean | all | 0.7973 | 1.1789 | 0.7150 | 0.5850 | -38.17 | +13.00 |
| lock | committed_mean | top5 | 0.4709 | 0.1880 | 0.4630 | 0.3040 | +28.29 | +15.90 |
| lock | committed_mean | top20 | 0.5672 | 0.2231 | 0.5200 | 0.3470 | +34.41 | +17.30 |
| lock | committed_mean | 101-120 | 0.5092 | 0.1885 | 0.5030 | 0.2960 | +32.08 | +20.70 |
| lock | committed_mean | all | 0.4162 | 0.2528 | 0.3960 | 0.2020 | +16.34 | +19.40 |
| rearm_form12 | mean | top5 | 0.7848 | 0.8480 | 0.7450 | 0.6190 | -6.32 | +12.60 |
| rearm_form12 | mean | top20 | 0.9598 | 1.1079 | 0.8950 | 0.8540 | -14.81 | +4.10 |
| rearm_form12 | mean | 101-120 | 0.8210 | 1.0572 | 0.7950 | 0.6650 | -23.62 | +13.00 |
| rearm_form12 | mean | all | 0.7973 | 1.4289 | 0.7150 | 0.5850 | -63.16 | +13.00 |
| rearm_form12 | committed_mean | top5 | 0.4709 | 0.3458 | 0.4630 | 0.3040 | +12.51 | +15.90 |
| rearm_form12 | committed_mean | top20 | 0.5672 | 0.3936 | 0.5200 | 0.3470 | +17.36 | +17.30 |
| rearm_form12 | committed_mean | 101-120 | 0.5092 | 0.3362 | 0.5030 | 0.2960 | +17.30 | +20.70 |
| rearm_form12 | committed_mean | all | 0.4162 | 0.4228 | 0.3960 | 0.2020 | -0.66 | +19.40 |

## All 44 Table 9B targets

Within-10% and within-25% counts describe numerical proximity only; they are not proof of replication. Every entry is our value / original paper value.

### rearm

| Statistic | top5 | top20 | 101-120 | all |
|---|---:|---:|---:|---:|
| mean (%) | 0.85654 / 0.61900 | 1.14282 / 0.85400 | 0.96535 / 0.66500 | 1.28644 / 0.58500 |
| nw_se (%) | 0.13535 / 0.11500 | 0.12152 / 0.09400 | 0.10765 / 0.08500 | 0.10296 / 0.09800 |
| t_stat | 6.32830 / 5.39000 | 9.40426 / 9.07000 | 8.96769 / 7.81000 | 12.49442 / 5.95000 |
| median (%) | 0.82824 / 0.59200 | 1.02281 / 0.70300 | 0.95405 / 0.53100 | 1.00846 / 0.31200 |
| std (%) | 2.27083 / 2.21000 | 1.73961 / 1.48800 | 1.88994 / 1.50500 | 1.84091 / 1.55500 |
| skew | 0.35692 / 0.15000 | 0.54808 / 0.48000 | 0.20998 / 1.03000 | 1.99404 / 2.82000 |
| kurtosis | 6.54853 / 5.39000 | 5.50784 / 6.00000 | 3.95189 / 7.39000 | 13.54682 / 18.98000 |
| min (%) | -9.35654 / -9.61100 | -7.04471 / -6.59400 | -6.29972 / -4.40800 | -6.28117 / -3.46500 |
| max (%) | 12.67736 / 10.50400 | 9.13113 / 7.25500 | 8.47868 / 10.08400 | 14.09549 / 14.17300 |
| share_negative | 0.34599 / 0.39000 | 0.25105 / 0.26000 | 0.30802 / 0.34000 | 0.16456 / 0.37000 |
| committed_mean (%) | 0.36128 / 0.30400 | 0.40906 / 0.34700 | 0.31911 / 0.29600 | 0.38850 / 0.20200 |

Within 10%: 10/44; within 25% (including within 10%): 22/44. Positive means: 4/4; Newey-West t > 2: 4/4.

### immediate

| Statistic | top5 | top20 | 101-120 | all |
|---|---:|---:|---:|---:|
| mean (%) | 0.81532 / 0.61900 | 1.05714 / 0.85400 | 0.92127 / 0.66500 | 0.94567 / 0.58500 |
| nw_se (%) | 0.11887 / 0.11500 | 0.10732 / 0.09400 | 0.08853 / 0.08500 | 0.10447 / 0.09800 |
| t_stat | 6.85911 / 5.39000 | 9.84998 / 9.07000 | 10.40622 / 7.81000 | 9.05227 / 5.95000 |
| median (%) | 0.72994 / 0.59200 | 0.97203 / 0.70300 | 0.80844 / 0.53100 | 0.62485 / 0.31200 |
| std (%) | 2.15104 / 2.21000 | 1.59606 / 1.48800 | 1.65803 / 1.50500 | 2.02619 / 1.55500 |
| skew | -0.40746 / 0.15000 | 0.24822 / 0.48000 | 0.28097 / 1.03000 | 1.55070 / 2.82000 |
| kurtosis | 8.46729 / 5.39000 | 7.06766 / 6.00000 | 4.25382 / 7.39000 | 14.88594 / 18.98000 |
| min (%) | -14.23556 / -9.61100 | -8.61183 / -6.59400 | -4.54705 / -4.40800 | -11.18910 / -3.46500 |
| max (%) | 8.68901 / 10.50400 | 7.61666 / 7.25500 | 7.62435 / 10.08400 | 15.33825 / 14.17300 |
| share_negative | 0.33544 / 0.39000 | 0.24473 / 0.26000 | 0.27848 / 0.34000 | 0.28903 / 0.37000 |
| committed_mean (%) | 0.44518 / 0.30400 | 0.54777 / 0.34700 | 0.50978 / 0.29600 | 0.44677 / 0.20200 |

Within 10%: 10/44; within 25% (including within 10%): 21/44. Positive means: 4/4; Newey-West t > 2: 4/4.

### lock

| Statistic | top5 | top20 | 101-120 | all |
|---|---:|---:|---:|---:|
| mean (%) | 0.57229 / 0.61900 | 1.04942 / 0.85400 | 0.82239 / 0.66500 | 1.17894 / 0.58500 |
| nw_se (%) | 0.10942 / 0.11500 | 0.13012 / 0.09400 | 0.14618 / 0.08500 | 0.13272 / 0.09800 |
| t_stat | 5.23035 / 5.39000 | 8.06476 / 9.07000 | 5.62584 / 7.81000 | 8.88276 / 5.95000 |
| median (%) | 0.62644 / 0.59200 | 0.98721 / 0.70300 | 0.85815 / 0.53100 | 0.94095 / 0.31200 |
| std (%) | 1.95946 / 2.21000 | 2.07819 / 1.48800 | 2.69424 / 1.50500 | 2.30735 / 1.55500 |
| skew | -1.03828 / 0.15000 | -0.68617 / 0.48000 | -0.92467 / 1.03000 | 1.44147 / 2.82000 |
| kurtosis | 10.66006 / 5.39000 | 10.81480 / 6.00000 | 10.93115 / 7.39000 | 11.63174 / 18.98000 |
| min (%) | -12.38219 / -9.61100 | -14.92090 / -6.59400 | -17.74741 / -4.40800 | -10.25851 / -3.46500 |
| max (%) | 8.08658 / 10.50400 | 8.30294 / 7.25500 | 12.11880 / 10.08400 | 16.39695 / 14.17300 |
| share_negative | 0.29747 / 0.39000 | 0.26160 / 0.26000 | 0.35232 / 0.34000 | 0.24684 / 0.37000 |
| committed_mean (%) | 0.18796 / 0.30400 | 0.22312 / 0.34700 | 0.18846 / 0.29600 | 0.25276 / 0.20200 |

Within 10%: 6/44; within 25% (including within 10%): 15/44. Positive means: 4/4; Newey-West t > 2: 4/4.

### rearm_form12

| Statistic | top5 | top20 | 101-120 | all |
|---|---:|---:|---:|---:|
| mean (%) | 0.84800 / 0.61900 | 1.10790 / 0.85400 | 1.05719 / 0.66500 | 1.42891 / 0.58500 |
| nw_se (%) | 0.13320 / 0.11500 | 0.12483 / 0.09400 | 0.10713 / 0.08500 | 0.10038 / 0.09800 |
| t_stat | 6.36619 / 5.39000 | 8.87500 / 9.07000 | 9.86818 / 7.81000 | 14.23518 / 5.95000 |
| median (%) | 0.79619 / 0.59200 | 1.00721 / 0.70300 | 1.04467 / 0.53100 | 1.11666 / 0.31200 |
| std (%) | 2.25267 / 2.21000 | 1.77245 / 1.48800 | 1.83562 / 1.50500 | 1.82669 / 1.55500 |
| skew | 0.30739 / 0.15000 | 0.54633 / 0.48000 | 0.03325 / 1.03000 | 2.20676 / 2.82000 |
| kurtosis | 5.54270 / 5.39000 | 5.11264 / 6.00000 | 3.83414 / 7.39000 | 13.80981 / 18.98000 |
| min (%) | -8.41783 / -9.61100 | -5.91634 / -6.59400 | -6.61421 / -4.40800 | -3.66923 / -3.46500 |
| max (%) | 10.96185 / 10.50400 | 9.40337 / 7.25500 | 7.54668 / 10.08400 | 14.59640 / 14.17300 |
| share_negative | 0.34177 / 0.39000 | 0.25949 / 0.26000 | 0.27426 / 0.34000 | 0.12236 / 0.37000 |
| committed_mean (%) | 0.34578 / 0.30400 | 0.39361 / 0.34700 | 0.33624 / 0.29600 | 0.42282 / 0.20200 |

Within 10%: 8/44; within 25% (including within 10%): 23/44. Positive means: 4/4; Newey-West t > 2: 4/4.

## Activity and limitations

| Variant | Trades | Recall closes | Recall share | Short trades without volume |
|---|---:|---:|---:|---:|
| rearm | 2187775 | 1498017 | 68.47% | 230849 |
| immediate | 5065368 | 3988810 | 78.75% | 231074 |
| lock | 1101353 | 705942 | 64.10% | 215459 |
| rearm_form12 | 2216396 | 1527570 | 68.92% | 230860 |

The experiment uses trading volume as a recall proxy, not observed loan recalls or borrow fees. Historical volume coverage and the source universe remain limitations. No causal explanation for numerical differences is inferred from the size of the recall effect alone.

## Reproduce

```sh
python scripts/claims/table9b_recalls.py run --cache-root /Users/jaredcohen/code/DDMF-pair-trading/IEOR-4576-Course-Project/data/processed/replication/reconciliation/baseline --out-root /Users/jaredcohen/code/DDMF-pair-trading/IEOR-4576-Course-Project/results/replication/reconciliation/baseline_table9b --raw-dir data/interim/crsp/volume --report-dir /Users/jaredcohen/code/DDMF-pair-trading/IEOR-4576-Course-Project/results/replication/reconciliation/baseline_table9b/report --start 1963-07 --end 2002-12 --workers 2 --specification baseline --source-universe vol_common --source-exclude-constant
```

Cohort build runtime: 905.3 seconds. Targets: `scripts/claims/table9b_paper.json`; Table 9B cells also verified against the attached February 2006 working paper, p. 42.
