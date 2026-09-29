import importlib.util
from pathlib import Path

import yaml

spec = importlib.util.spec_from_file_location(
    "make_azure_setup", Path(__file__).resolve().parent.parent / "tools" / "make_azure_setup.py")
mas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mas)


def test_cloud_init_is_valid_yaml_with_env_service_and_https():
    env = "FREELANCER_TOKEN=abc\r\nDASHBOARD_PASSWORD=strongpass123\r\nDB_PATH=C:/x.db\r\n"
    text = mas.build(env, "bidsmith-d.uaenorth.cloudapp.azure.com")
    assert text.startswith("#cloud-config\n")
    cfg = yaml.safe_load(text)
    files = {f["path"]: f["content"] for f in cfg["write_files"]}
    env_out = files["/opt/bidsmith/env"]
    assert "\r" not in env_out and "C:/x.db" not in env_out
    assert "DB_PATH=data/bidsmith.db" in env_out and "FREELANCER_TOKEN=abc" in env_out
    assert "PUBLIC_BASE_URL=https://bidsmith-d.uaenorth.cloudapp.azure.com" in env_out
    assert "--host 127.0.0.1" in files["/etc/systemd/system/bidsmith.service"]
    assert files["/opt/bidsmith/Caddyfile"].startswith("bidsmith-d.uaenorth.cloudapp.azure.com {")
    assert "/opt/bidsmith/gh_token" not in files
    assert "#!/usr/bin/env bash" in files["/opt/bidsmith/update.sh"]
    assert not any("sudoers" in p for p in files)
    assert any("update.sh" in c for c in cfg["runcmd"])
