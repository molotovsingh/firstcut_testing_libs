# tests/conftest.py
import os
from pathlib import Path

from dotenv import load_dotenv


def _ensure_gemini_key() -> None:
    """
    Load .env and mirror GOOGLE_API_KEY into GEMINI_API_KEY when needed.
    Keeps tests working whether the key was saved as Google or Gemini.
    """
    # Load .env only once; quiet=True suppresses noise if file missing
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

    if "GEMINI_API_KEY" in os.environ:
        return

    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        os.environ["GEMINI_API_KEY"] = google_key


_ensure_gemini_key()