from __future__ import annotations

from types import SimpleNamespace

from app.services.attachments import parse_attachments


def test_parse_attachments_uses_only_largest_photo_size() -> None:
    message = SimpleNamespace(
        photo=[
            SimpleNamespace(file_id="small"),
            SimpleNamespace(file_id="medium"),
            SimpleNamespace(file_id="largest"),
        ],
        document=None,
    )

    attachments = parse_attachments(message)

    assert attachments == [
        {
            "type": "image",
            "file_id": "largest",
            "file_name": "image_1.jpg",
            "extension": ".jpg",
        }
    ]


def test_parse_attachments_includes_voice_message() -> None:
    message = SimpleNamespace(
        photo=[],
        document=None,
        voice=SimpleNamespace(
            file_id="voice-id",
            file_unique_id="voice-uid",
            mime_type="audio/ogg",
        ),
    )

    attachments = parse_attachments(message)

    assert attachments == [
        {
            "type": "file",
            "file_id": "voice-id",
            "file_name": "voice_voice-uid.ogg",
            "extension": ".ogg",
        }
    ]
