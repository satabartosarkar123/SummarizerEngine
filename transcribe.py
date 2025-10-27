from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Sequence, Tuple

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "whisper-large-v3")


def _create_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in the environment")
    return Groq(api_key=api_key)


def transcribe_audio(
    path: str, *, model: Optional[str] = None
) -> Tuple[str, Sequence[dict]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    client = _create_client()
    model_name = model or DEFAULT_MODEL

    with file_path.open("rb") as audio_file:
        response = client.audio.transcriptions.with_raw_response.create(
            file=(file_path.name, audio_file.read()),
            model=model_name,
            response_format="verbose_json",
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Groq transcription failed with status {response.status_code}: {response.text}"
        )

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        transcript = (payload.get("text") or "").strip()
        segments = payload.get("segments") or []
        if transcript:
            return transcript, segments
        raise RuntimeError("Groq transcription response did not include text")

    text = response.text.strip()
    if text:
        return text, []

    raise RuntimeError("Groq transcription response did not return usable data")


def transcribe_audio_file(path: str, *, model: Optional[str] = None) -> str:
    transcript, _ = transcribe_audio(path, model=model)
    return transcript
