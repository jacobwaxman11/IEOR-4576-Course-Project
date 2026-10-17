"""One-time WRDS credential setup. Run it yourself, in your own terminal:

    .venv/bin/python scripts/wrds_setup.py

It prompts for your WRDS username and password (the password is not echoed),
stores them in ~/.pgpass with mode 600, outside this repository, and then
connects once. Approve the Duo push on your phone when it arrives.
Never paste credentials into chat, notebooks, configs or commit messages.
"""

import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from project.data import (
    WRDS_DB,
    WRDS_HOST,
    WRDS_PORT,
    _split_pgpass,
    pgpass_path,
    wrds_connection,
)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:")


def main() -> None:
    if not sys.stdin.isatty():
        sys.exit("Run this in an interactive terminal so the password prompt stays private.")
    username = input("WRDS username: ").strip()
    password = getpass.getpass("WRDS password (not shown): ")
    if not username or not password:
        sys.exit("Username and password are both required.")

    path = pgpass_path()
    keep = []
    if path.exists():
        for line in path.read_text().splitlines():
            fields = _split_pgpass(line)
            if not (len(fields) == 5 and fields[0] == WRDS_HOST):
                keep.append(line)
    keep.append(f"{WRDS_HOST}:{WRDS_PORT}:{WRDS_DB}:{_escape(username)}:{_escape(password)}")

    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write("\n".join(keep) + "\n")
    os.chmod(path, 0o600)
    print(f"Saved credentials to {path} (mode 600).")

    print("Connecting to WRDS; approve the Duo push on your phone...")
    db = wrds_connection()
    db.raw_sql("select 1 as ok")
    db.close()
    print(f"Connected as {username}. Setup complete.")


if __name__ == "__main__":
    main()
