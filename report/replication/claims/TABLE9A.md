# Table 9A — same-baseline size robustness

GGR (2006), section 3.9 / Table 9A, p. 824. Both samples contain 474 cohorts; only the top-three-size-decile screen changes. Returns are monthly. The documented skew/kurtosis label correction is retained.

cohort 1963-07: formation 1962-07-01..1963-06-28
  eligible stocks            624
  kept in deciles 1-3      397 (63.6% of eligible)
  cached pairs               335
  distinct pair legs         397
  legs outside deciles 1-3 0
| Row | Top 5 | Top 20 | 20 after top 100 | All |
|---|---|---|---|---|
| Mean monthly return (fully invested) | 0.996% (0.835%) ~ | 1.029% (0.914%) ~ | 0.760% (0.728%) ✓ | 0.754% (0.690%) ✓ |
| Standard error (Newey-West) | 0.132% (0.112%) ~ | 0.114% (0.096%) ~ | 0.079% (0.075%) ✓ | 0.069% (0.064%) ✓ |
| t-Statistic | 7.58 (7.47) ✓ | 9.05 (9.48) ✓ | 9.57 (9.66) ✓ | 10.87 (10.85) ✓ |
| Median | 0.735% (0.800%) ✓ | 0.926% (0.793%) ~ | 0.647% (0.614%) ✓ | 0.653% (0.508%) ✗ |
| Standard deviation | 2.142% (1.904%) ~ | 1.648% (1.464%) ~ | 1.631% (1.579%) ✓ | 1.524% (1.294%) ~ |
| Kurtosis | 7.78 (7.01) ~ | 8.31 (8.20) ✓ | 5.05 (6.46) ~ | 9.49 (11.67) ~ |
| Skewness | 0.04 (0.02) ✗ | 0.41 (0.98) ✗ | 0.48 (0.80) ✗ | 0.96 (1.77) ✗ |
| Minimum | -12.973% (-10.894%) ~ | -8.657% (-5.646%) ✗ | -4.557% (-3.803%) ~ | -7.484% (-2.680%) ✗ |
| Maximum | 9.737% (10.144%) ✓ | 10.224% (10.003%) ✓ | 8.342% (10.642%) ~ | 8.901% (10.478%) ~ |
| Observations with excess return < 0 | 31% (32%) ✓ | 23% (26%) ~ | 32% (33%) ✓ | 29% (27%) ✓ |
| Mean excess return on committed capital | 0.598% (0.493%) ~ | 0.588% (0.514%) ~ | 0.453% (0.462%) ✓ | 0.436% (0.401%) ✓ |

| Portfolio | Our mean change | Paper mean change | Our t | Paper t |
|---|---|---|---|---|
| Top 5 | +21.2 bp | +9.0 bp | 7.58 (6.93) | 7.47 (6.26) |
| Top 20 | +7.0 bp | +1.9 bp | 9.05 (9.73) | 9.48 (9.29) |
| 20 after top 100 | -6.1 bp | -6.7 bp | 9.57 (10.27) | 9.66 (9.40) |
| All | -4.3 bp | -2.5 bp | 10.87 (8.13) | 10.85 (7.92) |

      base_stocks   base_pairs  top3_stocks  top3_pairs
mean  2293.080169  2008.831224   700.924051  587.312236
min    616.000000   524.000000   397.000000  335.000000
max   4016.000000  3542.000000  1165.000000  988.000000
