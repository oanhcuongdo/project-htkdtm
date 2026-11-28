"""Audio/video preprocessing and transcription requests for the AI service."""

import base64
import logging
import os
import struct
import subprocess
import tempfile

import httpx

from src.core.config import settings

logger = logging.getLogger("worker.transcription")

_MAX_CHUNK_BYTES = 18 * 1024 * 1024  # 18 MB safe inline audio limit for Gemini


def _extract_audio_to_wav(input_bytes: bytes, ext: str) -> bytes:
    """Extract and convert audio from media file to mono 16kHz WAV using ffmpeg."""
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as inp:
        inp.write(input_bytes)
        inp_path = inp.name

    out_path = inp_path + ".wav"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", inp_path,
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-acodec", "pcm_s16le",
                out_path,
            ],
            check=True,
            capture_output=True,
            timeout=300,
        )
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(inp_path)
        if os.path.exists(out_path):
            os.unlink(out_path)


def _split_wav(wav_bytes: bytes) -> list[bytes]:
    """Split WAV into chunks of at most _MAX_CHUNK_BYTES, rebuilding headers per chunk."""
    if len(wav_bytes) <= _MAX_CHUNK_BYTES:
        return [wav_bytes]

    header = wav_bytes[:44]
    audio_data = wav_bytes[44:]
    chunk_data_size = _MAX_CHUNK_BYTES - 44

    num_channels = struct.unpack_from("<H", header, 22)[0]
    sample_rate = struct.unpack_from("<I", header, 24)[0]
    bits_per_sample = struct.unpack_from("<H", header, 34)[0]
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8

    chunks = []
    offset = 0
    while offset < len(audio_data):
        part = audio_data[offset: offset + chunk_data_size]
        data_size = len(part)
        riff_size = 36 + data_size
        chunk_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", riff_size, b"WAVE",
            b"fmt ", 16,
            1,
            num_channels, sample_rate, byte_rate, block_align, bits_per_sample,
            b"data", data_size,
        )
        chunks.append(chunk_header + part)
        offset += chunk_data_size

    return chunks


def transcribe_media(file_bytes: bytes, ext: str, file_name: str = "") -> list[dict]:
    """
    Transcribe audio/video through the centrally managed AI service.

    Returns list of {page_number: int, text: str} dicts.
    page_number = segment index, used as citation reference.
    Falls back to placeholder text on error (never returns empty list).
    """
    try:
        logger.info("Transcribing %s (%d bytes)", file_name or ext, len(file_bytes))
        wav_bytes = _extract_audio_to_wav(file_bytes, ext)
        logger.info("Extracted WAV: %d bytes", len(wav_bytes))

        audio_chunks = _split_wav(wav_bytes)
        logger.info("Split into %d chunk(s)", len(audio_chunks))

        pages = []
        headers = {"X-Internal-API-Key": settings.INTERNAL_API_KEY}
        ai_url = f"{settings.AI_SERVICE_URL.rstrip('/')}/internal/transcribe"

        for idx, chunk in enumerate(audio_chunks):
            page_number = idx + 1
            try:
                response = httpx.post(
                    ai_url,
                    headers=headers,
                    json={
                        "mime_type": "audio/wav",
                        "audio_base64": base64.b64encode(chunk).decode("ascii"),
                    },
                    timeout=httpx.Timeout(180.0, connect=15.0),
                )
                response.raise_for_status()
                text = response.json().get("text", "")
                if text and text.strip():
                    pages.append({"page_number": page_number, "text": text.strip()})
                    logger.info("Chunk %d/%d: %d chars", page_number, len(audio_chunks), len(text))
                else:
                    logger.warning("Chunk %d/%d: empty transcription", page_number, len(audio_chunks))
            except Exception as e:
                logger.error("Chunk %d transcription error: %s", page_number, e)
                pages.append({
                    "page_number": page_number,
                    "text": f"[Transcription unavailable for segment {page_number}]",
                })

        if not pages:
            return [{"page_number": 1, "text": f"[Audio content — transcription unavailable for {file_name}]"}]

        return pages

    except Exception as e:
        logger.error("transcribe_media failed: %s", e)
        return [{"page_number": 1, "text": f"[Transcription error for {file_name}: {e}]"}]
