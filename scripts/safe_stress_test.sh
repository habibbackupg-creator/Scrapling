#!/usr/bin/env bash
set -euo pipefail

# Safe stress test for Scrapling Web UI.
# Default target is the deployed DigitalOcean app. Override with BASE_URL env or first arg.
BASE_URL="${1:-${BASE_URL:-https://scrapling-ui-qx83k.ondigitalocean.app}}"
EXTRACT_URL="${BASE_URL%/}/extract"
TARGET_PAGE="${TARGET_PAGE:-https://example.com}"
CSS_SELECTOR="${CSS_SELECTOR:-h1}"
FMT="${FMT:-txt}"
SEQUENTIAL_RUNS="${SEQUENTIAL_RUNS:-5}"
CONCURRENT_RUNS="${CONCURRENT_RUNS:-10}"
CONCURRENCY="${CONCURRENCY:-3}"

# Expected metrics (tune for your infra):
# - sequential_success_rate >= 95%
# - sequential_p95_seconds <= 12
# - concurrent_success_rate >= 90%
# - concurrent_p95_seconds <= 18
EXPECTED_SEQ_SUCCESS="${EXPECTED_SEQ_SUCCESS:-95}"
EXPECTED_SEQ_P95="${EXPECTED_SEQ_P95:-12}"
EXPECTED_CONC_SUCCESS="${EXPECTED_CONC_SUCCESS:-90}"
EXPECTED_CONC_P95="${EXPECTED_CONC_P95:-18}"

PAYLOAD="url=$(printf '%s' "$TARGET_PAGE" | sed 's/:/%3A/g; s/\//%2F/g')&fmt=${FMT}&css_selector=${CSS_SELECTOR}"
TMPDIR_PATH="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_PATH"' EXIT

run_once() {
    curl -sS -o /dev/null \
      -X POST "$EXTRACT_URL" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data "$PAYLOAD" \
      -w "%{http_code} %{time_total}\n"
}

calc_metrics() {
    local file="$1"
    local count
    count="$(wc -l < "$file" | tr -d ' ')"

    awk -v n="$count" '
      {
        code[NR]=$1
        t[NR]=$2
        if ($1 >= 200 && $1 < 400) ok++
      }
      END {
        if (n == 0) {
          print "0 0 0 0"
          exit
        }
        for (i=1; i<=n; i++) {
          for (j=i+1; j<=n; j++) {
            if (t[i] > t[j]) {
              tmp=t[i]; t[i]=t[j]; t[j]=tmp
            }
          }
        }
        p50_index = int((n + 1) * 0.50)
        p95_index = int((n + 1) * 0.95)
        if (p50_index < 1) p50_index = 1
        if (p95_index < 1) p95_index = 1
        if (p50_index > n) p50_index = n
        if (p95_index > n) p95_index = n

        success_rate = (ok * 100.0) / n
        printf "%.2f %.3f %.3f %d\n", success_rate, t[p50_index], t[p95_index], n
      }
    ' "$file"
}

print_report() {
    local label="$1"
    local success="$2"
    local p50="$3"
    local p95="$4"
    local total="$5"
    echo "$label"
    echo "  total_requests=$total"
    echo "  success_rate=${success}%"
    echo "  p50_seconds=${p50}"
    echo "  p95_seconds=${p95}"
}

assert_thresholds() {
    local label="$1"
    local success="$2"
    local p95="$3"
    local min_success="$4"
    local max_p95="$5"

    local failed=0
    awk -v a="$success" -v b="$min_success" 'BEGIN { exit !(a >= b) }' || failed=1
    awk -v a="$p95" -v b="$max_p95" 'BEGIN { exit !(a <= b) }' || failed=1

    if [[ "$failed" -eq 0 ]]; then
      echo "  status=PASS (expected success>=$min_success%, p95<=$max_p95 s)"
    else
      echo "  status=WARN (expected success>=$min_success%, p95<=$max_p95 s)"
    fi
}

echo "Running safe stress test"
echo "  base_url=$BASE_URL"
echo "  extract_url=$EXTRACT_URL"
echo "  target_page=$TARGET_PAGE"

echo "\n[1/2] Sequential test ($SEQUENTIAL_RUNS requests)"
SEQ_FILE="$TMPDIR_PATH/sequential.txt"
for _ in $(seq 1 "$SEQUENTIAL_RUNS"); do
  run_once >> "$SEQ_FILE"
done
read -r seq_success seq_p50 seq_p95 seq_total < <(calc_metrics "$SEQ_FILE")
print_report "sequential" "$seq_success" "$seq_p50" "$seq_p95" "$seq_total"
assert_thresholds "sequential" "$seq_success" "$seq_p95" "$EXPECTED_SEQ_SUCCESS" "$EXPECTED_SEQ_P95"

echo "\n[2/2] Concurrent test ($CONCURRENT_RUNS requests, concurrency=$CONCURRENCY)"
CONC_FILE="$TMPDIR_PATH/concurrent.txt"
seq "$CONCURRENT_RUNS" | xargs -I{} -P "$CONCURRENCY" bash -c 'curl -sS -o /dev/null -X POST "'$EXTRACT_URL'" -H "Content-Type: application/x-www-form-urlencoded" --data "'$PAYLOAD'" -w "%{http_code} %{time_total}\n"' >> "$CONC_FILE"
read -r conc_success conc_p50 conc_p95 conc_total < <(calc_metrics "$CONC_FILE")
print_report "concurrent" "$conc_success" "$conc_p50" "$conc_p95" "$conc_total"
assert_thresholds "concurrent" "$conc_success" "$conc_p95" "$EXPECTED_CONC_SUCCESS" "$EXPECTED_CONC_P95"

echo "\nDone."
