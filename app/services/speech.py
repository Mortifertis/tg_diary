from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Voice

from app.observability import EXTERNAL_API_ERRORS_TOTAL, emit_alert

if TYPE_CHECKING:
    from faster_whisper import WhisperModel


class SpeechRecognitionError(RuntimeError):
    """Raised when voice transcription fails."""


def _build_voice_filename(voice: Voice) -> str:
    suffix = ".ogg"
    if voice.mime_type == "audio/mpeg":
        suffix = ".mp3"
    return f"voice_{voice.file_unique_id}{suffix}"


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _whisper_available() -> bool:
    try:
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError:
        return False
    return True


def local_speech_available() -> bool:
    return _ffmpeg_available() and _whisper_available()


def _convert_audio_to_wav(source_path: Path, target_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-ar",
        "16000",
        "-ac",
        "1",
        str(target_path),
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SpeechRecognitionError("ffmpeg_failed")


def _build_whisper_model(model_name: str, device: str) -> WhisperModel:
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise SpeechRecognitionError("whisper_not_installed") from error
    return WhisperModel(model_name, device=device)


def _transcribe_wav_file(
    wav_path: Path,
    model_name: str,
    device: str,
) -> str:
    model = _build_whisper_model(model_name, device)
    segments, _ = model.transcribe(str(wav_path))
    text_parts: list[str] = []
    for segment in segments:
        segment_text = getattr(segment, "text", "")
        cleaned = str(segment_text).strip()
        if cleaned:
            text_parts.append(cleaned)
    return " ".join(text_parts).strip()


async def transcribe_voice(
    bot: Bot,
    voice: Voice,
    model_name: str,
    device: str,
) -> str:
    if not local_speech_available():
        raise SpeechRecognitionError("engine_unavailable")

    try:
        telegram_file = await bot.get_file(voice.file_id)
    except TelegramAPIError as error:
        EXTERNAL_API_ERRORS_TOTAL.labels(
            api="telegram",
            operation="get_file",
            error="telegram_api_error",
        ).inc()
        emit_alert(
            category="external_api",
            message="Failed to fetch Telegram voice file metadata",
            severity="warning",
            api="telegram",
            operation="get_file",
        )
        raise SpeechRecognitionError("telegram_get_file_failed") from error
    source_name = _build_voice_filename(voice)

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / source_name
        wav_path = Path(tmp_dir) / "voice.wav"
        try:
            await bot.download(
                telegram_file,
                destination=input_path,
            )
        except TelegramAPIError as error:
            EXTERNAL_API_ERRORS_TOTAL.labels(
                api="telegram",
                operation="download",
                error="telegram_api_error",
            ).inc()
            emit_alert(
                category="external_api",
                message="Failed to download Telegram voice file",
                severity="warning",
                api="telegram",
                operation="download",
            )
            raise SpeechRecognitionError("telegram_download_failed") from error
        _convert_audio_to_wav(input_path, wav_path)
        transcript = _transcribe_wav_file(wav_path, model_name, device)

    if not transcript:
        raise SpeechRecognitionError("empty_result")
    return transcript
