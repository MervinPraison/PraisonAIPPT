"""Tests for env-var overrides in praisonaippt.config."""

from praisonaippt.config import Config


def test_env_overrides_folder_id(monkeypatch, tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("gdrive:\n  folder_id: from_file\n")
    cfg = Config(config_path=cfg_file)
    monkeypatch.setenv("PRAISONAIPPT_GDRIVE_FOLDER_ID", "from_env")
    assert cfg.get_gdrive_folder_id() == "from_env"


def test_env_overrides_folder_name(monkeypatch, tmp_path):
    cfg = Config(config_path=tmp_path / "missing.yaml")
    monkeypatch.setenv("PRAISONAIPPT_GDRIVE_FOLDER_NAME", "Bible Decks")
    assert cfg.get_gdrive_folder_name() == "Bible Decks"


def test_env_overrides_credentials(monkeypatch, tmp_path):
    cfg = Config(config_path=tmp_path / "missing.yaml")
    monkeypatch.setenv("PRAISONAIPPT_GDRIVE_CREDENTIALS", "/tmp/cred.json")
    assert cfg.get_gdrive_credentials() == "/tmp/cred.json"


def test_falls_back_to_config_when_env_unset(monkeypatch, tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("gdrive:\n  folder_id: from_file\n")
    cfg = Config(config_path=cfg_file)
    monkeypatch.delenv("PRAISONAIPPT_GDRIVE_FOLDER_ID", raising=False)
    assert cfg.get_gdrive_folder_id() == "from_file"
