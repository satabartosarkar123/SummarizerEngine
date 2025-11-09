# SummarizerEngine
## Links:
- Render Based UI: https://summarizerengine.onrender.com
- Render Dashboard: https://dashboard.render.com/web/srv-d3voo624d50c73ai3sh0

## Prerequisites
- Python 3.11+
- Groq API key with access to Whisper
- Mistral API key (for summarization)

## Setup
1. Create a virtual environment (`python -m venv venv`) and activate it.
2. Install dependencies:
   ```bash
   ./venv/bin/pip install -r requirements.txt
   ```
3. Copy `.env` and populate the secrets:
   ```env
   GROQ_API_KEY=your_groq_api_key
   GROQ_MODEL=whisper-large-v3
   MISTRAL_API_KEY=your_mistral_api_key
   MISTRAL_MODEL=mistral-large-latest
   FLASK_DEBUG=false
   PORT=5055
   ```
   Feel free to adjust `GROQ_MODEL`, `MISTRAL_MODEL`, or `PORT` as needed.

## Transcription
`transcribe_audio_file` in `transcribe.py` uses the Groq Python SDK to transcribe any supported audio file into text.

```python
from transcribe import transcribe_audio_file

text = transcribe_audio_file("/path/to/audio.mp3")
print(text)
```

Use `transcribe_audio` if you also need segment timing metadata:

```python
from transcribe import transcribe_audio

transcript, segments = transcribe_audio("/path/to/audio.mp3")
```

## Summarization
`summarizer.summarize_text` calls Mistral chat completions to condense transcripts into concise summaries:

```python
from summarizer import summarize_text

summary = summarize_text("Long transcript text...")
print(summary)
```

`summarizer.main.summarize_meeting` is a convenience wrapper for meeting transcripts.

## Running the API
Start the Flask backend (either command works):
```bash
FLASK_APP=app.py ./venv/bin/flask run --port "${PORT:-5055}"
# or
python app.py
```
Adjust `PORT` if it’s already in use.

Visit `http://localhost:${PORT:-5055}` for the web UI. Backend endpoints:
- `/api/transcribe` – upload audio via form-data `audio` (optional `summarize=true`) to receive transcript, segments, and summary.
- `/api/summarize` – POST JSON `{"text": "..."}` to summarize existing text.
- `/api/process` – upload audio via form-data `audio` to run full transcription + summarization workflow.

The frontend (served at `/`) lets you pick an audio file, sends it to `/api/process`, and renders the resulting summary, transcript, and segments.

## Vercel Deployment Notes
- Use a project name/slug that meets Vercel’s requirements: lowercase only, digits allowed, and the characters `.`, `_`, `-` (no `---`, max 100 chars). Example: `summarizer-engine`.
- Vercel automatically detects the Python runtime from `app.py`, so you do not need a custom `vercel.json`.
- If deploying via CLI, run `vercel --name summarizer-engine` (and `vercel --prod --name summarizer-engine` for production) to ensure the slug is valid.
- Configure environment variables in Vercel (`GROQ_API_KEY`, `MISTRAL_API_KEY`, optional model overrides, `FLASK_DEBUG`, `PORT`) for both Preview and Production scopes.

## Render Deployment Notes
- `gunicorn.conf.py` forces Gunicorn to bind to `0.0.0.0:${PORT}` so any start command that launches Gunicorn (e.g. `gunicorn app:app`) will satisfy Render’s port check.
- Do **not** set a manual `PORT` environment variable on Render—the platform injects it automatically.
- Build command: `pip install -r requirements.txt`
- Start command (if you need to enter it): `gunicorn app:app` (the config file adds the bind flag for you)
- Add the same secrets (`GROQ_API_KEY`, `MISTRAL_API_KEY`, etc.) under the service’s Environment tab.
