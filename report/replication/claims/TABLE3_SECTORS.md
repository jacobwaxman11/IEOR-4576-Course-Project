# Table 3's sector gap: seven label readings, the era split and the pair kinds (round 6C)

Table 3 is the largest single block of the check (139 cells: 58 check, 44 tilde, 37 cross = 80.0 of 139 points). Its failure has a shape: Industrials' closest pairs earn too
much, Industrials' "all" portfolio earns too little, Financials' 101-120 earns too much, and the
medians run high. The paper names the industry label but not the field it is read from, the day it is
read, or the group a stock with no code falls into:

> "Each stock is assigned to one of these four groups, based on the stock's SIC code. The
> minimum-distance criterion is then used to match stocks within each of the groups." (p. 803)

> "The average number of stocks in the industry groups is as follows: 156 Utilities, 61
> Transportation, 371 Financials, and 1729 Industrials." (Table 3's caption, p. 812)

This page reports what the seven readings of that sentence produce, what kind of pair carries the
excess at the top and the shortfall in "all", and the era split of both. Numbers are from the run
directory `/tmp/T/t3` (built by `scripts/experiments/table3_sectors.py build --workers 5`) and its
aggregation `/tmp/T/rep`; the score column is the standard check on the assembled cache.

## 1. The seven readings of the group label

| reading | rule |
|---|---|
| `shipped` | the CRSP dated SIC on the last formation day, then the CIZ header SIC, then the permno's earliest known SIC; 0 is matched as an Industrial; telephone = 4811 only |
| `header` | the CIZ security-header SIC first, the dated SIC as its fallback |
| `formstart` | the dated SIC on the first formation day, not the last |
| `tradestart` | the dated SIC on the first trading day, six months later |
| `mode18` | the dated SIC the stock carries on most of the 18 months' days |
| `nosic_drop` | a stock whose SIC resolves to 0 belongs to no group and is not matched |
| `481x` | 4810-4819 are telephone utilities, so 4810/4812/4813 leave Industrials for Utilities |

## 2. What each reading produces: Table 3 means, fully invested, one-day wait

| sector | portfolio | shipped | header | formstart | tradestart | mode18 | nosic_drop | 481x | paper |
|---|---|---|---|---|---|---|---|---|---|
| Utilities | top5 | 0.00972 | 0.01016 | 0.00897 | 0.00698 | 0.00859 | 0.01027 | 0.00838 | 0.00905 |
|  | top20 | 0.01159 | 0.01198 | 0.01048 | 0.00696 | 0.01078 | 0.01215 | 0.01003 | 0.01084 |
|  | 101-120 | 0.00890 | 0.00785 | 0.00775 | 0.00722 | 0.00894 | 0.00948 | 0.00567 | 0.009256 |
|  | all | 0.01104 | 0.01164 | 0.00998 | 0.00693 | 0.01002 | 0.01095 | 0.01036 | 0.01036 |
| Transportation | top5 | 0.00895 | 0.00759 | 0.00856 | 0.00593 | 0.00570 | 0.01026 | 0.00797 | 0.00497 |
|  | top20 | 0.00567 | 0.00558 | 0.00537 | 0.00498 | 0.00566 | 0.00657 | 0.00573 | 0.00577 |
|  | all | 0.00470 | 0.00423 | 0.00443 | 0.00501 | 0.00638 | 0.00575 | 0.00558 | 0.00440 |
| Financials | top5 | 0.00696 | 0.00733 | 0.00619 | 0.00656 | 0.00597 | 0.00528 | 0.00607 | 0.00678 |
|  | top20 | 0.00808 | 0.00895 | 0.00757 | 0.00762 | 0.00836 | 0.00884 | 0.00884 | 0.00775 |
|  | 101-120 | 0.01048 | 0.01025 | 0.01024 | 0.00489 | 0.00989 | 0.01065 | 0.01026 | 0.00854 |
|  | all | 0.00717 | 0.00738 | 0.00718 | 0.00398 | 0.00791 | 0.00939 | 0.00890 | 0.00726 |
| Industrials | top5 | 0.00626 | 0.00690 | 0.00489 | 0.00450 | 0.00396 | 0.00470 | 0.00460 | 0.00490 |
|  | top20 | 0.00725 | 0.00686 | 0.00667 | 0.00612 | 0.00694 | 0.00658 | 0.00686 | 0.00607 |
|  | 101-120 | 0.00760 | 0.00755 | 0.00732 | 0.00531 | 0.00715 | 0.00701 | 0.00731 | 0.00664 |
|  | all | 0.00585 | 0.00585 | 0.00563 | 0.00200 | 0.00639 | 0.00833 | 0.00638 | 0.00715 |

