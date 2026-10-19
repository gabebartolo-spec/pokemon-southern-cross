#!/usr/bin/env bash
# Usage: tools/run_tests.sh [python|ruby|content]   (default: all)
# Prints `SUITE <name> CHECKS <n>` per passing suite, `SUITE <name> SKIPPED` when a suite
# cannot run here. Exit 1 on any failure. With PSC_CI=1 a missing runtime is a failure.
# The python and ruby suites also print `SUITE <name> FUNCTIONS <ran> of <defined>`
# (tools/functions_ran.py): a test function that never ran fails the suite, by name.
# Run only the suite you touched locally (seconds each); CI runs all three.
cd "$(dirname "$0")/.." || exit 1
PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
fail=0
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

missing() { # $1 suite, $2 what is missing
  if [ -n "$PSC_CI" ]; then echo "SUITE $1 FAILED ($2 missing in CI)"; fail=1
  else echo "SUITE $1 SKIPPED ($2 not installed)"; fi
}

suite_python() {
  out=$("$PY" -m pytest tests/python -q --junitxml="$tmp/python.xml" 2>&1); rc=$?
  echo "$out"
  n=$(echo "$out" | grep -Eo '[0-9]+ passed' | grep -Eo '[0-9]+' | tail -1)
  if [ -f "$tmp/python.xml" ]; then "$PY" tools/functions_ran.py python "$tmp/python.xml" || rc=1
  else rc=1; fi
  if [ $rc -eq 0 ] && [ -n "$n" ]; then echo "SUITE python CHECKS $n"
  else echo "SUITE python FAILED"; fail=1; fi
}

suite_ruby() {
  if ! command -v ruby >/dev/null 2>&1; then missing ruby ruby; return; fi
  ruby -Itests/ruby -e 'Dir["tests/ruby/test_*.rb"].sort.each{|f| require "./"+f}' -- -v > "$tmp/ruby.txt" 2>&1; rc=$?
  out=$(grep -v -E '^\S+#test_\w+[?!]? = ' "$tmp/ruby.txt")
  echo "$out"
  n=$(echo "$out" | grep -Eo '[0-9]+ runs' | grep -Eo '[0-9]+' | tail -1)
  "$PY" tools/functions_ran.py ruby "$tmp/ruby.txt" || rc=1
  if [ $rc -eq 0 ] && [ -n "$n" ]; then echo "SUITE ruby CHECKS $n"
  else echo "SUITE ruby FAILED"; fail=1; fi
}

suite_content() {
  if [ ! -f tools/validate/content.py ]; then echo "SUITE content SKIPPED (tools/validate/content.py not written yet)"; return; fi
  out=$("$PY" tools/validate/content.py 2>&1); rc=$?
  echo "$out"
  n=$(echo "$out" | grep -Eo 'CHECKS [0-9]+' | grep -Eo '[0-9]+' | tail -1)
  if [ $rc -eq 0 ] && [ -n "$n" ]; then echo "SUITE content CHECKS $n"
  else echo "SUITE content FAILED"; fail=1; fi
}

case "${1:-all}" in
  python) suite_python ;;
  ruby) suite_ruby ;;
  content) suite_content ;;
  all) suite_python; suite_ruby; suite_content ;;
  *) echo "unknown suite: $1 (python|ruby|content)"; exit 2 ;;
esac
exit $fail
