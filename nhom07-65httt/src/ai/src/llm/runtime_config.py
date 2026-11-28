"""Runtime AI settings synchronized from the Admin database."""

from threading import RLock

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"

_lock = RLock()
_gemini_model = DEFAULT_GEMINI_MODEL


def get_gemini_model() -> str:
    with _lock:
        return _gemini_model


def set_gemini_model(model_id: str) -> None:
    model_id = model_id.strip()
    if not model_id.startswith("gemini-") or len(model_id) > 100:
        raise ValueError("Invalid Gemini model id")
    with _lock:
        global _gemini_model
        _gemini_model = model_id
