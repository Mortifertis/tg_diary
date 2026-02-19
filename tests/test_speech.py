from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.speech import (SpeechRecognitionError, _build_voice_filename,
                                 _convert_audio_to_wav, local_speech_available)


def test_build_voice_filename_for_ogg() -> None:
    voice = SimpleNamespace(file_unique_id="abc", mime_type="audio/ogg")

    assert _build_voice_filename(voice) == "voice_abc.ogg"


def test_build_voice_filename_for_mpeg() -> None:
    voice = SimpleNamespace(file_unique_id="abc", mime_type="audio/mpeg")

    assert _build_voice_filename(voice) == "voice_abc.mp3"


def test_convert_audio_to_wav_raises_on_ffmpeg_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    def _fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr("app.services.speech.subprocess.run", _fake_run)

    with pytest.raises(SpeechRecognitionError):
        _convert_audio_to_wav(tmp_path / "source.ogg", tmp_path / "target.wav")


def test_local_speech_available_false_without_ffmpeg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.speech._ffmpeg_available", lambda: False)
    monkeypatch.setattr("app.services.speech._whisper_available", lambda: True)

    assert local_speech_available() is False
