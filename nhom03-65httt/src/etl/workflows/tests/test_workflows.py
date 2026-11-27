"""Kiểm thử phần không cần Docker: tệp workflow n8n (JSON), ghép credentials và các ràng buộc an toàn của setup_n8n.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

WORKFLOW_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKFLOW_DIR))

import setup_n8n  # noqa: E402

FILES = sorted(WORKFLOW_DIR.glob("*.json"))
GOOD_ENV = {"POSTGRES_PASSWORD": "mat-khau-csdl", "POSTGRES_USER": "eduvision", "POSTGRES_DB": "eduvision",
            "ETL_RUNNER_TOKEN": "khoa-bo-chay-etl-dai-du-16", "N8N_WEBHOOK_KEY": "khoa-webhook-dai-du-16-ky-tu"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_three_workflow_files_exist_and_ids_match_the_setup_script():
    assert [f.name for f in FILES] == ["01_etl_hang_ngay.json", "02_webhook_cap_nhat_du_lieu.json", "03_email_canh_bao.json"]
    assert {load(f)["id"] for f in FILES} == set(setup_n8n.WORKFLOW_IDS.values())


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_workflow_is_valid_and_connections_point_to_existing_nodes(path):
    wf = load(path)
    names = [n["name"] for n in wf["nodes"]]
    assert len(names) == len(set(names)), "tên nút phải duy nhất (connections dùng tên)"
    for source, outputs in wf["connections"].items():
        assert source in names
        for branch in outputs["main"]:
            for target in branch:
                assert target["node"] in names, f"{source} nối tới nút không tồn tại: {target['node']}"
    assert wf["active"] is False                              # nhập vào luôn ở trạng thái tắt; bật bằng setup_n8n.py --activate
    assert wf["settings"]["timezone"] == "Asia/Ho_Chi_Minh"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_workflow_files_contain_no_secrets_only_credential_references(path):
    text = path.read_text(encoding="utf-8")
    for forbidden in ("password", "token", "apikey", "secret"):
        # chỉ cho phép tên credential và khóa tham chiếu; không có giá trị bí mật
        for node in load(path)["nodes"]:
            params = json.dumps(node.get("parameters", {}), ensure_ascii=False).lower()
            assert f'"{forbidden}"' not in params
    assert "docker-compose" not in text
    for node in load(path)["nodes"]:
        for cred in (node.get("credentials") or {}).values():
            assert set(cred) == {"id", "name"}                 # chỉ mã và tên, không có dữ liệu


def test_every_credential_a_workflow_uses_is_created_by_the_setup_script():
    provided = {c["id"] for c in setup_n8n.build_credentials(GOOD_ENV)}
    used = {cred["id"] for f in FILES for n in load(f)["nodes"] for cred in (n.get("credentials") or {}).values()}
    assert used and used <= provided


def test_runner_calls_stay_inside_the_compose_network():
    for f in FILES:
        for node in load(f)["nodes"]:
            url = str(node["parameters"].get("url", ""))
            if url:
                assert url.startswith("http://etl-runner:8099/")


def test_alert_workflow_sends_each_alert_once_and_escapes_html():
    wf = load(WORKFLOW_DIR / "03_email_canh_bao.json")
    query = next(n for n in wf["nodes"] if n["name"] == "Lấy cảnh báo chưa gửi")["parameters"]["query"]
    assert "notified_at IS NULL" in query and "status = 'moi'" in query and "LIMIT" in query
    update = next(n for n in wf["nodes"] if n["name"] == "Đánh dấu đã gửi")["parameters"]["query"]
    assert "notified_at = now()" in update and "Number.isSafeInteger" in update
    code = next(n for n in wf["nodes"] if n["name"] == "Gộp thành một email")["parameters"]["jsCode"]
    assert "&lt;" in code and "esc(" in code
    order = [t["node"] for t in wf["connections"]["Gửi email cảnh báo"]["main"][0]]
    assert order == ["Đánh dấu đã gửi"]                       # đánh dấu SAU khi gửi: gửi lỗi thì không mất cảnh báo


def test_credentials_use_env_values_and_default_to_mailpit():
    creds = {c["id"]: c for c in setup_n8n.build_credentials(GOOD_ENV)}
    assert creds["eduvisionRunnerKey"]["data"] == {"name": "X-Runner-Token", "value": GOOD_ENV["ETL_RUNNER_TOKEN"]}
    assert creds["eduvisionWebhookKey"]["data"]["name"] == "X-Webhook-Key"
    assert creds["eduvisionPostgres"]["data"]["host"] == "postgres" and creds["eduvisionPostgres"]["data"]["password"] == "mat-khau-csdl"
    assert creds["eduvisionSmtp"]["data"]["host"] == "mailpit"            # mặc định không gửi ra Internet


def test_real_smtp_is_used_only_when_configured():
    env = dict(GOOD_ENV, SMTP_HOST="smtp.gmail.com", SMTP_USER="a@gmail.com", SMTP_PASSWORD="mat-khau-ung-dung", SMTP_SECURE="true")
    smtp = {c["id"]: c for c in setup_n8n.build_credentials(env)}["eduvisionSmtp"]["data"]
    assert smtp["host"] == "smtp.gmail.com" and smtp["port"] == 465 and smtp["secure"] is True


@pytest.mark.parametrize("env, message", [
    ({k: v for k, v in GOOD_ENV.items() if k != "ETL_RUNNER_TOKEN"}, "Thiếu trong .env"),
    ({k: v for k, v in GOOD_ENV.items() if k != "N8N_WEBHOOK_KEY"}, "Thiếu trong .env"),
    ({k: v for k, v in GOOD_ENV.items() if k != "POSTGRES_PASSWORD"}, "Thiếu trong .env"),
    (dict(GOOD_ENV, ETL_RUNNER_TOKEN="ngan"), "ít nhất"),
    (dict(GOOD_ENV, N8N_WEBHOOK_KEY="ngan"), "ít nhất"),
    (dict(GOOD_ENV, N8N_WEBHOOK_KEY=GOOD_ENV["ETL_RUNNER_TOKEN"]), "khác nhau"),
])
def test_weak_or_missing_secrets_are_refused(env, message):
    with pytest.raises(setup_n8n.SetupError, match=message):
        setup_n8n.build_credentials(env)


def test_env_file_parser_ignores_comments_and_strips_quotes(tmp_path):
    path = tmp_path / ".env"
    path.write_text('# ghi chú\nA=1\nB="hai"\n\nC = ba \nKHONG_CO_DAU_BANG\n', encoding="utf-8")
    assert setup_n8n.read_env_file(path) == {"A": "1", "B": "hai", "C": "ba"}
    assert setup_n8n.read_env_file(tmp_path / "khong_co") == {}


# ---------------------------------------------------------------- người nhận email (ALERT_EMAIL_TO)
def test_patch_workflow_sets_recipient_only_on_email_nodes_and_keeps_the_original():
    original = load(WORKFLOW_DIR / "03_email_canh_bao.json")
    before = json.dumps(original, sort_keys=True)
    patched = setup_n8n.patch_workflow(original, "nguoi.nhan@gmail.com", "gui@gmail.com")
    assert json.dumps(original, sort_keys=True) == before                  # không sửa bản gốc
    emails = [n for n in patched["nodes"] if n["type"] == "n8n-nodes-base.emailSend"]
    assert emails and all(n["parameters"]["toEmail"] == "nguoi.nhan@gmail.com" for n in emails)
    assert all(n["parameters"]["fromEmail"] == "EduVision BI <gui@gmail.com>" for n in emails)
    others = [n for n in patched["nodes"] if n["type"] != "n8n-nodes-base.emailSend"]
    assert others == [n for n in original["nodes"] if n["type"] != "n8n-nodes-base.emailSend"]


def test_patch_workflow_without_addresses_keeps_defaults():
    original = load(WORKFLOW_DIR / "01_etl_hang_ngay.json")
    assert setup_n8n.patch_workflow(original, None, None) == original


def test_every_workflow_with_email_nodes_gets_patched():
    for f in FILES:
        patched = setup_n8n.patch_workflow(load(f), "a@b.vn", None)
        for node in patched["nodes"]:
            if node["type"] == "n8n-nodes-base.emailSend":
                assert node["parameters"]["toEmail"] == "a@b.vn"


def test_recipients_come_from_env_and_gmail_sender_defaults_to_smtp_user():
    assert setup_n8n.resolve_recipients({}) == (None, None)
    assert setup_n8n.resolve_recipients({"ALERT_EMAIL_TO": "a@gmail.com"}) == ("a@gmail.com", None)
    env = {"ALERT_EMAIL_TO": "a@gmail.com", "SMTP_HOST": "smtp.gmail.com", "SMTP_USER": "b@gmail.com"}
    assert setup_n8n.resolve_recipients(env) == ("a@gmail.com", "b@gmail.com")    # Gmail yêu cầu From là tài khoản đăng nhập
    env["ALERT_EMAIL_FROM"] = "c@gmail.com"
    assert setup_n8n.resolve_recipients(env)[1] == "c@gmail.com"
    assert setup_n8n.resolve_recipients({"SMTP_USER": "b@gmail.com"}) == (None, None)    # không có SMTP_HOST thì bỏ qua SMTP_USER


@pytest.mark.parametrize("bad", ["khong-phai-email", "a b@c.com", "a@b.com,c@d.com", "a@b.com\nBcc: x@y.com",
                                 "a@b.com\r\nSubject: x", "@b.com", "a@b", "a@b.com;c@d.com", "<a@b.com>"])
def test_unsafe_or_invalid_addresses_are_refused(bad):
    with pytest.raises(setup_n8n.SetupError, match="email hợp lệ"):
        setup_n8n.resolve_recipients({"ALERT_EMAIL_TO": bad})
