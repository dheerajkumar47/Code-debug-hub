from bidsmith.config import Settings, clean_secret
from bidsmith.setup_wizard import run

FL = "fl_tok_1234567890abcdefghijkl"
AI = "AIzaSyA-1234567890abcdefghijklmnopqrs"


def _clear(monkeypatch):
    for k in ("FREELANCER_OAUTH_TOKEN", "LLM_API_KEY", "WHATSAPP_TOKEN", "WHATSAPP_APP_SECRET",
              "WHATSAPP_PHONE_NUMBER_ID", "OWNER_WHATSAPP", "DASHBOARD_PASSWORD", "WHATSAPP_VERIFY_TOKEN",
              "NOTIFY_CHANNELS", "LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)


def test_setup_writes_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    answers = iter(["gemini", "y", "+92 300 1234567", "12345"])
    secrets_ = iter([FL, AI, "EAAG" + "x" * 40, "a" * 32])
    path = run(".env", ask=lambda _: next(answers), ask_secret=lambda _: next(secrets_))
    text = path.read_text()
    assert f"FREELANCER_OAUTH_TOKEN={FL}" in text and "OWNER_WHATSAPP=923001234567" in text
    _clear(monkeypatch)
    s = Settings.load(str(path))
    assert s.freelancer_token == FL and s.llm_api_key == AI
    assert s.notify_channels[0] == "whatsapp" and len(s.dashboard_password) >= 12


def test_setup_minimal_without_whatsapp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    answers = iter(["", ""])  # default provider, no WhatsApp
    secrets_ = iter([FL, AI])
    text = run(".env", ask=lambda _: next(answers), ask_secret=lambda _: next(secrets_)).read_text()
    assert f"FREELANCER_OAUTH_TOKEN={FL}" in text and "NOTIFY_CHANNELS=web,console" in text


def test_failed_hidden_paste_falls_back_to_visible(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    answers = iter([f"  '{FL}'  ", "", ""])  # visible re-paste (with junk), provider, no WhatsApp
    secrets_ = iter(["\x16", AI])  # Ctrl+V in Windows hidden input gives a control char
    text = run(".env", ask=lambda _: next(answers), ask_secret=lambda _: next(secrets_)).read_text()
    assert f"FREELANCER_OAUTH_TOKEN={FL}\n" in text


def test_clean_secret():
    assert clean_secret(' "Bearer abc123" \r\n') == "abc123"
    assert clean_secret("\x16") == ""


def test_keys_file_import_and_delete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "keys.txt").write_text(
        "﻿FREELANCER: " + FL + "\r\nGEMINI: AQ.Ab8RN6Kabcdefghijklmnopqrstuvwxyz0123456789-5TCw\r\n", encoding="utf-8")
    text = run(".env", ask=lambda _: "", ask_secret=lambda _: "").read_text()
    assert f"FREELANCER_OAUTH_TOKEN={FL}\n" in text
    assert "LLM_API_KEY=AQ.Ab8RN6Kabcdefghijklmnopqrstuvwxyz0123456789-5TCw\n" in text
    assert "LLM_PROVIDER=gemini" in text
    assert not (tmp_path / "keys.txt").exists()


def test_keys_file_unlabeled_lines(tmp_path, monkeypatch):
    from bidsmith.setup_wizard import parse_keys_file
    out = parse_keys_file(f"{FL}\n\n{AI}\n")
    assert out == {"FREELANCER_OAUTH_TOKEN": FL, "LLM_PROVIDER": "gemini", "LLM_API_KEY": AI}


def test_keys_file_with_groq_backup(tmp_path, monkeypatch):
    from bidsmith.setup_wizard import parse_keys_file
    out = parse_keys_file(f"FREELANCER: {FL}\nGEMINI: {AI}\nGROQ: gsk_abcdefghijklmnopqrstuvwxyz123456\n")
    assert out["LLM_FALLBACK_KEY"].startswith("gsk_")
    assert out["LLM_FALLBACK_BASE_URL"] == "https://api.groq.com/openai/v1"
    # a keys.txt containing only the new Groq key keeps the existing keys
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(f"FREELANCER_OAUTH_TOKEN={FL}\nLLM_API_KEY={AI}\n")
    (tmp_path / "keys.txt").write_text("GROQ: gsk_abcdefghijklmnopqrstuvwxyz123456\n")
    text = run(".env", ask=lambda _: (_ for _ in ()).throw(AssertionError("should not ask")),
               ask_secret=lambda _: (_ for _ in ()).throw(AssertionError("should not ask"))).read_text()
    assert f"FREELANCER_OAUTH_TOKEN={FL}" in text and "LLM_FALLBACK_KEY=gsk_" in text


def test_adding_openai_keeps_gemini_and_orders_openai_first(tmp_path, monkeypatch):
    from bidsmith.app import build_llm
    from bidsmith.config import Settings
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(f"FREELANCER_OAUTH_TOKEN={FL}\nLLM_PROVIDER=gemini\nLLM_API_KEY={AI}\n"
                                   "LLM_FALLBACK_KEY=gsk_abcdefghijklmnopqrstuvwxyz123456\n")
    (tmp_path / "keys.txt").write_text("OPENAI: sk-proj-abcdefghijklmnopqrstuvwxyz0123456789\n")
    no = lambda _: (_ for _ in ()).throw(AssertionError("should not ask"))  # noqa: E731
    text = run(".env", ask=no, ask_secret=no).read_text()
    assert "OPENAI_API_KEY=sk-proj-" in text and f"GEMINI_API_KEY={AI}" in text and f"LLM_API_KEY={AI}" in text
    for k in ("OPENAI_API_KEY", "GEMINI_API_KEY", "LLM_API_KEY", "LLM_PROVIDER", "LLM_FALLBACK_KEY",
              "ANTHROPIC_API_KEY", "LLM_MODEL", "LLM_BASE_URL", "AI_ORDER"):
        monkeypatch.delenv(k, raising=False)
    chain = build_llm(Settings.load(".env"))
    assert chain.names == "OpenAI → Gemini → Groq"
