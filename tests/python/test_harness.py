"""Tests for the function counter (tools/functions_ran.py) and the doc caps."""
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "functions_ran.py"

PY_TESTS = '''
import pytest

def test_a():
    pass

@pytest.mark.parametrize("n", [1, 2])
def test_b(n):
    pass

class TestThing:
    def test_c(self):
        pass

def helper():
    pass
'''


def junit(cases):
    rows = "".join(f'<testcase classname="{c}" name="{n}"/>' for c, n in cases)
    return f'<?xml version="1.0"?><testsuites><testsuite>{rows}</testsuite></testsuites>'


def run_counter(tmp_path, suite, filename, source, result_text):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / filename).write_text(source, encoding="utf-8")
    result = tmp_path / "result.txt"
    result.write_text(result_text, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), suite, str(result), "--tests", str(tests)],
                          capture_output=True, text=True)


def test_counter_accepts_every_function_ran(tmp_path):
    cases = [("tests.test_x", "test_a"), ("tests.test_x", "test_b[1]"), ("tests.test_x", "test_b[2]"),
             ("tests.test_x.TestThing", "test_c")]
    result = run_counter(tmp_path, "python", "test_x.py", PY_TESTS, junit(cases))
    assert result.returncode == 0, result.stdout
    assert "SUITE python FUNCTIONS 3 of 3" in result.stdout


def test_counter_names_a_function_that_never_ran(tmp_path):
    cases = [("tests.test_x", "test_a"), ("tests.test_x", "test_b[1]")]
    result = run_counter(tmp_path, "python", "test_x.py", PY_TESTS, junit(cases))
    assert result.returncode == 1
    assert "FUNCTIONS 2 of 3" in result.stdout
    assert "never ran: test_x::TestThing.test_c" in result.stdout


def test_counter_fails_a_shadowed_function(tmp_path):
    source = "def test_a():\n    pass\n\ndef test_a():\n    pass\n"
    result = run_counter(tmp_path, "python", "test_x.py", source, junit([("tests.test_x", "test_a")]))
    assert result.returncode == 1 and "never ran: test_x::test_a" in result.stdout


def test_counter_fails_a_suite_with_no_tests(tmp_path):
    result = run_counter(tmp_path, "python", "test_x.py", "def helper():\n    pass\n", junit([]))
    assert result.returncode == 1 and "no test functions" in result.stdout


RB_TESTS = '''
class TestRules < Minitest::Test
  def test_one
  end

  def test_two?
  end
end
'''


def test_counter_reads_minitest_verbose_output(tmp_path):
    out = "TestRules#test_one = 0.00 s = .\nTestRules#test_two? = 0.00 s = .\n2 runs, 2 assertions\n"
    result = run_counter(tmp_path, "ruby", "test_rules.rb", RB_TESTS, out)
    assert result.returncode == 0, result.stdout
    assert "SUITE ruby FUNCTIONS 2 of 2" in result.stdout


def test_counter_names_a_ruby_test_that_never_ran(tmp_path):
    out = "TestRules#test_one = 0.00 s = .\n1 runs, 1 assertions\n"
    result = run_counter(tmp_path, "ruby", "test_rules.rb", RB_TESTS, out)
    assert result.returncode == 1 and "never ran: test_rules::test_two?" in result.stdout


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
