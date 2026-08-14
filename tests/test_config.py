from src.config import Settings


def test_stt_falls_back_to_deepgram():
    settings = Settings(
        _env_file=None, stt_provider="sarvam", sarvam_api_key="", deepgram_api_key="dg"
    )
    assert settings.resolved_stt() == "deepgram"


def test_tts_falls_back_to_azure():
    settings = Settings(
        _env_file=None,
        tts_provider="sarvam",
        sarvam_api_key="",
        azure_speech_key="k",
        azure_speech_region="centralindia",
    )
    assert settings.resolved_tts() == "azure"


def test_llm_prefers_openrouter():
    settings = Settings(
        _env_file=None,
        llm_provider="openrouter",
        openrouter_api_key="or",
        google_api_key="g",
    )
    assert settings.resolved_llm() == "openrouter"


def test_llm_falls_back_to_google():
    settings = Settings(
        _env_file=None,
        llm_provider="openrouter",
        openrouter_api_key="",
        google_api_key="g",
    )
    assert settings.resolved_llm() == "google"
