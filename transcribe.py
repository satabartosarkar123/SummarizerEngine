from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional, Sequence, Tuple

import httpx
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "whisper-large-v3")
DEFAULT_TIMEOUT_SECONDS = 240.0
MAX_CONNECT_TIMEOUT_SECONDS = 30.0


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid value for %s: %r – using default %.1f", name, raw, default)
        return default


def _groq_timeout() -> Tuple[Optional[httpx.Timeout], Optional[float]]:
    timeout_seconds = _float_env("GROQ_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
    if timeout_seconds <= 0:
        return None, None

    connect_timeout = min(timeout_seconds, MAX_CONNECT_TIMEOUT_SECONDS)
    timeout = httpx.Timeout(
        timeout=timeout_seconds,
        connect=connect_timeout,
        read=timeout_seconds,
        write=timeout_seconds,
    )
    return timeout, timeout_seconds


def _create_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in the environment")
    timeout, timeout_seconds = _groq_timeout()
    if timeout:
        logger.debug(
            "Creating Groq client with read timeout %.1fs and connect timeout %.1fs",
            timeout_seconds,
            timeout.connect,
        )
    else:
        logger.debug("Creating Groq client with default timeout settings")
    return Groq(api_key=api_key, timeout=timeout)


def transcribe_audio(
    path: str, *, model: Optional[str] = None
) -> Tuple[str, Sequence[dict]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    client = _create_client()
    model_name = model or DEFAULT_MODEL

    try:
        file_size = file_path.stat().st_size
    except OSError:
        file_size = None

    size_desc = f"{file_size} bytes" if file_size is not None else "unknown size"
    logger.info("Starting Groq transcription for %s (%s) using %s", file_path.name, size_desc, model_name)

    start_time = time.perf_counter()

    try:
        with file_path.open("rb") as audio_file:
            response = client.audio.transcriptions.with_raw_response.create(
                file=(file_path.name, audio_file.read()),
                model=model_name,
                response_format="verbose_json",
            )
    except httpx.TimeoutException as exc:
        elapsed = time.perf_counter() - start_time
        logger.error("Groq transcription timed out after %.1fs for %s", elapsed, file_path)
        raise RuntimeError(f"Groq transcription timed out after {elapsed:.1f}s") from exc
    except httpx.HTTPError as exc:
        elapsed = time.perf_counter() - start_time
        logger.error("Groq transcription HTTP error after %.1fs for %s: %s", elapsed, file_path, exc)
        raise RuntimeError("Groq transcription request failed") from exc

    elapsed = time.perf_counter() - start_time
    logger.info("Groq transcription completed in %.1fs for %s", elapsed, file_path)

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
