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
#   make benchmark  - fast: regenerate Tables 1-3 from the full cohort cache
#                     and score them (writes eval/score.json)
#   make edition-1999 - score the cohort cache against the 1999 NBER draft's
#                     Tables I-II (second opinion; see report/replication/EDITION_1999.md)
#
# The venv is pinned on PATH so recipes call its interpreter directly.

export PATH := $(CURDIR)/.venv/bin:$(PATH)

.PHONY: test conformance-full build build-data benchmark edition-1999 verify-targets

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
	python scripts/03_replicate.py --universe vol_common --aggregate-only --steps tables,table3,check
	python scripts/replication_score.py

edition-1999:
	python scripts/edition_1999.py

verify-targets:
	python scripts/verify_paper_targets.py
