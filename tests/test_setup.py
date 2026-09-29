from bidsmith.config import Settings
from bidsmith.setup_wizard import run


def test_setup_writes_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    answers = iter(["gemini", "y", "+92 300 1234567", "12345"])
    secrets_ = iter(["FL_TOKEN", "AI_KEY", "WA_TOKEN", "APP_SECRET"])
    path = run(".env", ask=lambda _: next(answers), ask_secret=lambda _: next(secrets_))
    text = path.read_text()
    assert "FREELANCER_OAUTH_TOKEN=FL_TOKEN" in text and "OWNER_WHATSAPP=923001234567" in text
    for k in ("FREELANCER_OAUTH_TOKEN", "LLM_API_KEY", "WHATSAPP_TOKEN", "WHATSAPP_APP_SECRET",
              "WHATSAPP_PHONE_NUMBER_ID", "OWNER_WHATSAPP", "DASHBOARD_PASSWORD", "WHATSAPP_VERIFY_TOKEN",
              "NOTIFY_CHANNELS", "LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    s = Settings.load(str(path))
    assert s.freelancer_token == "FL_TOKEN" and s.llm_api_key == "AI_KEY"
    assert s.notify_channels[0] == "whatsapp" and len(s.dashboard_password) >= 12


def test_setup_minimal_without_whatsapp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    answers = iter(["", ""])  # no WhatsApp, default provider
    secrets_ = iter(["FL", "KEY"])
    text = run(".env", ask=lambda _: next(answers), ask_secret=lambda _: next(secrets_)).read_text()
    assert "FREELANCER_OAUTH_TOKEN=FL" in text and "NOTIFY_CHANNELS=web,console" in text
