# Replication pipeline (Gatev, Goetzmann and Rouwenhorst 2006).
#
#   make test       - the test suite, including the paper-conformance
#                     checks (the sample rebuild needs the CRSP daily panel
#                     and is skipped when it is absent)
#   make conformance-full - rebuild all 474 cohorts and require the shipped
#                     full-sample check to be reproduced (a few minutes)
#   make build      - raw WRDS-API parquet -> processed yearly panels
#   make build-data - pull the licensed CRSP source data (once; credentials
#                     stay in ~/.pgpass via scripts/wrds_setup.py)
#   make table9a    - build the screened (top three size deciles) cohort cache
#                     Table 9 Panel A is scored from (about 6 minutes)
#   make table9b    - build the recall cohort cache Table 9 Panel B is scored
#                     from (scripts/claims/table9b_recalls.py, about 2 minutes)
#   make table6     - run the random-pair bootstrap (200 replications, eight
#                     subprocess workers) Table 6 is scored from; the committed
#                     rows use the caption's value-weighted book (book-share)
#   make delist100  - build the delisting-loss cohort cache footnote 4's two
#                     cells are scored from (--long-delisting-loss, about 25 minutes)
#   make benchmark  - fast: regenerate the check from the full cohort cache and
#                     the four side caches, and score it (writes eval/score.json);
#                     PYTHON= and REPL= pick the interpreter and the cache root
#   make outputs   - regenerate report/replication/outputs/ (the committed
#                     tables and figures) and the generated parts of the
#                     replication pages from the check
#   make edition-1999 - score the cohort cache against the 1999 NBER draft's
#                     Tables I-II (second opinion; see report/replication/EDITION_1999.md)
#
# The venv is pinned on PATH so recipes call its interpreter directly.

export PATH := $(CURDIR)/.venv/bin:$(PATH)

# The interpreter and the shared cache root, so the targets can run against a
# checkout whose .venv and caches live elsewhere: make benchmark \
#   PYTHON=/path/.venv/bin/python REPL=/path/data/processed/replication
PYTHON ?= python
REPL ?= data/processed/replication

.PHONY: test conformance-full build build-data benchmark edition-1999 verify-targets table9a table9b table6 delist100 outputs

test:
	python -m pytest tests/ -q

conformance-full:
	REPLICATION_FULL=1 REPLICATION_WORKERS=$${REPLICATION_WORKERS:-4} python -m pytest -q -m conformance_full tests/test_replication_conformance.py

build:
	python scripts/02_build_dataset.py

build-data:
	python scripts/01_get_data.py
	python scripts/02_build_dataset.py

benchmark:
	$(PYTHON) scripts/03_replicate.py --universe vol_common --aggregate-only --workers 1 \
		--cache-root $(REPL)/vol_common \
		--table9a-cache $(REPL)/vol_common_top3 \
		--table9b-cache $(REPL)/vol_common_recalls_r1 \
		--table6-cache $(REPL)/vol_common_t6_book \
		--delist-cache $(REPL)/vol_common_delist100 \
		--steps tables,table3,figure1,check
	$(PYTHON) scripts/replication_score.py

edition-1999:
	python scripts/edition_1999.py

outputs:
	python scripts/03_replicate.py --universe vol_common --aggregate-only --steps tables,table3,figure1
	python scripts/replication_figures.py
	python scripts/docs_sync.py --outputs

table9a:
	python scripts/03_replicate.py --steps tables --size-deciles-top 3 --workers 1 \
		--cache-root data/processed/replication/vol_common_top3 \
		--out-root data/processed/replication/vol_common_top3_out

table9b:
	python scripts/claims/table9b_recalls.py run --workers 8 --reading R1 \
		--cache-root data/processed/replication/vol_common \
		--out-root data/processed/replication/vol_common_recalls_r1

table6:
	python scripts/claims/table6_random_pairs.py --mode run --reps 200 \
		--committed-capital book-share --workers 8 \
		--out-root data/processed/replication/vol_common_t6_book

delist100:
	python scripts/03_replicate.py --steps tables --long-delisting-loss --workers 1 \
		--cache-root data/processed/replication/vol_common_delist100 \
		--out-root data/processed/replication/vol_common_delist100_out

verify-targets:
	python scripts/verify_paper_targets.py
