# Safe Stress Test Guide

This guide provides exact commands and expected metrics to validate Scrapling Web UI performance in a safe and legal way.

## What It Tests

- Sequential extraction reliability and latency.
- Concurrent extraction reliability and latency.
- Expected thresholds for success rate and p95 latency.

## Exact Command

```bash
bash scripts/safe_stress_test.sh
```

## Optional Command Variants

Test another deployment URL:

```bash
bash scripts/safe_stress_test.sh https://your-app.example.com
```

Tune request counts and thresholds:

```bash
SEQUENTIAL_RUNS=8 CONCURRENT_RUNS=15 CONCURRENCY=4 EXPECTED_SEQ_P95=15 EXPECTED_CONC_P95=20 bash scripts/safe_stress_test.sh
```

## Expected Metrics (Defaults)

- `sequential_success_rate >= 95%`
- `sequential_p95_seconds <= 12`
- `concurrent_success_rate >= 90%`
- `concurrent_p95_seconds <= 18`

The script prints `PASS` or `WARN` against these thresholds.

## Example Output

```text
sequential
  total_requests=5
  success_rate=100.00%
  p50_seconds=1.202
  p95_seconds=1.901
  status=PASS (expected success>=95%, p95<=12 s)

concurrent
  total_requests=10
  success_rate=100.00%
  p50_seconds=1.884
  p95_seconds=3.221
  status=PASS (expected success>=90%, p95<=18 s)
```

## Safety Notes

- Run only against your own app or targets where you have permission.
- Keep concurrency low and increase gradually.
- Do not attempt bypassing protections or violating terms of service.
