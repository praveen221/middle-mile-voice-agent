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
