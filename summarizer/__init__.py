from __future__ import annotations

import os
import time
from typing import Optional

from dotenv import load_dotenv
from mistralai import Mistral
from mistralai.models import sdkerror

load_dotenv()


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


DEFAULT_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
DEFAULT_SYSTEM_PROMPT = (
    "You are a concise meeting assistant. Summarize the key points, decisions, "
    "and action items from the transcript. Use bullet points when appropriate."
)
DEFAULT_RETRY_ATTEMPTS = _int_env("MISTRAL_SUMMARY_RETRY_ATTEMPTS", 2)
DEFAULT_RETRY_DELAY_SECONDS = _float_env("MISTRAL_SUMMARY_RETRY_DELAY_SECONDS", 1.0)


class SummarizationServiceUnavailable(RuntimeError):
    """Raised when the remote LLM cannot fulfil the summarization request."""


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

    attempts = max(1, DEFAULT_RETRY_ATTEMPTS)
    delay = max(0.0, DEFAULT_RETRY_DELAY_SECONDS)
    response = None

    for attempt in range(1, attempts + 1):
        try:
            response = client.chat.complete(model=model, messages=messages)
            break
        except sdkerror.MistralError as err:
            if err.status_code == 429:
                if attempt == attempts:
                    raise SummarizationServiceUnavailable(
                        "Summarization temporarily unavailable due to Mistral capacity limits. Please try again shortly."
                    ) from err
                time.sleep(delay)
                continue
            raise

    if not response or not response.choices:
        raise RuntimeError("Mistral response did not include any choices")

    message = response.choices[0].message
    if not message or not message.content:
        raise RuntimeError("Mistral response did not include message content")

    return message.content.strip()


__all__ = ["summarize_text", "SummarizationServiceUnavailable"]
