"""Bộ chạy ETL qua HTTP (dịch vụ `etl-runner` trong Docker Compose), để n8n lập lịch và nút "Cập nhật dữ liệu" gọi được.

Vì sao có dịch vụ này: n8n chạy trong Docker, không gọi được Python của máy. Dịch vụ này bọc `run_pipeline.py` (T8a)
sau ba điểm cuối đơn giản, chỉ nghe trong mạng Compose (không mở cổng ra ngoài):

    GET  /health   không cần khóa; dùng cho healthcheck
    GET  /status   cần khóa; trạng thái công việc hiện tại, công việc gần nhất và số ngày chạy liên tiếp
    POST /run      cần khóa; bắt đầu một vòng ETL chạy nền, trả 202 và mã công việc
                   (đang chạy: 409; bấm quá nhanh sau lần trước: 429)

Khóa gửi trong tiêu đề `X-Runner-Token`, đặt bằng biến môi trường ETL_RUNNER_TOKEN (từ 16 ký tự, bắt buộc).
Nội dung POST /run (JSON, tùy chọn): {"only": ["ELSA Speak"], "count": 100, "dry_run": false, "skip_collect": false}.
Chỉ nhận đúng các trường này; `only` phải là mã nền tảng có trong config/platforms.yml. Lệnh chạy được ghép từ giá trị đã
kiểm tra, không qua shell, nên không thể chèn lệnh.
Mỗi vòng ghi vào data/logs/pipeline_runs.jsonl như khi chạy tay (cùng khóa pipeline.lock nên không chạy chồng với Task Scheduler).
"""

from __future__ import annotations

import hmac
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ETL_DIR))

from common import load_platforms  # noqa: E402
from run_pipeline import consecutive_days, read_log  # noqa: E402

MAX_BODY = 4096
MIN_TOKEN_LENGTH = 16
ALLOWED_FIELDS = {"only", "count", "dry_run", "skip_collect"}
OUTPUT_TAIL_LINES = 25

_lock = threading.Lock()
_state: dict = {"current": None, "last": None, "finished_monotonic": None}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def min_interval() -> float:
    """Giây chờ tối thiểu sau khi một công việc kết thúc rồi mới nhận công việc mới (đề cương: chống bấm liên tục)."""
    try:
        return max(0.0, float(os.environ.get("ETL_RUNNER_MIN_INTERVAL", "60")))
    except ValueError:
        return 60.0


def validate_payload(body: object) -> tuple[list[str], dict]:
    """Trả về (danh sách lỗi, tham số đã chuẩn hóa). Chỉ nhận các trường đã liệt kê, đúng kiểu và đúng miền."""
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return ["nội dung phải là một đối tượng JSON"], {}
    errors = [f"trường không được hỗ trợ: {key}" for key in body if key not in ALLOWED_FIELDS]
    params: dict = {"only": [], "count": 100, "dry_run": False, "skip_collect": False}
    if "count" in body:
        count = body["count"]
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 500:
            errors.append("count phải là số nguyên từ 1 đến 500")
        else:
            params["count"] = count
    for flag in ("dry_run", "skip_collect"):
        if flag in body:
            if not isinstance(body[flag], bool):
                errors.append(f"{flag} phải là true hoặc false")
            else:
                params[flag] = body[flag]
    if "only" in body:
        only = body["only"]
        known = {p["id"] for p in load_platforms()}
        if not isinstance(only, list) or not all(isinstance(x, str) for x in only):
            errors.append("only phải là danh sách tên nền tảng")
        else:
            unknown = [x for x in only if x not in known]
            if unknown:
                errors.append(f"nền tảng không có trong cấu hình: {unknown}")
            else:
                params["only"] = only
    return errors, params


def build_command(params: dict) -> list[str]:
    """Ghép lệnh chạy run_pipeline.py từ tham số đã kiểm tra (danh sách đối số, không dùng shell)."""
    command = [sys.executable, str(ETL_DIR / "run_pipeline.py"), "--count", str(params["count"])]
    for platform_id in params["only"]:
        command += ["--only", platform_id]
    if params["dry_run"]:
        command.append("--dry-run")
    if params["skip_collect"]:
        command.append("--skip-collect")
    return command


def cycle_status_since(started_at: str) -> str | None:
    """Trạng thái vòng (success, partial, failed, dry_run) mà run_pipeline vừa ghi vào nhật ký sau thời điểm started_at."""
    entries = read_log()
    if not entries:
        return None
    latest = entries[-1]
    try:
        began = datetime.fromisoformat(str(latest.get("started_at")))
    except ValueError:
        return None
    return latest.get("status") if began >= datetime.fromisoformat(started_at) else None


