"""The Git LFS guard: a pointer file must stop the run, not quietly shrink the check.

A fresh checkout carries ``data/raw/french``, ``data/raw/french_vintage_2005`` and
``data/raw/goyal_welch`` as Git LFS pointer files. Before the guard, the driver warned,
dropped the regression rows and wrote a check over 544 cells whose score (331.5) reads like a
result (REVIEW_NOTES section 88). These tests use temporary directories only: no real market
data is read.
"""

from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path

import pytest

from project import factors
from project.factors import (
    LFS_POINTER_PREFIX,
    _french_text,
    factor_inputs,
    factor_problem_files,
    is_lfs_pointer,
)

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "replicate_lfs_guard", ROOT / "scripts" / "03_replicate.py")
rep = importlib.util.module_from_spec(_spec)
sys.modules["replicate_lfs_guard"] = rep
_spec.loader.exec_module(rep)

POINTER = (b"version https://git-lfs.github.com/spec/v1\n"
           b"oid sha256:" + b"0" * 64 + b"\nsize 12345\n")


@pytest.fixture
def vintage_restored(monkeypatch):
    """The driver's ``main`` sets the factor vintage globally; put it back after the test.

    Without this the first ``main`` call leaves every later test reading French's 2005
    archives instead of the module default.
    """
    monkeypatch.setattr(factors, "_VINTAGE", factors.vintage())


def _pointer(path: Path) -> Path:
    """A file that says what it would be, and is not it."""
    path.write_bytes(POINTER)
    return path


def _real_zip(path: Path) -> Path:
    """A readable archive: the shape a fetched French file has."""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("F-F_Research_Data_Factors.csv", ",Mkt-RF,SMB,HML,RF\n196307,0,0,0,0\n")
    return path


def test_pointer_constant_is_what_git_writes():
    assert LFS_POINTER_PREFIX == b"version https://git-lfs"
    assert POINTER.startswith(LFS_POINTER_PREFIX)


def test_is_lfs_pointer_reads_the_first_bytes(tmp_path):
    pointer = _pointer(tmp_path / "F-F_Research_Data_Factors_CSV.zip")
    real = _real_zip(tmp_path / "real.zip")
    assert is_lfs_pointer(pointer) is True
    assert is_lfs_pointer(real) is False
    assert is_lfs_pointer(tmp_path / "absent.zip") is False


def test_problem_files_name_pointers_and_missing_files(tmp_path):
    real = _real_zip(tmp_path / "real.zip")
    pointer = _pointer(tmp_path / "F-F_Momentum_Factor_CSV.zip")
    absent = tmp_path / "PredictorData_original_2005.xls"
    assert factor_problem_files([real, pointer, absent]) == [
        (pointer, "git-lfs pointer"), (absent, "missing")]


def test_problem_files_are_empty_when_every_input_is_real(tmp_path):
    real = _real_zip(tmp_path / "F-F_Research_Data_Factors_CSV.zip")
    assert factor_problem_files([real]) == []


def test_factor_inputs_covers_every_loader_the_tables_use():
    """The guard reads its list from the loaders' own constants, not a copy of them."""
    current = factor_inputs("current")
    older = factor_inputs("2005")
    names = {p.name for p in current} | {p.name for p in older}
    assert {"F-F_Research_Data_Factors_CSV.zip", "F-F_Momentum_Factor_CSV.zip"} <= names
    # the 2005 archives, and the reversal file and prior-return deciles the losers-only
    # series reads whatever the vintage
    assert {"F-F_Research_Data_Factors.zip", "F-F_Momentum_Factor.zip"} <= names
    assert {"F-F_ST_Reversal_Factor_CSV.zip", "10_Portfolios_Prior_1_0_CSV.zip"} <= names
    # Goyal and Welch's workbook, Table 4's Ibbotson inputs
    assert "PredictorData_original_2005.xls" in names
    assert len(current) == len(set(current)), "no input is read twice"


def test_a_pointer_is_never_read_as_an_archive(tmp_path):
    """The loader refuses the pointer by name instead of failing inside zipfile."""
    pointer = _pointer(tmp_path / "F-F_Research_Data_Factors_CSV.zip")
    with pytest.raises(FileNotFoundError, match="Git LFS pointer"):
        _french_text(pointer)
    assert "Mkt-RF" in _french_text(_real_zip(tmp_path / "real.zip"))


