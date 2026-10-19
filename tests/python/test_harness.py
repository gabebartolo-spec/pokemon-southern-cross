"""Tests for the floor checker (tools/check_floors.py)."""
import importlib.util
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


def test_floor_ignores_skipped_suite(tmp_path):
    result = run_floors(tmp_path, "SUITE python CHECKS 4\nSUITE ruby SKIPPED (no ruby)\n",
                        "python 4\nruby 1\n")
    assert result.returncode == 0
    assert "skip ruby" in result.stdout


def test_floored_suite_with_no_result_fails(tmp_path):
    result = run_floors(tmp_path, "SUITE python CHECKS 4\n", "python 4\nruby 1\n")
    assert result.returncode == 1
    assert "no result" in result.stdout


def run_base(tmp_path, floors_text, base_text, log_text="SUITE python CHECKS 99\nSUITE ruby CHECKS 99\n"):
    base = tmp_path / "base.txt"
    base.write_text(base_text, encoding="utf-8")
    log = tmp_path / "run.log"
    floors = tmp_path / "expected_checks.txt"
    log.write_text(log_text, encoding="utf-8")
    floors.write_text(floors_text, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(log), "--floors", str(floors),
                           "--base", str(base)], capture_output=True, text=True)


def test_ratchet_rejects_lowered_floor(tmp_path):
    result = run_base(tmp_path, "python 5\nruby 1\n", "python 6\nruby 1\n")
    assert result.returncode == 1 and "lowered" in result.stdout


def test_ratchet_rejects_missing_suite(tmp_path):
    result = run_base(tmp_path, "python 6\n", "python 6\nruby 1\n")
    assert result.returncode == 1 and "removed" in result.stdout


def test_ratchet_accepts_equal_and_raised(tmp_path):
    assert run_base(tmp_path, "python 6\nruby 2\n", "python 6\nruby 1\n").returncode == 0


def test_doc_caps_regex_is_anchored(tmp_path):
    spec = importlib.util.spec_from_file_location("check_doc_sizes", ROOT / "tools" / "check_doc_sizes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    (tmp_path / "docs").mkdir()
    (tmp_path / "CLAUDE.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "docs" / "STATUS.md").write_text("see Cap: 500 lines elsewhere\n" + "y\n" * 200,
                                                  encoding="utf-8")
    (tmp_path / "docs" / "DECISIONS.md").write_text("Cap: 5 lines\n" + "y\n" * 10, encoding="utf-8")
    mod.ROOT = tmp_path
    mod.DOCS = ["docs/STATUS.md"]
    assert mod.main() == 1  # mid-line "Cap:" ignored -> no cap -> fail
    mod.DOCS = ["docs/DECISIONS.md"]
    assert mod.main() == 1  # line-start cap honoured -> 11 lines > 5
    (tmp_path / "docs" / "DECISIONS.md").write_text("Cap: 50 lines\n", encoding="utf-8")
    assert mod.main() == 0
