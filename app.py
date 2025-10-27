from __future__ import annotations

import os
import tempfile
import logging
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from summarizer import summarize_text
from summarizer.main import summarize_meeting
from transcribe import transcribe_audio, transcribe_audio_file

load_dotenv()
logging.basicConfig(level=logging.INFO)


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    @app.route("/", methods=["GET"])
    def index() -> str:
        return render_template("index.html")

    @app.route("/api/transcribe", methods=["POST"])
    def api_transcribe():
        if "audio" not in request.files:
            return jsonify({"error": "audio file is required"}), 400

        uploaded = request.files["audio"]
        if uploaded.filename == "":
            return jsonify({"error": "audio file is required"}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.filename).suffix) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name

        try:
            transcript, segments = transcribe_audio(tmp_path)
        except Exception as exc:  # pragma: no cover - propagated to client
            app.logger.exception("Failed to transcribe audio in /api/transcribe")
            return jsonify({"error": "Failed to transcribe audio"}), 500
        finally:
            os.unlink(tmp_path)

        summary = None
        if request.form.get("summarize") == "true":
            try:
                summary = summarize_text(transcript)
            except Exception as exc:  # pragma: no cover - propagated to client
                app.logger.exception("Failed to summarize transcript in /api/transcribe")
                return jsonify({"error": "Failed to summarize transcript", "transcript": transcript}), 500

        return jsonify({"transcript": transcript, "segments": segments, "summary": summary})

    @app.route("/api/process", methods=["GET", "POST"])
    def api_process():
        if request.method == "GET":
            return jsonify(
                {
                    "message": "Upload audio via POST multipart/form-data with field 'audio' to use this endpoint."
                }
            )

        if "audio" not in request.files:
            return jsonify({"error": "No audio uploaded"}), 400

        uploaded = request.files["audio"]
        if uploaded.filename == "":
            return jsonify({"error": "No audio uploaded"}), 400

        uploads_dir = Path(tempfile.gettempdir()) / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        target_path = uploads_dir / uploaded.filename
        uploaded.save(target_path)

        try:
            transcript, segments = transcribe_audio(str(target_path))
            summary = summarize_meeting(transcript)
        except Exception as exc:  # pragma: no cover - propagated to client
            app.logger.exception("Failed to process audio upload in /api/process")
            return jsonify({"error": "Failed to process audio upload"}), 500
        finally:
            try:
                target_path.unlink()
            except FileNotFoundError:
                app.logger.debug("Temporary file %s already cleaned up", target_path)
            except Exception:
                app.logger.exception("Failed to remove temporary file %s", target_path)

        return jsonify(
            {"transcript": transcript, "segments": segments, "summary": summary}
        )

    @app.route("/api/summarize", methods=["POST"])
    def api_summarize():
        payload = request.get_json(silent=True) or {}
        text = payload.get("text", "")
        if not text.strip():
            return jsonify({"error": "text is required"}), 400

        try:
            summary = summarize_text(text)
        except Exception as exc:  # pragma: no cover - propagated to client
            app.logger.exception("Failed to summarize text in /api/summarize")
            return jsonify({"error": "Failed to summarize text"}), 500

        return jsonify({"summary": summary})

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
