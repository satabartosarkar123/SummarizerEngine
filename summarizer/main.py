from __future__ import annotations

from typing import Optional

from . import summarize_text


def summarize_meeting(transcript: str, *, system_prompt: Optional[str] = None) -> str:
    return summarize_text(transcript, system_prompt=system_prompt)