@pytest.mark.parametrize("steps", [["tables"], ["check"],
                                   ["tables", "table3", "figure1", "check"], ("check",)])
def test_guard_stops_the_factor_steps(tmp_path, monkeypatch, capsys, steps):
    pointer = _pointer(tmp_path / "F-F_Research_Data_Factors_CSV.zip")
    monkeypatch.setattr(rep, "factor_problem_files",
                        lambda paths=None: [(pointer, "git-lfs pointer")])
    with pytest.raises(SystemExit) as caught:
        rep.guard_factor_inputs(list(steps), allow_missing=False)
    assert caught.value.code == 1  # non-zero, so a shell chain sees the failure
    captured = capsys.readouterr()
    assert captured.out == ""  # nothing on stdout that a score-reading script could take
    assert "git-lfs pointer" in captured.err  # says which kind of unreadable
    assert str(pointer) in captured.err  # names the file
    assert "git lfs pull" in captured.err  # names the fix
    assert "--allow-missing-factors" in captured.err  # names the way back


@pytest.mark.parametrize("steps", [["table3"], ["figure1"], ["table3", "figure1"]])
def test_guard_leaves_steps_that_need_no_factor_file_alone(tmp_path, monkeypatch, steps):
    pointer = _pointer(tmp_path / "F-F_Research_Data_Factors_CSV.zip")
    monkeypatch.setattr(rep, "factor_problem_files",
                        lambda paths=None: [(pointer, "git-lfs pointer")])
    rep.guard_factor_inputs(steps, allow_missing=False)  # does not raise


def test_allow_missing_factors_keeps_the_old_fallback(tmp_path, monkeypatch, capsys):
    pointer = _pointer(tmp_path / "F-F_Research_Data_Factors_CSV.zip")
    monkeypatch.setattr(rep, "factor_problem_files",
                        lambda paths=None: [(pointer, "git-lfs pointer")])
    rep.guard_factor_inputs(["check"], allow_missing=True)  # explicit opt-in: no exit
    err = capsys.readouterr().err
    assert "--allow-missing-factors" in err
    assert str(pointer) in err


def test_guard_is_silent_when_the_files_are_readable(monkeypatch, capsys):
    monkeypatch.setattr(rep, "factor_problem_files", lambda paths=None: [])
    rep.guard_factor_inputs(["tables", "check"], allow_missing=False)
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_the_driver_exits_before_writing_anything(tmp_path, monkeypatch, vintage_restored):
    """End to end through the driver's argv: the run stops at the guard."""
    pointer = _pointer(tmp_path / "F-F_Research_Data_Factors_CSV.zip")
    monkeypatch.setattr(rep, "factor_problem_files",
                        lambda paths=None: [(pointer, "git-lfs pointer")])
    monkeypatch.setattr(sys, "argv", [
        "03_replicate.py", "--aggregate-only", "--steps", "check",
        "--out-root", str(tmp_path / "out"), "--cache-root", str(tmp_path / "cache")])
    with pytest.raises(SystemExit) as caught:
        rep.main()
    assert caught.value.code == 1
    assert not (tmp_path / "out").exists()  # nothing written to be mistaken for a result


def test_allow_missing_factors_reaches_the_driver_flag(monkeypatch, tmp_path, vintage_restored):
    """``--allow-missing-factors`` is a real flag, parsed and handed to the guard."""
    seen = {}

    def fake_guard(steps, allow_missing):
        seen["steps"], seen["allow_missing"] = list(steps), allow_missing

    def stop(*args, **kwargs):
        raise SystemExit("arguments parsed; the guard has run")

    monkeypatch.setattr(rep, "guard_factor_inputs", fake_guard)
    monkeypatch.setattr(rep, "parse_month", stop)
    monkeypatch.setattr(sys, "argv", [
        "03_replicate.py", "--allow-missing-factors", "--steps", "table3",
        "--out-root", str(tmp_path / "out")])
    with pytest.raises(SystemExit):
        rep.main()
    assert seen == {"steps": ["table3"], "allow_missing": True}