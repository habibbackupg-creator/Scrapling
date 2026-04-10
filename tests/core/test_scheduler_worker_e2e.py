import json
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

from scrapling.core import scheduler_worker


def _request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
    return json.loads(body or "{}")


def test_scheduler_worker_posts_insight_on_matching_minute(monkeypatch):
    state = {"schedules": [], "insights": []}

    class FakeAPIHandler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self):  # noqa: N802
            if self.path == "/api/schedules":
                self._send_json({"ok": True, "items": list(state["schedules"])})
                return
            if self.path == "/api/marketing-insights":
                self._send_json({"ok": True, "items": list(state["insights"])})
                return
            self.send_error(HTTPStatus.NOT_FOUND.value, "Not found")

        def do_POST(self):  # noqa: N802
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8") or "{}")

            if self.path == "/api/schedules":
                state["schedules"].append(payload)
                self._send_json({"ok": True, "item": payload}, status=HTTPStatus.CREATED)
                return

            if self.path == "/api/extract":
                self._send_json(
                    {
                        "ok": True,
                        "lead_score": 52,
                        "tracker_hits": ["ga"],
                        "cta_links": ["/demo"],
                        "social_links": ["https://linkedin.com/company/example"],
                    }
                )
                return

            if self.path == "/api/marketing-insights":
                state["insights"].append(payload)
                self._send_json({"ok": True}, status=HTTPStatus.CREATED)
                return

            self.send_error(HTTPStatus.NOT_FOUND.value, "Not found")

        def log_message(self, format, *args):  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeAPIHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{port}"

    fixed_now = datetime(2026, 4, 10, 21, 34, tzinfo=timezone.utc)
    cron_weekday = (fixed_now.weekday() + 1) % 7
    cron_expr = f"{fixed_now.minute} {fixed_now.hour} {fixed_now.day} {fixed_now.month} {cron_weekday}"

    schedule = {
        "id": "job-e2e-1",
        "url": "https://example.com",
        "goal": "marketing",
        "cron": cron_expr,
        "enabled": True,
        "created_at": fixed_now.isoformat(),
    }
    _request_json("POST", f"{base_url}/api/schedules", schedule)

    class _FixedDateTime:
        @staticmethod
        def now(tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

    class _OneLoopStopSignal:
        def __init__(self):
            self._stop = False

        def stop(self, *_):
            self._stop = True

        def is_set(self):
            return self._stop

        def wait(self, _seconds):
            self._stop = True
            return True

    monkeypatch.setattr(scheduler_worker, "datetime", _FixedDateTime)
    monkeypatch.setattr(scheduler_worker, "_StopSignal", _OneLoopStopSignal)
    monkeypatch.setattr(scheduler_worker.signal, "signal", lambda *_args, **_kwargs: None)

    try:
        scheduler_worker.run_scheduler_worker(ui_base_url=base_url, poll_seconds=1)
        insights_payload = _request_json("GET", f"{base_url}/api/marketing-insights")
        insights = list(insights_payload.get("items") or [])

        assert len(insights) == 1
        insight = insights[0]
        assert insight["job_id"] == "job-e2e-1"
        assert insight["url"] == "https://example.com"
        assert insight["goal"] == "marketing"
        assert isinstance(insight.get("enhanced_score"), int)
        assert "recommendation" in insight
    finally:
        server.shutdown()
        server.server_close()