def _run_job(job: dict, command: list[str]) -> None:
    started = time.monotonic()
    try:
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=3 * 3600)
        lines = (done.stdout + done.stderr).strip().splitlines()
        job.update(returncode=done.returncode, output_tail=lines[-OUTPUT_TAIL_LINES:])
        # mã 0: xong (success hoặc partial trong nhật ký); mã 4: đang có vòng khác giữ khóa pipeline.lock, vòng này bị bỏ qua
        job["status"] = "success" if done.returncode == 0 else ("skipped" if done.returncode == 4 else "failed")
        job["cycle_status"] = cycle_status_since(job["started_at"])
    except subprocess.TimeoutExpired:
        job.update(returncode=None, output_tail=["quá thời gian tối đa 3 giờ"], status="failed")
    except Exception as exc:  # noqa: BLE001 - mọi lỗi đều phải được ghi lại cho n8n thấy
        job.update(returncode=None, output_tail=[f"{type(exc).__name__}: {exc}"], status="failed")
    job["finished_at"] = now_iso()
    job["seconds"] = round(time.monotonic() - started, 1)
    with _lock:
        _state["last"], _state["current"], _state["finished_monotonic"] = job, None, time.monotonic()


def start_job(params: dict) -> tuple[int, dict]:
    """Bắt đầu công việc nếu được phép. Trả về (mã HTTP, nội dung)."""
    with _lock:
        if _state["current"] is not None:
            return 409, {"detail": "đang có một vòng chạy", "job_id": _state["current"]["job_id"]}
        finished = _state["finished_monotonic"]
        if finished is not None and time.monotonic() - finished < min_interval():
            wait = int(min_interval() - (time.monotonic() - finished)) + 1
            return 429, {"detail": f"vừa chạy xong, thử lại sau {wait} giây", "retry_after": wait}
        job = {"job_id": uuid.uuid4().hex[:12], "status": "running", "started_at": now_iso(), "params": params}
        _state["current"] = job
    threading.Thread(target=_run_job, args=(job, build_command(params)), daemon=True).start()
    return 202, {"job_id": job["job_id"], "status": "running", "started_at": job["started_at"]}


def status_payload() -> dict:
    with _lock:
        current, last = _state["current"], _state["last"]
    entries = read_log()
    days, streak = consecutive_days(entries)
    latest = entries[-1] if entries else None
    return {
        "running": current is not None,
        "current": current,
        "last_job": last,
        "last_logged_cycle": None if latest is None else {k: latest.get(k) for k in ("started_at", "status", "dry_run")},
        "success_days": days,
        "consecutive_days": streak,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "EduVisionRunner/1.0"

    def _send(self, code: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if code == 429 and "retry_after" in payload:
            self.send_header("Retry-After", str(payload["retry_after"]))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self) -> bool:
        expected = os.environ.get("ETL_RUNNER_TOKEN", "").encode("utf-8")
        given = self.headers.get("X-Runner-Token", "").encode("utf-8")
        return len(expected) >= MIN_TOKEN_LENGTH and hmac.compare_digest(given, expected)

    def do_GET(self) -> None:  # noqa: N802 - tên do http.server quy định
        if self.path == "/health":
            return self._send(200, {"status": "ok"})
        if not self._authorized():
            return self._send(401, {"detail": "thiếu hoặc sai khóa X-Runner-Token"})
        if self.path == "/status":
            return self._send(200, status_payload())
        self._send(404, {"detail": "không có điểm cuối này"})

    def do_POST(self) -> None:  # noqa: N802
        # Đọc hết nội dung (tối đa MAX_BODY) TRƯỚC khi trả lời bất kỳ mã nào; trả lời khi phía gọi còn đang gửi sẽ làm họ bị ngắt kết nối.
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self.close_connection = True
            return self._send(400, {"detail": "Content-Length không hợp lệ"})
        if length < 0 or length > MAX_BODY:
            self.close_connection = True
            return self._send(413, {"detail": f"nội dung quá lớn (tối đa {MAX_BODY} byte)"})
        raw = self.rfile.read(length) if length else b""
        if not self._authorized():
            return self._send(401, {"detail": "thiếu hoặc sai khóa X-Runner-Token"})
        if self.path != "/run":
            return self._send(404, {"detail": "không có điểm cuối này"})
        try:
            body = json.loads(raw.decode("utf-8")) if raw.strip() else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._send(400, {"detail": "nội dung không phải JSON hợp lệ"})
        errors, params = validate_payload(body)
        if errors:
            return self._send(422, {"detail": errors})
        code, payload = start_job(params)
        self._send(code, payload)

    def log_message(self, fmt: str, *args) -> None:  # ghi ra stderr của container, không kèm khóa
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))


def main() -> int:
    if len(os.environ.get("ETL_RUNNER_TOKEN", "")) < MIN_TOKEN_LENGTH:
        print(f"LỖI: đặt ETL_RUNNER_TOKEN (ít nhất {MIN_TOKEN_LENGTH} ký tự) trong .env rồi chạy lại.", file=sys.stderr)
        return 2
    port = int(os.environ.get("ETL_RUNNER_PORT", "8099"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"etl-runner nghe ở cổng {port} (chỉ trong mạng Compose)", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
