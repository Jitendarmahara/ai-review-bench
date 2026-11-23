"""Cloud Run deploy/verify for the report fixture (GCP twin of aws/deploy.py).
Subcommands: package, smoke [--docker], deploy, verify, delete. See gcp/GCP_SETUP.md."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["reports.py", "migrations", os.path.join("gcp", "main.py"), os.path.join("gcp", "Dockerfile")]

KNOWN_EVENT = {"report": "Weekly orders", "scheduled_at": 1700000000,
               "queue": "reports", "run_at": 1700000001}


def _run(cmd, **kw):
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=True, text=True, **kw)


def _out(cmd):
    return subprocess.run(cmd, check=True, text=True, capture_output=True).stdout.strip()


def cmd_package(a):
    missing = [p for p in REQUIRED if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        sys.exit(f"missing build inputs: {missing}")
    print("package ok — build context has:", ", ".join(REQUIRED))


def _assert_report(result):
    assert result["report"] == KNOWN_EVENT["report"], result
    assert result["delivered_this_run"] == 1, result
    assert result["receipt_at"] == KNOWN_EVENT["run_at"], result
    assert result["summary"] == {"delivered": 1, "pending": 0}, result
    print("smoke assertions passed:", json.dumps(result))


def cmd_smoke(a):
    if a.docker:
        image = "bench-gcp-smoke:local"
        _run(["docker", "build", "-f", "gcp/Dockerfile", "-t", image, "."], cwd=ROOT)
        cid = _out(["docker", "run", "-d", "-e", "SOURCE_COMMIT=smoke", "-e", "PORT=8080",
                    "-p", "8080:8080", image])
        try:
            _wait_http("http://127.0.0.1:8080/")
            result = _post_json("http://127.0.0.1:8080/", KNOWN_EVENT)
            _assert_report(result)
            assert result["commit"] == "smoke", result
        finally:
            subprocess.run(["docker", "rm", "-f", cid], check=False, capture_output=True, text=True)
        return
    os.environ.setdefault("SOURCE_COMMIT", "smoke")
    main = _import_file(os.path.join(ROOT, "gcp", "main.py"))
    _assert_report(main.run_experiment(dict(KNOWN_EVENT)))


def _import_file(path):
    import importlib.util
    sys.path.insert(0, ROOT)
    spec = importlib.util.spec_from_file_location("gcp_main", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_deploy(a):
    commit = a.commit or _out(["git", "rev-parse", "HEAD"])
    image = f"{a.region}-docker.pkg.dev/{a.project}/{a.repo}/{a.service}:{commit[:12]}"
    _run(["gcloud", "builds", "submit", "--project", a.project,
          "--config", "gcp/cloudbuild.yaml",
          f"--substitutions=_IMAGE={image},_COMMIT={commit}", "."], cwd=ROOT)
    _run(["gcloud", "run", "deploy", a.service, "--project", a.project,
          "--region", a.region, "--image", image,
          "--no-allow-unauthenticated", "--port", "8080",
          "--set-env-vars", f"SOURCE_COMMIT={commit}", "--quiet"])
    url = _service_url(a)
    print(json.dumps({"deployed": a.service, "image": image, "url": url, "commit": commit}))


def cmd_verify(a):
    url = _service_url(a)
    token = _out(["gcloud", "auth", "print-identity-token"])
    result = _post_json(url, KNOWN_EVENT, token=token)
    print(json.dumps(result, indent=2))
    assert result.get("report") == KNOWN_EVENT["report"], result
    assert result.get("receipt_at") == KNOWN_EVENT["run_at"], result
    assert result.get("commit") not in (None, "", "unknown"), result
    print("VERIFIED commit", result["commit"], "request_id", result["request_id"])


def cmd_delete(a):
    _run(["gcloud", "run", "services", "delete", a.service, "--project", a.project,
          "--region", a.region, "--quiet"])
    print("deleted", a.service)


def _service_url(a):
    return _out(["gcloud", "run", "services", "describe", a.service,
                 "--project", a.project, "--region", a.region,
                 "--format", "value(status.url)"])


def _post_json(url, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def _wait_http(url, tries=30, delay=0.3):
    last = None
    for _ in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                r.read()
                return
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(delay)
    raise RuntimeError(f"service did not come up: {last}")


def build_parser():
    p = argparse.ArgumentParser(prog="gcp/deploy.py", description="Cloud Run deploy for the report fixture")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("package").set_defaults(func=cmd_package)
    sm = sub.add_parser("smoke"); sm.set_defaults(func=cmd_smoke)
    sm.add_argument("--docker", action="store_true")
    for name, fn in (("deploy", cmd_deploy), ("verify", cmd_verify), ("delete", cmd_delete)):
        sp = sub.add_parser(name); sp.set_defaults(func=fn)
        sp.add_argument("--project", required=True)
        sp.add_argument("--region", default="us-central1")
        sp.add_argument("--service", default="ai-review-bench")
        if name == "deploy":
            sp.add_argument("--repo", default="bench")
            sp.add_argument("--commit")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
