from src.lab.catalog import LANGUAGE_NAMES, speech_catalog


def test_dropdown_languages_use_full_names():
    catalog = speech_catalog()
    for vendor in catalog["stt"] + catalog["tts"]:
        assert vendor["languages"], vendor["id"]
        for lang in vendor["languages"]:
            assert lang["id"]
            assert lang["label"] == LANGUAGE_NAMES[lang["id"]]
            assert lang["label"] != lang["id"] or lang["id"] in LANGUAGE_NAMES


def test_cartesia_tts_lists_indic_languages():
    tts = {row["id"]: row for row in speech_catalog()["tts"]}
    ids = {lang["id"] for lang in tts["cartesia"]["languages"]}
    assert {"hi", "kn", "ml", "ta", "te", "mr", "gu", "bn", "pa"} <= ids
    assert "or" not in ids


def test_deepgram_tts_is_english_only():
    tts = {row["id"]: row for row in speech_catalog()["tts"]}
    ids = [lang["id"] for lang in tts["deepgram"]["languages"]]
    assert ids == ["en"]
