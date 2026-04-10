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

case "$MODE" in
  full-test)
    if [[ ! -d "$VENV_DIR" ]]; then
      "$PYTHON_BIN" -m venv "$VENV_DIR"
    fi
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"

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
    if [[ "${SCRAPLING_SKIP_INSTALL:-0}" != "1" ]]; then
      if [[ ! -d "$VENV_DIR" ]]; then
        "$PYTHON_BIN" -m venv "$VENV_DIR"
      fi
      # shellcheck disable=SC1091
      source "$VENV_DIR/bin/activate"

      python -m pip install --upgrade pip
      # Install only what web UI needs when running outside App Platform build step.
      python -m pip install -e ".[fetchers]"
    fi
    start_ui() {
      if command -v uv >/dev/null 2>&1; then
        uv run python -c "from scrapling.core.webui import run_web_ui; run_web_ui(host='0.0.0.0', port=int('${PORT:-8000}'), open_browser=False)"
      else
        python -c "from scrapling.core.webui import run_web_ui; run_web_ui(host='0.0.0.0', port=int('${PORT:-8000}'), open_browser=False)"
      fi
    }

    start_worker() {
      if command -v uv >/dev/null 2>&1; then
        uv run scrapling scheduler-worker --ui-base-url "http://127.0.0.1:${PORT:-8000}" --poll-seconds "${SCRAPLING_WORKER_POLL_SECONDS:-20}"
      else
        scrapling scheduler-worker --ui-base-url "http://127.0.0.1:${PORT:-8000}" --poll-seconds "${SCRAPLING_WORKER_POLL_SECONDS:-20}"
      fi
    }

    start_ui &
    UI_PID=$!
    start_worker &
    WORKER_PID=$!

    shutdown() {
      kill "$UI_PID" "$WORKER_PID" 2>/dev/null || true
      wait "$UI_PID" "$WORKER_PID" 2>/dev/null || true
    }

    trap shutdown SIGTERM SIGINT

    wait -n "$UI_PID" "$WORKER_PID"
    EXIT_CODE=$?
    shutdown
    exit "$EXIT_CODE"
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    echo "Valid modes: full-test | ui" >&2
    exit 1
    ;;
esac
