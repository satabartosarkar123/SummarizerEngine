from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

DEFAULT_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
DEFAULT_SYSTEM_PROMPT = (
    "You are a concise meeting assistant. Summarize the key points, decisions, "
    "and action items from the transcript. Use bullet points when appropriate."
)


def _create_client() -> Mistral:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not set in the environment")
    return Mistral(api_key=api_key)


def summarize_text(text: str, *, system_prompt: Optional[str] = None) -> str:
    if not text or not text.strip():
        raise ValueError("Input text for summarization cannot be empty")

    client = _create_client()
    model = DEFAULT_MODEL
    prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text},
    ]

    response = client.chat.complete(model=model, messages=messages)
    if not response or not response.choices:
        raise RuntimeError("Mistral response did not include any choices")

    message = response.choices[0].message
    if not message or not message.content:
        raise RuntimeError("Mistral response did not include message content")

    return message.content.strip()
