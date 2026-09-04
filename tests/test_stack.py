from src.lab.stack import VoiceStack, normalize_stack


def test_smallest_tts_does_not_keep_sarvam_model():
    stack = normalize_stack(
        VoiceStack(stt="smallest", tts="smallest", tts_model="bulbul:v3", stt_model="saaras:v3")
    )
    assert stack.tts_model.startswith("lightning")
    assert stack.stt_model == "pulse"
    assert stack.tts_voice in {"sophia", "meher"}
