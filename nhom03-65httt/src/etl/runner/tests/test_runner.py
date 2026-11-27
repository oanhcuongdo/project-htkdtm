"""Kiểm thử bộ chạy ETL qua HTTP: xác thực, kiểm tra đầu vào, chống chèn lệnh, chạy nền và giới hạn tần suất.

Không gọi pipeline thật: subprocess.run được thay bằng hàm giả. Máy chủ chạy thật trên cổng ngẫu nhiên của 127.0.0.1.
"""

from __future__ import annotations

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

RUNNER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNNER_DIR))

import runner  # noqa: E402
from run_pipeline import append_log  # noqa: E402

TOKEN = "khoa-thu-nghiem-dai-hon-16-ky-tu"


@pytest.fixture()
def server(monkeypatch, tmp_path):
    monkeypatch.setenv("ETL_RUNNER_TOKEN", TOKEN)
    monkeypatch.setenv("ETL_RUNNER_MIN_INTERVAL", "0")
    monkeypatch.setenv("EDUVISION_LOG_DIR", str(tmp_path))          # không đụng nhật ký thật
    monkeypatch.setattr(runner, "_state", {"current": None, "last": None, "finished_monotonic": None})
    calls: list[list[str]] = []
    gate = threading.Event()
    gate.set()

    def fake_run(command, **kwargs):
        calls.append(command)
        gate.wait(5)
        return SimpleNamespace(returncode=0, stdout="xong\n", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), runner.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    yield SimpleNamespace(base=base, calls=calls, gate=gate)
    gate.set()
    httpd.shutdown()


def call(base, path, method="GET", body=None, token=TOKEN, raw=None):
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode("utf-8"))
    request = urllib.request.Request(base + path, data=data, method=method)
    if token is not None:
        request.add_header("X-Runner-Token", token)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def wait_idle(base, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not call(base, "/status")[1]["running"]:
            return
        time.sleep(0.05)
    raise AssertionError("công việc không kết thúc")


def test_health_needs_no_token_but_everything_else_does(server):
    assert call(server.base, "/health", token=None) == (200, {"status": "ok"})
    assert call(server.base, "/status", token=None)[0] == 401
    assert call(server.base, "/status", token="sai-khoa-sai-khoa-sai")[0] == 401
    assert call(server.base, "/run", "POST", {}, token=None)[0] == 401
    assert call(server.base, "/run", "POST", {}, token="")[0] == 401
    assert server.calls == []                                        # chưa ai được phép thì chưa chạy gì


def test_short_or_missing_server_token_rejects_everyone(server, monkeypatch):
    monkeypatch.setenv("ETL_RUNNER_TOKEN", "ngan")
    assert call(server.base, "/status", token="ngan")[0] == 401      # khóa quá ngắn: từ chối cả khi khớp
    monkeypatch.delenv("ETL_RUNNER_TOKEN")
    assert call(server.base, "/status", token="")[0] == 401


def test_run_starts_in_background_and_reports_result(server):
    code, body = call(server.base, "/run", "POST", {"only": ["ELSA Speak"], "count": 20, "dry_run": True})
    assert code == 202 and body["status"] == "running" and len(body["job_id"]) == 12
    wait_idle(server.base)
    status = call(server.base, "/status")[1]
    assert status["last_job"]["status"] == "success" and status["last_job"]["output_tail"] == ["xong"]
    command = server.calls[0]
    assert command[command.index("--count") + 1] == "20" and "--only" in command and "--dry-run" in command


def test_default_body_runs_with_count_100(server):
    assert call(server.base, "/run", "POST")[0] == 202             # không gửi nội dung vẫn chạy với giá trị mặc định
    wait_idle(server.base)
    command = server.calls[0]
    assert command[command.index("--count") + 1] == "100" and "--dry-run" not in command and "--only" not in command


@pytest.mark.parametrize("body", [
    {"count": 0}, {"count": 501}, {"count": "100"}, {"count": True}, {"count": 1.5},
    {"dry_run": "yes"}, {"skip_collect": 1}, {"only": "ELSA Speak"}, {"only": [1]}, {"only": ["Khong Co"]},
    {"command": "rm -rf /"}, {"only": ["ELSA Speak; rm -rf /"]}, [], "chuoi",
])
def test_bad_payloads_are_rejected_without_running(server, body):
    code, payload = call(server.base, "/run", "POST", body)
    assert code == 422 and payload["detail"]
    assert server.calls == []


def test_malformed_json_and_oversize_body(server):
    assert call(server.base, "/run", "POST", raw=b"{khong phai json")[0] == 400
    assert call(server.base, "/run", "POST", raw=b"\xff\xfe\xfd")[0] == 400
    assert call(server.base, "/run", "POST", raw=b"{" + b" " * 5000 + b"}")[0] == 413
    assert server.calls == []


def test_second_run_while_running_gets_409_then_works_after_finish(server):
    server.gate.clear()
    first = call(server.base, "/run", "POST", {"dry_run": True})
    assert first[0] == 202
    code, body = call(server.base, "/run", "POST", {"dry_run": True})
    assert code == 409 and body["job_id"] == first[1]["job_id"]      # không sinh công việc thứ hai
    assert call(server.base, "/status")[1]["running"] is True
    server.gate.set()
    wait_idle(server.base)
    assert call(server.base, "/run", "POST", {"dry_run": True})[0] == 202
    wait_idle(server.base)
    assert len(server.calls) == 2


def test_cooldown_after_a_finished_job_returns_429(server, monkeypatch):
    monkeypatch.setenv("ETL_RUNNER_MIN_INTERVAL", "600")
    assert call(server.base, "/run", "POST", {"dry_run": True})[0] == 202
    wait_idle(server.base)
    code, body = call(server.base, "/run", "POST", {"dry_run": True})
    assert code == 429 and body["retry_after"] > 0
    assert len(server.calls) == 1


def test_failed_pipeline_is_reported_as_failed(server, monkeypatch):
    monkeypatch.setattr(runner.subprocess, "run",
                        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="LỖI: không nối được CSDL"))
    call(server.base, "/run", "POST", {"dry_run": True})
    wait_idle(server.base)
    job = call(server.base, "/status")[1]["last_job"]
    assert job["status"] == "failed" and job["returncode"] == 1 and "không nối được" in job["output_tail"][-1]


