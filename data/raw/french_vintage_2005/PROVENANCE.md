# French's factors, as the paper had them (2005 data library)

GGR (2006) regress on "the three factors of Fama and French (1996), augmented by two
additional factors" downloaded from Kenneth French's data library before the paper appeared
(RFS Advance Access, February 2006). French has revised the monthly factors since; these two
archives are the Internet Archive's captures from 2005 and replace nothing: the current files
stay under `data/raw/french`, and `--factor-vintage` chooses between the two
(REVIEW_NOTES section 72).

Neither archive is Git LFS: they are committed whole, as downloaded, so a checkout can read
them without `git lfs pull`.

## `F-F_Research_Data_Factors.zip`

- URL: <https://web.archive.org/web/20050930202651id_/http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors.zip>
- Wayback timestamp: `20050930202651`
- Member: `F-F_Research_Data_Factors.txt`, dated 2005-09-22
- First line: `This file was created by CMPT_ME_BEME_RETS using the 200508 CRSP database.`
- Monthly block: `Mkt-RF`, `SMB`, `HML`, `RF`, 192607-200508
- sha256: `1b6d305a2f630c316eae764c3bb858c5f4746aa7888f462135d45d6f1ae88c2f`

## `F-F_Momentum_Factor.zip`

- URL: <https://web.archive.org/web/20051029233931id_/http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor.zip>
- Wayback timestamp: `20051029233931`
- Member: `F-F_Momentum_Factor.txt`, dated 2005-10-21
- First line: `This file was created by CMPT_ME_PRIOR_RETS using the 200509 CRSP database.`
- Monthly block: `UMD`, 192701-200509
- sha256: `d9688cd1c11d789fcbeb35df65ca285e1cd289ea9e3a71fad541be5413522888`

## Why these and not today's files

Table 8 prints each factor's standard deviation per panel (p. 822). The 2005 archives
reproduce that column; today's files do not, because French revised HML in 2015
(REVIEW_NOTES section 72; the test `tests/test_factors.py::test_2005_loader_reproduces_the_paper_factor_sd`).

The prior-month deciles that give the losers-only reversal series are not part of this
vintage: the earliest archived `10_Portfolios_Prior_1_0` file is from 2007 and matches today's
(monthly returns correlate 0.9995, losers-only SD 0.0687 against 0.0685), so the loader reads
the reversal inputs from `data/raw/french` and subtracts this vintage's `RF`.