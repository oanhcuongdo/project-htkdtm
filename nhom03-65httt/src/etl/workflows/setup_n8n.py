"""Cài đặt n8n cho EduVision BI: nạp credentials (lấy từ .env) và 3 workflow vào n8n đang chạy, tùy chọn kích hoạt.

Chạy từ thư mục nhom03-65httt sau khi `docker compose --profile automation up -d --build`:

    python src/etl/workflows/setup_n8n.py                          # nhập credentials và workflow (chưa kích hoạt gì)
    python src/etl/workflows/setup_n8n.py --activate alert webhook # kích hoạt email cảnh báo và webhook "Cập nhật dữ liệu"
    python src/etl/workflows/setup_n8n.py --activate daily         # kích hoạt lịch ETL hằng ngày (xem README: chỉ một bộ lập lịch)
    python src/etl/workflows/setup_n8n.py --deactivate daily
    python src/etl/workflows/setup_n8n.py --status

Bí mật (mật khẩu CSDL, khóa bộ chạy, khóa webhook, SMTP) đi thẳng từ .env vào n8n qua lệnh `docker exec -i` (stdin),
không ghi ra tệp trên máy và không in ra màn hình. Chạy lại nhiều lần an toàn (cập nhật theo mã cố định).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]                      # thư mục nhom03-65httt
WORKFLOW_IDS = {"daily": "eduvisionEtlDaily", "webhook": "eduvisionRefreshWebhook", "alert": "eduvisionAlertEmail"}
MIN_SECRET_LENGTH = 16


WORKFLOW_DIR = Path(__file__).resolve().parent
# Một địa chỉ duy nhất, không khoảng trắng, dấu phẩy hay xuống dòng (chặn chèn tiêu đề thư như "Bcc:").
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


class SetupError(RuntimeError):
    """Lỗi có thông báo rõ ràng cho người chạy."""


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_recipients(env: dict[str, str]) -> tuple[str | None, str | None]:
    """Địa chỉ nhận (ALERT_EMAIL_TO) và gửi (ALERT_EMAIL_FROM, hoặc SMTP_USER khi dùng SMTP thật). Rỗng thì giữ mặc định trong workflow."""
    to_email = (env.get("ALERT_EMAIL_TO") or "").strip() or None
    smtp_user = (env.get("SMTP_USER") or "").strip() if env.get("SMTP_HOST") else ""
    from_email = (env.get("ALERT_EMAIL_FROM") or "").strip() or smtp_user or None
    for name, value in (("ALERT_EMAIL_TO", to_email), ("ALERT_EMAIL_FROM/SMTP_USER", from_email)):
        if value is not None and not EMAIL_RE.fullmatch(value):
            raise SetupError(f"{name} không phải một địa chỉ email hợp lệ (chỉ một địa chỉ, không khoảng trắng hay dấu phẩy)")
    return to_email, from_email


def patch_workflow(workflow: dict, to_email: str | None, from_email: str | None) -> dict:
    """Bản sao workflow với địa chỉ nhận/gửi đã điền vào mọi nút Send Email. Không sửa bản gốc, không đụng nút khác."""
    patched = copy.deepcopy(workflow)
    for node in patched["nodes"]:
        if node["type"] == "n8n-nodes-base.emailSend":
            if to_email:
                node["parameters"]["toEmail"] = to_email
            if from_email:
                node["parameters"]["fromEmail"] = f"EduVision BI <{from_email}>"
    return patched


def import_workflows(container: str, to_email: str | None, from_email: str | None) -> str:
    """Nhập 3 workflow (đã điền người nhận) qua stdin vào thư mục tạm trong container, nhập xong thì xóa."""
    folder = "/tmp/eduvision_workflows"
    docker(container, "rm", "-rf", folder)
    try:
        for path in sorted(WORKFLOW_DIR.glob("*.json")):
            workflow = patch_workflow(json.loads(path.read_text(encoding="utf-8")), to_email, from_email)
            written = docker(container, "sh", "-c", f"mkdir -p {folder} && cat > {folder}/{path.name}",
                             stdin=json.dumps(workflow, ensure_ascii=False).encode("utf-8"))
            if written.returncode != 0:
                raise SetupError(f"Không ghi được {path.name} vào container n8n")
        return n8n(container, "import:workflow", "--separate", f"--input={folder}")
    finally:
        docker(container, "rm", "-rf", folder)


def build_credentials(env: dict[str, str]) -> list[dict]:
    """Ghép danh sách credentials theo định dạng nhập của n8n. Thiếu hoặc yếu thì báo lỗi rõ, không tự đặt mặc định cho bí mật."""
    missing = [k for k in ("POSTGRES_PASSWORD", "ETL_RUNNER_TOKEN", "N8N_WEBHOOK_KEY") if not env.get(k)]
    if missing:
        raise SetupError(f"Thiếu trong .env: {', '.join(missing)} (xem .env.example)")
    for key in ("ETL_RUNNER_TOKEN", "N8N_WEBHOOK_KEY"):
        if len(env[key]) < MIN_SECRET_LENGTH:
            raise SetupError(f"{key} phải dài ít nhất {MIN_SECRET_LENGTH} ký tự")
    if env["ETL_RUNNER_TOKEN"] == env["N8N_WEBHOOK_KEY"]:
        raise SetupError("ETL_RUNNER_TOKEN và N8N_WEBHOOK_KEY phải khác nhau (hai khóa cho hai việc khác nhau)")

    if env.get("SMTP_HOST"):                                    # SMTP thật do người dùng cấu hình trong .env
        secure = env.get("SMTP_SECURE", "").lower() in ("1", "true", "yes")
        smtp = {"host": env["SMTP_HOST"], "port": int(env.get("SMTP_PORT") or (465 if secure else 587)), "secure": secure,
                "disableStartTls": False, "user": env.get("SMTP_USER", ""), "password": env.get("SMTP_PASSWORD", "")}
    else:                                                       # mặc định: hộp thư thử Mailpit, không gửi ra ngoài
        smtp = {"host": "mailpit", "port": 1025, "secure": False, "disableStartTls": True,
                "user": "mailpit", "password": "mailpit"}

    return [
        {"id": "eduvisionRunnerKey", "name": "EduVision ETL Runner", "type": "httpHeaderAuth",
         "data": {"name": "X-Runner-Token", "value": env["ETL_RUNNER_TOKEN"]}},
        {"id": "eduvisionWebhookKey", "name": "EduVision Webhook Key", "type": "httpHeaderAuth",
         "data": {"name": "X-Webhook-Key", "value": env["N8N_WEBHOOK_KEY"]}},
        {"id": "eduvisionPostgres", "name": "EduVision PostgreSQL", "type": "postgres",
         "data": {"host": "postgres", "port": 5432, "database": env.get("POSTGRES_DB") or "eduvision",
                  "user": env.get("POSTGRES_USER") or "eduvision", "password": env["POSTGRES_PASSWORD"],
                  "ssl": "disable", "allowUnauthorizedCerts": False, "sshTunnel": False}},
        {"id": "eduvisionSmtp", "name": "EduVision SMTP", "type": "smtp", "data": smtp},
    ]


def docker(container: str, *args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "exec", *(["-i"] if stdin is not None else []), container, *args],
                          input=stdin, capture_output=True, check=False)


def n8n(container: str, *args: str) -> str:
    done = docker(container, "n8n", *args)
    text = (done.stdout + done.stderr).decode("utf-8", errors="replace")
    if done.returncode != 0:
        raise SetupError(f"Lệnh n8n {' '.join(args)} lỗi:\n{text.strip()[-600:]}")
    return "\n".join(line for line in text.splitlines() if "license SDK" not in line)


def ensure_running(container: str) -> None:
    done = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", container], capture_output=True, check=False)
    if done.returncode != 0 or done.stdout.strip() != b"true":
        raise SetupError(f"Container {container} chưa chạy. Chạy trước: docker compose --profile automation up -d --build")


def import_credentials(container: str, credentials: list[dict]) -> None:
    payload = json.dumps(credentials).encode("utf-8")
    target = "/tmp/eduvision_credentials.json"
    written = docker(container, "sh", "-c", f"umask 077 && cat > {target}", stdin=payload)
    if written.returncode != 0:
        raise SetupError("Không ghi được tệp credentials tạm vào container n8n")
    try:
        n8n(container, "import:credentials", f"--input={target}")
    finally:
        docker(container, "rm", "-f", target)                  # xóa ngay, không để bí mật nằm lại trong container


def active_workflow_ids(container: str) -> set[str]:
    """Mã các workflow đang kích hoạt (mỗi dòng của list:workflow có dạng mã|tên)."""
    lines = n8n(container, "list:workflow", "--active=true").splitlines()
    return {line.split("|", 1)[0].strip() for line in lines if "|" in line}


def set_active(container: str, names: list[str], active: bool) -> None:
    for name in names:
        n8n(container, "update:workflow", f"--id={WORKFLOW_IDS[name]}", f"--active={'true' if active else 'false'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nạp credentials và workflow vào n8n (EduVision BI)")
    parser.add_argument("--container", default="eduvision-n8n")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--activate", nargs="*", choices=sorted(WORKFLOW_IDS), default=[], metavar="TÊN",
                        help="kích hoạt: daily, webhook, alert")
    parser.add_argument("--deactivate", nargs="*", choices=sorted(WORKFLOW_IDS), default=[], metavar="TÊN")
    parser.add_argument("--status", action="store_true", help="chỉ liệt kê workflow và trạng thái kích hoạt")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        ensure_running(args.container)
        if args.status:
            print("Tất cả:\n" + n8n(args.container, "list:workflow").strip())
            print("Đang kích hoạt:\n" + (n8n(args.container, "list:workflow", "--active=true").strip() or "(không có)"))
            return 0
        if not args.deactivate or args.activate:
            # biến môi trường của phiên chạy thắng .env (giống cách Docker Compose xử lý)
            env = {**read_env_file(args.env_file),
                   **{k: v for k, v in os.environ.items() if k.startswith(("POSTGRES_", "SMTP_", "ETL_RUNNER_", "N8N_", "ALERT_EMAIL_"))}}
            credentials = build_credentials(env)                # kiểm tra đủ và đủ mạnh TRƯỚC khi đụng vào n8n
            to_email, from_email = resolve_recipients(env)
            was_active = active_workflow_ids(args.container)
            import_credentials(args.container, credentials)
            print("Đã nhập 4 credentials (PostgreSQL, SMTP, khóa bộ chạy ETL, khóa webhook).")
            print(import_workflows(args.container, to_email, from_email).strip().splitlines()[-1])
            print(f"Email gửi từ: {from_email or '(mặc định trong workflow)'} | gửi tới: {to_email or '(mặc định trong workflow)'}")
            # n8n tắt mọi workflow vừa nhập; bật lại những cái đang chạy trước đó để chạy lại script không làm mất kích hoạt
            keep = [name for name, wid in WORKFLOW_IDS.items() if wid in was_active and name not in args.deactivate]
            if keep:
                set_active(args.container, keep, True)
                print("Giữ nguyên trạng thái đang bật:", ", ".join(keep))
        if args.deactivate:
            set_active(args.container, args.deactivate, False)
            print("Đã tắt:", ", ".join(args.deactivate))
        if args.activate:
            set_active(args.container, args.activate, True)
            print("Đã kích hoạt:", ", ".join(args.activate), "(n8n áp dụng sau vài giây)")
        port = read_env_file(args.env_file).get("N8N_PORT") or "5678"
        print(f"\nWebhook 'Cập nhật dữ liệu': POST http://localhost:{port}/webhook/eduvision-refresh  (tiêu đề X-Webhook-Key)")
        print(f"Giao diện n8n: http://localhost:{port}    Hộp thư thử Mailpit: http://localhost:8025")
        return 0
    except SetupError as exc:
        print("LỖI:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
