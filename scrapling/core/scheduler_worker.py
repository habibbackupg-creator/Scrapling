from __future__ import annotations

import json
import os
import signal
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from scrapling.core.marketing_agent import build_marketing_insight
from scrapling.core.utils import log


class _StopSignal:
    def __init__(self) -> None:
        self._event = threading.Event()

    def stop(self, *_: object) -> None:
        self._event.set()

    def is_set(self) -> bool:
        return self._event.is_set()

    def wait(self, seconds: float) -> bool:
        return self._event.wait(seconds)


def _parse_num_set(field: str, min_value: int, max_value: int) -> set[int]:
    values: set[int] = set()
    for token in field.split(","):
        token = token.strip()
        if not token:
            continue
        if token == "*":
            values.update(range(min_value, max_value + 1))
            continue
        if "/" in token:
            left, step_raw = token.split("/", 1)
            step = max(1, int(step_raw))
            if left == "*":
                values.update(v for v in range(min_value, max_value + 1) if (v - min_value) % step == 0)
                continue
            token = left
            # Fall through for ranged steps.
            rng = token
            if "-" in rng:
                start_raw, end_raw = rng.split("-", 1)
                start = int(start_raw)
                end = int(end_raw)
                values.update(v for v in range(start, end + 1) if (v - start) % step == 0)
                continue
        if "-" in token:
            start_raw, end_raw = token.split("-", 1)
            start = int(start_raw)
            end = int(end_raw)
            values.update(range(start, end + 1))
            continue
        values.add(int(token))

    return {v for v in values if min_value <= v <= max_value}


def _cron_matches(expr: str, now: datetime) -> bool:
    parts = expr.split()
    if len(parts) != 5:
        return False

    minute = _parse_num_set(parts[0], 0, 59)
    hour = _parse_num_set(parts[1], 0, 23)
    day = _parse_num_set(parts[2], 1, 31)
    month = _parse_num_set(parts[3], 1, 12)
    weekday = _parse_num_set(parts[4], 0, 6)

    cron_weekday = (now.weekday() + 1) % 7
    return (
        now.minute in minute
        and now.hour in hour
        and now.day in day
        and now.month in month
        and cron_weekday in weekday
    )


def _request_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, method=method, headers=headers)
    with urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
    return json.loads(body or "{}")


def _goal_request_defaults(goal: str, url: str) -> dict[str, Any]:
    if goal == "contact":
        return {"url": url, "fmt": "txt", "css_selector": 'a[href^="mailto:"], a[href*="contact"], footer'}
    if goal == "lead":
        return {"url": url, "fmt": "txt", "css_selector": 'a[href], [class*="pricing"], [class*="demo"], [class*="sales"]'}
    if goal == "competitor":
        return {"url": url, "fmt": "md", "css_selector": 'h1, h2, [class*="feature"], [class*="pricing"], a[href]'}
    return {"url": url, "fmt": "txt", "css_selector": 'script, noscript, a[href], form'}


def run_scheduler_worker(ui_base_url: str | None = None, poll_seconds: int = 20) -> None:
    base = (ui_base_url or os.getenv("SCRAPLING_UI_URL") or f"http://127.0.0.1:{os.getenv('PORT', '8000')}").rstrip("/")
    stop_signal = _StopSignal()
    signal.signal(signal.SIGTERM, stop_signal.stop)
    signal.signal(signal.SIGINT, stop_signal.stop)

    last_minute_run: dict[str, str] = {}
    score_history: dict[str, list[int]] = {}

    log.info(f"Scheduler worker started against {base}")

    while not stop_signal.is_set():
        try:
            schedules_payload = _request_json("GET", f"{base}/api/schedules")
            schedules = list(schedules_payload.get("items") or [])
            now = datetime.now(tz=timezone.utc)
            minute_key = now.strftime("%Y-%m-%dT%H:%M")

            for schedule in schedules:
                job_id = str(schedule.get("id") or "")
                url = str(schedule.get("url") or "").strip()
                goal = str(schedule.get("goal") or "contact").strip() or "contact"
                expr = str(schedule.get("cron") or "").strip()

                if not job_id or not url or not expr:
                    continue

                if not _cron_matches(expr, now):
                    continue

                last_key = last_minute_run.get(job_id)
                if last_key == minute_key:
                    continue

                payload = _goal_request_defaults(goal, url)
                result = _request_json("POST", f"{base}/api/extract", payload)
                if not result.get("ok"):
                    log.warning(f"Scheduled extraction failed for {url}")
                    last_minute_run[job_id] = minute_key
                    continue

                previous = score_history.get(job_id, [])[-5:]
                insight = build_marketing_insight(
                    job_id=job_id,
                    goal=goal,
                    extract_payload={
                        "url": url,
                        "lead_score": result.get("lead_score", 0),
                        "tracker_hits": result.get("tracker_hits", []),
                        "cta_links": result.get("cta_links", []),
                        "social_links": result.get("social_links", []),
                    },
                    previous_scores=previous,
                )

                score_history.setdefault(job_id, []).append(insight.enhanced_score)
                _request_json("POST", f"{base}/api/marketing-insights", asdict(insight))
                log.info(f"Scheduled run completed for {url} ({goal}) -> {insight.enhanced_score}")
                last_minute_run[job_id] = minute_key

        except HTTPError as exc:
            log.error(f"Scheduler HTTP error: {exc}")
        except URLError as exc:
            log.error(f"Scheduler connection error: {exc}")
        except Exception as exc:  # pragma: no cover
            log.exception(f"Unexpected scheduler worker error: {exc}")

        stop_signal.wait(poll_seconds)

    log.info("Scheduler worker stopped")
