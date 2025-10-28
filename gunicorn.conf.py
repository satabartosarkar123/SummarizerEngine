import os

# Ensure the web dyno binds to the port exposed by the hosting platform.
bind = f"0.0.0.0:{os.getenv('PORT', '5055')}"

# Allow Render's WEB_CONCURRENCY hint to scale workers, defaulting to 1 locally.
workers = int(os.getenv("WEB_CONCURRENCY", "1"))

