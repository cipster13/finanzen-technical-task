import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings

DEFAULT_MODEL = Settings.model_fields["openai_model"].default
DEFAULT_TIMEOUT = Settings.model_fields["openai_timeout"].default


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def load(monkeypatch, tmp_path):
    def _load(name: str | None = None, value: str = "", source: str = "env"):
        if name is None:
            return Settings(_env_file=None)
        if source == "env":
            monkeypatch.setenv(name, value)
            return Settings(_env_file=None)
        if source == "file":
            path = tmp_path / ".env"
            path.write_text(f"{name}={value}\n")
            return Settings(_env_file=path)
        return Settings(_env_file=None, **{name.lower(): value})

    return _load


class TestApiKey:
    def test_missing_key_is_rejected(self, load):
        with pytest.raises(ValidationError, match="openai_api_key"):
            load()

    @pytest.mark.parametrize("source", ["env", "file", "direct"])
    def test_empty_key_is_rejected(self, load, source):
        with pytest.raises(ValidationError, match="openai_api_key"):
            load("OPENAI_API_KEY", "", source)

    @pytest.mark.parametrize("source", ["env", "file"])
    def test_key_is_read(self, load, source):
        settings = load("OPENAI_API_KEY", "sk-test", source)

        assert settings.openai_api_key.get_secret_value() == "sk-test"

    def test_environment_wins_over_env_file(self, monkeypatch, tmp_path):
        path = tmp_path / ".env"
        path.write_text("OPENAI_API_KEY=sk-from-file\n")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")

        settings = Settings(_env_file=path)

        assert settings.openai_api_key.get_secret_value() == "sk-from-env"

    def test_key_is_masked_when_printed(self, load):
        settings = load("OPENAI_API_KEY", "sk-secret")

        assert "sk-secret" not in str(settings)
        assert "sk-secret" not in repr(settings)


class TestModelAndTimeout:
    @pytest.fixture(autouse=True)
    def api_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(None, id="not-set"),
            pytest.param("env", id="empty-in-env"),
            pytest.param("file", id="empty-in-file"),
        ],
    )
    def test_falls_back_to_defaults(self, load, source):
        settings = load("OPENAI_MODEL" if source else None, "", source or "env")

        assert settings.openai_model == DEFAULT_MODEL
        assert settings.openai_timeout == DEFAULT_TIMEOUT

    def test_custom_values_are_read(self, monkeypatch):
        monkeypatch.setenv("OPENAI_MODEL", "my-model")
        monkeypatch.setenv("OPENAI_TIMEOUT", "12.5")

        settings = Settings(_env_file=None)

        assert settings.openai_model == "my-model"
        assert settings.openai_timeout == 12.5

    def test_invalid_timeout_is_rejected(self, load):
        with pytest.raises(ValidationError, match="openai_timeout"):
            load("OPENAI_TIMEOUT", "soon")


def test_get_settings_returns_the_same_instance(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    get_settings.cache_clear()
    try:
        assert get_settings() is get_settings()
    finally:
        get_settings.cache_clear()
