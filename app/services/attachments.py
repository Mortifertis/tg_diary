from __future__ import annotations

from pathlib import Path

from aiogram.types import Message

from app.constants import (ALLOWED_FILE_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS,
                           ENTRY_MEDIA_MAX_IMAGES)


class AttachmentValidationError(ValueError):
    """Raised when attachment payload is invalid."""


def parse_attachments(message: Message) -> list[dict[str, str]]:
    attachments: list[dict[str, str]] = []

    photos = message.photo or []
    if len(photos) > ENTRY_MEDIA_MAX_IMAGES:
        raise AttachmentValidationError("too_many_images")

    if photos:
        photo = photos[-1]
        attachments.append(
            {
                "type": "image",
                "file_id": photo.file_id,
                "file_name": "image_1.jpg",
                "extension": ".jpg",
            }
        )

    if message.document:
        document = message.document
        extension = Path(document.file_name or "").suffix.lower()
        if extension in ALLOWED_IMAGE_EXTENSIONS:
            attachment_type = "image"
        elif extension in ALLOWED_FILE_EXTENSIONS:
            attachment_type = "file"
        else:
            raise AttachmentValidationError(extension or "unknown")

        attachments.append(
            {
                "type": attachment_type,
                "file_id": document.file_id,
                "file_name": document.file_name or "document",
                "extension": extension or "unknown",
            }
        )

    return attachments


def has_entry_content(message: Message, attachments: list[dict[str, str]]) -> bool:
    return bool((message.text or message.caption or "").strip() or attachments)