- `tradestart` is the one label that collapses (Industrials' all falls to 0.00200): reading the code six
  months later reassigns the names that changed code and costs Table 3 35.5 points (44.0 vs 80.0).
- `481x` lifts Utilities' **count** to 154.7 against the paper's 156 but costs Utilities' means
  (all 0.00868 against 0.01036) and scores 401.5 on the whole check.
- `nosic_drop` turns Industrials' all from 0.00585 to 0.00833 - past the paper's 0.00715 - but leaves
  Financials' all 29% high (0.00939) and scores 399.5.
- `formstart` is the only reading that gains on the whole check: **411.5** (Table 3 63 ✓ / 35 ~ / 41 ✗
  = 80.5). It moves one cell net and has no textual support for reading the code on the first formation
  day rather than the last, so it is recorded, not shipped (R6-C's ship rule).

## 3. The era split, by sector (shipped labels)

Mean excess return, fully invested, one-day wait, overlap-averaged per month:

| sector | portfolio | 1963-72 | 1973-82 | 1983-88 | 1989-98 | 1999-2002 | pre-1989 | post-1988 |
|---|---|---|---|---|---|---|---|---|
| Utilities | top5 | 0.01290 | 0.01676 | 0.01001 | 0.00314 | 0.00096 | 0.01373 | 0.00252 |
|  | top20 | 0.01547 | 0.01871 | 0.01161 | 0.00385 | 0.00416 | 0.01583 | 0.00394 |
|  | 101-120 | - | 0.01466 | 0.00671 | 0.00461 | - | 0.01173 | 0.00461 |
|  | all | 0.01592 | 0.01696 | 0.00967 | 0.00502 | 0.00173 | 0.01485 | 0.00408 |
| Transportation | top5 | 0.01147 | 0.00973 | 0.01584 | 0.00699 | -0.00483 | 0.01182 | 0.00361 |
|  | top20 | 0.00802 | 0.00590 | 0.01011 | 0.00538 | -0.00453 | 0.00768 | 0.00255 |
|  | all | 0.00414 | 0.00883 | 0.00708 | 0.00176 | 0.00116 | 0.00667 | 0.00159 |
| Financials | top5 | 0.00838 | 0.00232 | 0.01215 | 0.00675 | 0.00505 | 0.00689 | 0.00627 |
|  | top20 | 0.00545 | 0.00651 | 0.01303 | 0.00927 | 0.00705 | 0.00765 | 0.00864 |
|  | 101-120 | - | 0.01326 | 0.01049 | 0.00787 | 0.00913 | 0.01215 | 0.00823 |
|  | all | 0.00287 | 0.01160 | 0.00992 | 0.00541 | 0.00599 | 0.00795 | 0.00558 |
| Industrials | top5 | 0.00987 | 0.00467 | 0.00686 | 0.00434 | 0.00309 | 0.00712 | 0.00398 |
|  | top20 | 0.00723 | 0.00466 | 0.01086 | 0.00512 | 0.01195 | 0.00707 | 0.00707 |
|  | 101-120 | 0.00888 | 0.00855 | 0.01090 | 0.00513 | 0.00333 | 0.00923 | 0.00461 |
|  | all | 0.00516 | 0.01244 | 0.00893 | 0.00037 | 0.00008 | 0.00891 | 0.00029 |

Two things follow.

- **Industrials' "all" shortfall is late, not early.** Its pre-1989 mean (0.00891) is *above* the paper's
  full-sample 0.00715; the losses are 1989-98 (0.00037) and 1999-2002 (0.00008). So T3's "all-pairs
  earns 17% too little" is a post-1988 phenomenon, the same late-sample defect GAPS.md tracks as Q1/Q9,
  and it cannot be repaired by any label.
- **Transportation's excess at the top is a level gap in both halves** (1.18% pre-1989, 0.36% after), as Q6
  already recorded; and Financials' 101-120 excess (0.01215 pre-1989, 0.00823 after) is worst in the
  early half.

## 4. What kind of pair carries the book

The attribution splits each pair by six facts (2-digit SIC relation, size tercile of the pair's average
market cap, exchange pair, share of frozen-quote days, distance-rank bucket, and the cheaper leg's dollar
price) and allocates each month's compounded book return across the kinds by their daily payoff shares.
Shares of the book (they sum to 100% within a column):

| sector | portfolio | var | era | levels carrying the book |
|---|---|---|---|---|
| Industrials | top20 | size | 1963-72 | high 53%, low 9%, mid 38% |
| Industrials | top20 | frozen | 1963-72 | low-frozen 100% |
| Industrials | top20 | sic | 1963-72 | diff2 50%, same2 10%, same4 9%, unknown 2% |
| Industrials | all | rank | 1963-72 | 121+ 76%, 21-100 18%, 101-120 3%, 6-20 3% |
| Industrials | all | rank | 1973-82 | 121+ 94% |
| Financials | all | rank | 1973-82 | 121+ 86%, 21-100 12% |
| Financials | all | size | 1973-82 | high 47%, low 8%, mid 45% |

The load-bearing facts:
- **The "all" book is the loose pairs by construction**: ranks 121+ carry 73-94% of every sector's "all"
  column in every era. Nothing about the label moves that; the "all" gap is a deep-book gap.
- **At the top the excess is concentrated in high-cap, low-frozen, cross-2-digit pairs**: in
  Industrials' top 20 the high-cap tercile carries 53% and the low-frozen tercile 100% of the book.
  The label cannot move those names either.
- Pair kind does not separate the eras: the same kinds carry the book in 1973-82 as in 1963-72, so the
  era differences in section 3 are population/return differences, not composition.

## 5. Where this leaves Table 3

The seven readings are measured, and only `formstart` gains, by one cell and without support. The
structural facts the readings cannot touch - the "all" column being the loose pairs, the late Industrials
collapse, the Transportation level - are the ones that actually decide the block, and they are the subject
of `GAPS.md` Q1, Q6 and Q9. The attribution therefore names the cause without producing a shippable
reading, which is the outcome T3's ship rule allows for.

## 6. Reproduction

    PY=.venv/bin/python
    $PY scripts/experiments/table3_sectors.py build  --root /tmp/T/t3 --workers 5
    $PY scripts/experiments/table3_sectors.py counts --root /tmp/T/t3 --workers 4
    $PY scripts/experiments/table3_sectors.py report --root /tmp/T/t3 --cache $R/vol_common \
        --out-dir /tmp/T/rep
    sh /tmp/T/score_reading.sh formstart     # assemble one reading and score the whole check

`$R` is `<checkout>/data/processed/replication`.
The seven-reading table is `/tmp/T/rep/table3_readings.csv`, the kind shares
`/tmp/T/rep/table3_kinds_era.csv`, the counts `/tmp/T/ana/counts_by_reading.csv`.
