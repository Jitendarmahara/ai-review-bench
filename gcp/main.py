"""Cloud Run entrypoint. Runs one scheduled-report experiment and returns the same
evidence shape as aws/handler.py. Imports the app's reports.py; stdlib only."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import reports

SOURCE_COMMIT = os.environ.get("SOURCE_COMMIT", "unknown")
REVISION = os.environ.get("K_REVISION", "local")


def run_experiment(event):
    queue = event.get("queue", reports.DELIVERY_QUEUE)
    request_id = event.get("request_id") or str(uuid.uuid4())
    with closing(sqlite3.connect(":memory:")) as db:
        reports.migrate(db)
        job = reports.schedule(db, event["report"], int(event["scheduled_at"]))
        delivered = reports.deliver_due(db, queue, int(event["run_at"]))
        receipt = db.execute(
            "SELECT recorded_at FROM receipts WHERE delivery_id = ?", (job,)
        ).fetchone()
        return {
            "commit": SOURCE_COMMIT,
            "revision": REVISION,
            "request_id": request_id,
            "report": reports.history(db, 1).rows[0][1],
            "delivered_this_run": delivered,
            "receipt_at": receipt[0] if receipt else None,
            "summary": reports.summary(db),
        }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, {"status": "ok", "commit": SOURCE_COMMIT, "revision": REVISION})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            result = run_experiment(json.loads(raw or b"{}"))
        except KeyError as e:
            return self._send(400, {"error": f"missing field {e}"})
        except Exception as e:  # noqa: BLE001
            return self._send(500, {"error": str(e)})
        self._send(200, result)

    def log_message(self, *args):
        pass


def main():
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(json.dumps({"event": "listening", "port": port, "commit": SOURCE_COMMIT}))
    server.serve_forever()


if __name__ == "__main__":
    main()
