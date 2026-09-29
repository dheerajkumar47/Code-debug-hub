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
