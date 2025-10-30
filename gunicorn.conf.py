import os
from typing import Optional


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _optional_int_env(name: str) -> Optional[int]:
    raw = os.getenv(name)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


# Ensure the web dyno binds to the port exposed by the hosting platform.
bind = f"0.0.0.0:{os.getenv('PORT', '5055')}"

# Allow Render's WEB_CONCURRENCY hint to scale workers, defaulting to 1 locally.
workers = _int_env("WEB_CONCURRENCY", 1)

# Long audio files can take a while to transcribe, so we give the worker extra time.
timeout = _int_env("GUNICORN_TIMEOUT", 180)
graceful_timeout = _int_env("GUNICORN_GRACEFUL_TIMEOUT", timeout + 30)

# Allow optional tuning of keepalive without requiring it to be set.
keepalive_val = _optional_int_env("GUNICORN_KEEPALIVE")
if keepalive_val is not None:
    keepalive = keepalive_val
