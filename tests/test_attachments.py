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
