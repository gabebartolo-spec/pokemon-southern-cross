"""Tests for the floor checker (tools/check_floors.py)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "check_floors.py"


def run_floors(tmp_path, log_text, floors_text):
    log = tmp_path / "run.log"
    floors = tmp_path / "expected_checks.txt"
    log.write_text(log_text, encoding="utf-8")
    floors.write_text(floors_text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(log), "--floors", str(floors)],
        capture_output=True, text=True,
    )


def test_floor_rejects_lower_count(tmp_path):
    result = run_floors(tmp_path, "SUITE python CHECKS 3\n", "python 4\n")
    assert result.returncode == 1


def test_floor_accepts_equal_count(tmp_path):
    result = run_floors(tmp_path, "SUITE python CHECKS 4\n", "python 4\n")
    assert result.returncode == 0
