"""No tracked text file may carry leaked language-model tokens or filler.

The helper agents that run experiments for this replication sometimes leak their
tokenizer's special tokens (the begin-of-sentence token, spelled with fullwidth
vertical bars U+FF5C and word-piece blocks U+2581, or its ASCII spelling that opens
with a less-than sign and a vertical bar) or stretches of CJK, Hangul or Cyrillic
filler into commands and files. One such leak reached a committed review note in
round 6 and was caught only by hand. This test makes the check mechanical: every
git-tracked text file is scanned, and any hit fails with its path and line, so a
leak cannot land through a passing test run.

The patterns are built from code points, so this file is plain ASCII; it is also
excluded from its own scan. The check / tilde / cross marks, dashes, approx, times,
sigma and the other symbols the pages use legitimately are not matched.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

#: Text files worth scanning; binaries (PDF, zip, parquet, png, xlsx) are skipped.
TEXT_SUFFIXES = {
    ".py", ".md", ".json", ".csv", ".sql", ".yaml", ".yml", ".toml", ".txt",
    ".cfg", ".ini", ".sh", ".tex", ".bib",
}
TEXT_NAMES = {"Makefile", ".gitignore", ".gitattributes"}

FULLWIDTH_BAR = chr(0xFF5C)   # in the DeepSeek special tokens, never in this repo's prose
WORD_PIECE = chr(0x2581)      # SentencePiece's word-boundary block
ASCII_OPEN = "<" + "|"        # the ASCII spelling of the same tokens ("<|end", "<|bash|")

TOKEN = re.compile("|".join(re.escape(s) for s in (FULLWIDTH_BAR, WORD_PIECE, ASCII_OPEN)))

#: Scripts no page of this repository is written in: kana, CJK ideographs, Hangul, Cyrillic.
_RANGES = ((0x3040, 0x30FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xAC00, 0xD7AF),
           (0x0400, 0x04FF))
FOREIGN = re.compile("[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in _RANGES) + "]")


def _tracked_text_files() -> list[Path]:
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    done = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=False
    )
    if done.returncode != 0:
        pytest.skip("not a git checkout")
    names = [n for n in done.stdout.decode("utf-8").split("\0") if n]
    return [
        ROOT / n for n in names
        if (Path(n).suffix.lower() in TEXT_SUFFIXES or Path(n).name in TEXT_NAMES)
        and (ROOT / n).resolve() != SELF
    ]


def _hits(pattern: re.Pattern[str]) -> list[str]:
    found = []
    for path in _tracked_text_files():
        if not path.is_file():
            continue
        if path.read_bytes()[:40].startswith(b"version https://git-lfs"):
            continue  # an LFS pointer, not the file
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                found.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:120]}")
    return found


def test_no_leaked_special_tokens():
    hits = _hits(TOKEN)
    assert not hits, "leaked model tokens in tracked files:\n" + "\n".join(hits[:20])


def test_no_foreign_script_filler():
    hits = _hits(FOREIGN)
    assert not hits, "CJK / Hangul / Cyrillic text in tracked files:\n" + "\n".join(hits[:20])


def test_the_patterns_catch_the_leaks_seen_in_this_campaign():
    # Negative controls: the forms that actually leaked must be caught, and the symbols
    # the pages use legitimately must not.
    bos = "<" + FULLWIDTH_BAR + "begin" + WORD_PIECE + "of" + WORD_PIECE + "sentence" + FULLWIDTH_BAR + ">"
    leaked = [bos, ASCII_OPEN + "end", ASCII_OPEN + "bash|",
              chr(0x751F) + chr(0x4EA7), chr(0xC7AC), chr(0x5B63), chr(0x0441)]
    for sample in leaked:
        assert TOKEN.search(sample) or FOREIGN.search(sample), repr(sample)
    # check, tilde, cross, en and em dash, times, approx, sigma, half, arrow, <=, fullwidth tilde
    legitimate = "".join(chr(c) for c in (0x2713, 0x7E, 0x2717, 0x2013, 0x2014, 0xD7, 0x2248,
                                          0x3C3, 0xBD, 0x2192, 0x2264, 0xFF5E))
    assert not TOKEN.search(legitimate)
    assert not FOREIGN.search(legitimate)
