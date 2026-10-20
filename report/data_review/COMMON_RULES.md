# Data review: rules every worker follows

These rules apply to both data-review contracts (`AGENT_A_CONTRACT.md`, `AGENT_B_CONTRACT.md`).

## Working directory and git

- **Working directory:** `/home/congge2026/orca/workspaces/IEOR4576_Final_Paper/queenfish`, on branch `hw3150cu/queenfish`.
- **Git:** do not commit, push, rebase or stash. The coordinator commits.
- **Python:** use `.venv/bin/python`. It already has `wrds`, `pandas` and `pyarrow`, and `project` is installed in editable mode.
- **No download code exists yet.** The repo has no download code: `scripts/` and `src/project/` were empty. All existing CRSP files were pulled by hand through the WRDS website. Only their query definitions are in `data/metadata/queries/`, and the data files in `data/raw/` are Git LFS placeholders, not data.

## Credentials (hard rules)

- Connect to WRDS only with:

  ```python
  from project.data import wrds_connection
  db = wrds_connection()
  ```

- **Never** do any of the following:
  - read, `cat`, `grep` or copy `~/.pgpass`;
  - print environment variables or `db.engine.url`;
  - call `wrds.Connection()` directly. It falls back to interactive password prompts and would hang.
- If `wrds_connection()` raises, stop. Report the error message with `ask`. Do not try to work around it.

## Duo two-factor protocol

Every new WRDS connection can send a Duo push to Hao's phone, so connections are rationed.

1. Put all of your SQL in **one script per phase**. Each phase opens one connection, runs every query, saves the outputs and closes the connection. Separate `python -c` calls each open a new connection.
2. **Before every script run that connects**, ask the coordinator and wait for the answer `go`:

   ```sh
   orca orchestration ask --question "DUO: <A|B> phase <n> about to connect to WRDS" --options go,wait --timeout-ms 1800000 --json
   ```

   - If the answer is `wait`, ask again later.
   - If `ask` times out, resume it with `--resume <message_id>`.
3. **At most 3 connecting runs per worker.** The recommended split is: (1) discover the schema with `list_tables` and `describe_table`; (2) run the checks; (3) one rerun to fix mistakes.
4. Set a per-statement guard by connecting with `db = wrds_connection(statement_timeout="15min")`. Do **not** send `SET ...` through `db.raw_sql`, which only accepts statements that return rows. If a query times out, narrow it (by year) in the next phase.
5. Wrap each query in try/except so that one failing query is recorded (in the results and the findings) without aborting the whole phase, and the remaining queries still run on the same connection.
6. Aggregate on the server (`GROUP BY`, `COUNT`). Never pull row-level panels, and especially not the daily stock table of about 100M rows.

## Data handling

- Write only the files your contract lists, under `report/data_review/`.
- Results may hold only **aggregates**: counts, coverage, summary statistics.
- Any row-level sample that is genuinely needed goes to the git-ignored `data/raw/wrds_api/`, through `project.data.query_to_parquet`. Never commit it, and never put it in a findings file.

## Evidence standard

- Every claim in the findings file names its evidence: a query ID (`A3`, `B5`, ...) that appears in your SQL file, or a repo file and line.
- Mark each check **PASS**, **FAIL**, **WARN** or **UNVERIFIED**. When something could not be checked, say so. Never guess a number.
- Severity: **BLOCKER** stops the replication; **MAJOR** biases results; **MINOR** is cosmetic or documentation only.

## Done signal

Send this once, from your own terminal, when the findings file is complete:

```sh
orca orchestration send --type worker_done --subject "<A|B> data review done" \
  --body "<3 sentences: what passed, the worst problem found, what remains unverified>" \
  --task-id <task_id> --dispatch-id <dispatch_id> --outcome succeeded \
  --files-modified "<csv of files you wrote>" --json
```

Use `--outcome failed` if you could not finish, for example because WRDS was unreachable.