def test_lock_held_exit_code_is_reported_as_skipped_not_failed(server, monkeypatch):
    monkeypatch.setattr(runner.subprocess, "run",
                        lambda *a, **k: SimpleNamespace(returncode=4, stdout="", stderr="Đang có vòng khác chạy"))
    call(server.base, "/run", "POST", {"dry_run": True})
    wait_idle(server.base)
    assert call(server.base, "/status")[1]["last_job"]["status"] == "skipped"


def test_cycle_status_is_read_from_the_pipeline_log(server, monkeypatch):
    def fake_run(command, **kwargs):
        append_log({"run_id": "x", "started_at": runner.now_iso(), "status": "partial", "dry_run": False})
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    call(server.base, "/run", "POST", {"dry_run": True})
    wait_idle(server.base)
    job = call(server.base, "/status")[1]["last_job"]
    assert job["status"] == "success" and job["cycle_status"] == "partial"      # chạy xong nhưng một collector lỗi


def test_old_log_entries_are_not_mistaken_for_this_job(server):
    append_log({"run_id": "cu", "started_at": "2020-01-01T00:00:00+00:00", "status": "failed", "dry_run": False})
    call(server.base, "/run", "POST", {"dry_run": True})
    wait_idle(server.base)
    assert call(server.base, "/status")[1]["last_job"]["cycle_status"] is None


def test_unknown_paths_are_404(server):
    assert call(server.base, "/khong-co")[0] == 404
    assert call(server.base, "/khong-co", "POST", {})[0] == 404


def test_build_command_never_uses_a_shell_string():
    command = runner.build_command({"only": ["Khan Academy"], "count": 5, "dry_run": False, "skip_collect": True})
    assert isinstance(command, list) and command[-1] == "--skip-collect" and "Khan Academy" in command


def test_main_refuses_to_start_without_a_strong_token(monkeypatch, capsys):
    monkeypatch.delenv("ETL_RUNNER_TOKEN", raising=False)
    assert runner.main() == 2
    assert "ETL_RUNNER_TOKEN" in capsys.readouterr().err
