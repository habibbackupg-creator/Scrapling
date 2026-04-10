#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./deploy/digitalocean/run_scrapling.sh full-test
#   ./deploy/digitalocean/run_scrapling.sh ui

APP_DIR="${APP_DIR:-$PWD}"
VENV_DIR="${VENV_DIR:-$APP_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MODE="${1:-full-test}"

if [[ ! -d "$APP_DIR" ]]; then
  echo "APP_DIR '$APP_DIR' does not exist. Clone the repo first." >&2
  exit 1
fi

cd "$APP_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

case "$MODE" in
  full-test)
    python -m pip install --upgrade pip
    python -m pip install -e ".[all]"
    python -m pip install -r tests/requirements.txt

    # Browser dependencies for Playwright-based tests/fetchers.
    python -m playwright install chromium
    python -m playwright install-deps chromium
    python -m playwright install chrome

    cd tests
    xvfb-run -a pytest --cov=scrapling --cov-report=xml -k "DynamicFetcher or StealthyFetcher" --verbose
    xvfb-run -a pytest --cov=scrapling --cov-report=xml -m "asyncio" -k "not (DynamicFetcher or StealthyFetcher)" --verbose --cov-append
    xvfb-run -a pytest --cov=scrapling --cov-report=xml -m "not asyncio" -k "not (DynamicFetcher or StealthyFetcher)" -n auto --cov-append
    ;;
  ui)
    python -m pip install --upgrade pip
    # Install only core scrapling - UI doesn't need Playwright, IPython, MCP, etc.
    python -m pip install -e ".[fetchers]"
    exec python -m scrapling.cli ui --host 0.0.0.0 --port "${PORT:-8000}" --no-open-browser
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    echo "Valid modes: full-test | ui" >&2
    exit 1
    ;;
esac
