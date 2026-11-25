"""
Unit tests cho Giai đoạn 5: Multi-User Authentication (JWT + bcrypt),
Fernet mã hóa thông tin nguồn dữ liệu, và cấu hình Gemini AI Chat Agent.
"""

import pytest

from api.security import (
    create_access_token,
    decode_access_token,
    decrypt_config,
    encrypt_config,
    hash_password,
    verify_password,
)
from ai_service.chat_agent.gemini_agent import GeminiFinanceChatAgent


def test_bcrypt_password_hashing_and_verification():
    raw_pwd = "FinanceSecret@2026!"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert hashed.startswith("$2")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password(raw_pwd, "PENDING_INIT") is False


def test_jwt_access_token_roundtrip():
    token = create_access_token(user_id=42, email="student@tlu.edu.vn", full_name="Sinh Vien Nhom 13")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["email"] == "student@tlu.edu.vn"
    assert payload["full_name"] == "Sinh Vien Nhom 13"
    assert decode_access_token("invalid.jwt.token") is None


def test_fernet_config_encryption_roundtrip():
    secret_cfg = {
        "imap_email": "user@gmail.com",
        "imap_app_password": "abcd efgh ijkl mnop",
        "imap_host": "imap.gmail.com",
    }
    encrypted = encrypt_config(secret_cfg)
    assert isinstance(encrypted, str)
    assert "abcd efgh" not in encrypted
    decrypted = decrypt_config(encrypted)
    assert decrypted == secret_cfg
    assert decrypt_config("corrupted-token") == {}
    assert decrypt_config(None) == {}


def test_gemini_agent_registers_all_7_readonly_tools():
    agent = GeminiFinanceChatAgent(user_id=99)
    tools = agent._build_tools()
    tool_names = [fn.__name__ for fn in tools]
    expected = [
        "get_top_recipients",
        "get_top_senders",
        "get_spending_by_category",
        "get_monthly_cashflow",
        "get_burn_rate_and_forecast",
        "get_anomalies",
        "search_transactions",
    ]
    assert tool_names == expected
