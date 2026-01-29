from __future__ import annotations

from app.constants import DAILY_PROMPT_SUFFIX, MONTHLY_PROMPT_PREFIX, WEEKLY_PROMPT_PREFIX
from app.models import EntryType


def build_prompt(entry_type: EntryType, question: str) -> str:
    if entry_type == EntryType.daily:
        return f"{question}\n{DAILY_PROMPT_SUFFIX}"
    if entry_type == EntryType.weekly:
        return f"{WEEKLY_PROMPT_PREFIX} {question}"
    return f"{MONTHLY_PROMPT_PREFIX} {question}"
