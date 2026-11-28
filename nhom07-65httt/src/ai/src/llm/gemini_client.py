"""Gemini client with centrally managed credentials, model selection, and failover."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.llm.key_rotator import GeminiKeyRotator
from src.llm.runtime_config import get_gemini_model

if TYPE_CHECKING:
    from google import genai

logger = logging.getLogger("ai.gemini_client")


def _is_rate_limit_or_quota_error(exc: Exception) -> bool:
    message = str(exc).lower()
    error_type = type(exc).__name__.lower()
    return any(term in message or term in error_type for term in ("429", "resourceexhausted", "quota", "rate limit", "too many requests"))


def _client_for_next_key() -> tuple[genai.Client, str]:
    from google import genai

    key = GeminiKeyRotator.get_instance().get_next_key()
    return genai.Client(api_key=key), key


def _max_attempts() -> int:
    keys = GeminiKeyRotator.get_instance().keys
    return max(1, min(len(keys), 5)) if keys else 1


def generate_content(prompt: str, system_instruction: str | None = None) -> str:
    from google.genai import types

    rotator = GeminiKeyRotator.get_instance()
    last_error = None
    model_id = get_gemini_model()

    for attempt in range(_max_attempts()):
        client, key = _client_for_next_key()
        try:
            config = types.GenerateContentConfig(system_instruction=system_instruction) if system_instruction else None
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config,
            )
            usage = response.usage_metadata
            if usage:
                logger.info(
                    "gemini token_usage prompt=%s output=%s total=%s model=%s",
                    getattr(usage, "prompt_token_count", "?"),
                    getattr(usage, "candidates_token_count", "?"),
                    getattr(usage, "total_token_count", "?"),
                    model_id,
                )
            return response.text or ""
        except Exception as exc:
            last_error = exc
            if _is_rate_limit_or_quota_error(exc):
                rotator.report_rate_limit(key, cooldown_seconds=60.0)
                logger.warning("Gemini key rate-limited on attempt %d/%d; trying next key", attempt + 1, _max_attempts())
                continue
            logger.exception("Gemini generate_content failed")
            raise
        finally:
            client.close()

    if last_error:
        raise last_error
    return ""


def generate_content_stream(prompt: str, system_instruction: str | None = None):
    """Stream text chunks from Gemini using the next centrally managed key."""
    from google.genai import types

    client, key = _client_for_next_key()
    model_id = get_gemini_model()
    config = types.GenerateContentConfig(system_instruction=system_instruction) if system_instruction else None

    try:
        response_stream = client.models.generate_content_stream(
            model=model_id,
            contents=prompt,
            config=config,
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as exc:
        if _is_rate_limit_or_quota_error(exc):
            GeminiKeyRotator.get_instance().report_rate_limit(key, cooldown_seconds=60.0)
        logger.exception("Gemini streaming failed")
        raise
    finally:
        client.close()


def chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    """Execute chat-style messages against the Admin-selected Gemini model."""
    from google.genai import types

    system_parts = [m.get("content", "") for m in messages if m.get("role") == "system" and m.get("content")]
    system_instruction = "\n\n".join(system_parts) if system_parts else None
    dialogue = [m for m in messages if m.get("role") != "system" and m.get("content")]
    if not dialogue:
        return ""

    if len(dialogue) == 1:
        prompt = dialogue[0]["content"]
    else:
        prompt = "\n\n".join(
            f"{'Assistant' if message.get('role') == 'assistant' else 'User'}: {message['content']}"
            for message in dialogue
        )

    rotator = GeminiKeyRotator.get_instance()
    last_error = None
    model_id = get_gemini_model()
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction,
    )

    for attempt in range(_max_attempts()):
        try:
            client, key = _client_for_next_key()
        except RuntimeError as exc:
            logger.warning("No Gemini API key available: %s", exc)
            return ""
        try:
            response = client.models.generate_content(model=model_id, contents=prompt, config=config)
            return response.text or ""
        except Exception as exc:
            last_error = exc
            if _is_rate_limit_or_quota_error(exc):
                rotator.report_rate_limit(key, cooldown_seconds=60.0)
                logger.warning("Gemini rate limit hit on attempt %d/%d; trying next key", attempt + 1, _max_attempts())
                continue
            logger.exception("Gemini chat completion failed")
            return ""
        finally:
            client.close()

    if last_error:
        logger.warning("All configured Gemini keys failed: %s", type(last_error).__name__)
    return ""


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """Transcribe one audio chunk using the centrally managed key and model."""
    from google.genai import types

    rotator = GeminiKeyRotator.get_instance()
    last_error = None
    model_id = get_gemini_model()
    contents = [
        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        "Transcribe this audio accurately in its original language. Return only the transcribed text.",
    ]

    for attempt in range(_max_attempts()):
        client, key = _client_for_next_key()
        try:
            response = client.models.generate_content(model=model_id, contents=contents)
            return (response.text or "").strip()
        except Exception as exc:
            last_error = exc
            if _is_rate_limit_or_quota_error(exc):
                rotator.report_rate_limit(key, cooldown_seconds=60.0)
                logger.warning("Gemini transcription key rate-limited on attempt %d/%d; trying next key", attempt + 1, _max_attempts())
                continue
            logger.exception("Gemini audio transcription failed")
            raise
        finally:
            client.close()

    if last_error:
        raise last_error
    return ""
