from maverick_engine.config.llm_settings import LLMSettings, load_llm_settings
import pytest


class TestLLMSettings:
    """Tests for LLMSettings configuration."""

    def test_default_values(self):
        """Test default settings values."""
        settings = LLMSettings()
        assert settings.model_name == "gpt-4o-mini"
        assert settings.temperature == 0.0
        assert settings.max_tokens == 256
        assert settings.timeout == 30
        assert settings.max_retries == 3
        assert settings.confidence_threshold == 0.7

    def test_has_api_key_true(self):
        """Test has_api_key returns True when key is set."""
        settings = LLMSettings(api_key="valid-key")
        assert settings.has_api_key is True

    def test_has_api_key_false_none(self):
        """Test has_api_key returns False when key is None."""
        settings = LLMSettings(api_key=None)
        assert settings.has_api_key is False

    def test_has_api_key_false_empty(self):
        """Test has_api_key returns False when key is empty."""
        settings = LLMSettings(api_key="")
        assert settings.has_api_key is False

    def test_has_api_key_false_whitespace(self):
        """Test has_api_key returns False when key is whitespace."""
        settings = LLMSettings(api_key="   ")
        assert settings.has_api_key is False

    def test_invalid_temperature_raises(self):
        """Test that invalid temperature raises ValueError."""
        with pytest.raises(ValueError, match="Temperature"):
            LLMSettings(temperature=2.5)

    def test_invalid_max_tokens_raises(self):
        """Test that invalid max_tokens raises ValueError."""
        with pytest.raises(ValueError, match="max_tokens"):
            LLMSettings(max_tokens=0)

    def test_invalid_timeout_raises(self):
        """Test that invalid timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout"):
            LLMSettings(timeout=0)

    def test_invalid_confidence_threshold_raises(self):
        """Test that invalid confidence_threshold raises ValueError."""
        with pytest.raises(ValueError, match="confidence_threshold"):
            LLMSettings(confidence_threshold=1.5)


class TestLoadLLMSettings:
    """Tests for load_llm_settings function."""

    def test_load_from_environment(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        monkeypatch.setenv("OPENAI_MODEL_NAME", "gpt-4")
        monkeypatch.setenv("OPENAI_TEMPERATURE", "0.5")
        monkeypatch.setenv("OPENAI_MAX_TOKENS", "512")
        monkeypatch.setenv("OPENAI_TIMEOUT", "60")
        monkeypatch.setenv("LLM_MAX_RETRIES", "5")
        monkeypatch.setenv("LLM_CONFIDENCE_THRESHOLD", "0.9")

        settings = load_llm_settings()

        assert settings.api_key == "test-key-123"
        assert settings.model_name == "gpt-4"
        assert settings.temperature == 0.5
        assert settings.max_tokens == 512
        assert settings.timeout == 60
        assert settings.max_retries == 5
        assert settings.confidence_threshold == 0.9

    def test_load_defaults_when_env_missing(self, monkeypatch):
        """Test that defaults are used when env vars are missing."""
        # Clear any existing env vars
        for key in ["OPENAI_API_KEY", "OPENAI_MODEL_NAME", "OPENAI_TEMPERATURE",
                    "OPENAI_MAX_TOKENS", "OPENAI_TIMEOUT", "LLM_MAX_RETRIES",
                    "LLM_CONFIDENCE_THRESHOLD"]:
            monkeypatch.delenv(key, raising=False)

        settings = load_llm_settings()

        assert settings.api_key is None
        assert settings.model_name == "gpt-4o-mini"
        assert settings.temperature == 0.0
        assert settings.max_tokens == 256

    def test_load_invalid_numeric_uses_default(self, monkeypatch):
        """Test that invalid numeric values use defaults."""
        monkeypatch.setenv("OPENAI_TEMPERATURE", "not_a_number")
        monkeypatch.setenv("OPENAI_MAX_TOKENS", "invalid")

        settings = load_llm_settings()

        assert settings.temperature == 0.0
        assert settings.max_tokens == 256