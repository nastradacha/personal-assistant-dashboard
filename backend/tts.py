import os
import hashlib
import subprocess
import shlex
from typing import Optional

from google.cloud import texttospeech


TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "en-US")
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-Standard-C")
TTS_PLAYER_COMMAND = os.getenv("TTS_PLAYER_COMMAND", "aplay")
TTS_CACHE_DIR = os.getenv("TTS_CACHE_DIR", "tts_cache")
TTS_CACHE_MAX_FILES = int(os.getenv("TTS_CACHE_MAX_FILES", "500"))

_tts_client: Optional[texttospeech.TextToSpeechClient] = None


def _get_tts_client() -> texttospeech.TextToSpeechClient:
    global _tts_client
    if _tts_client is None:
        _tts_client = texttospeech.TextToSpeechClient()
    return _tts_client


def _ensure_cache_dir() -> str:
    path = TTS_CACHE_DIR or "tts_cache"
    os.makedirs(path, exist_ok=True)
    return path


def _cache_key(text: str) -> str:
    key_source = f"v1|{TTS_LANGUAGE}|{TTS_VOICE}|{text}"
    return hashlib.sha256(key_source.encode("utf-8")).hexdigest()


def _cache_path_for_text(text: str) -> str:
    cache_dir = _ensure_cache_dir()
    filename = f"{_cache_key(text)}.wav"
    return os.path.join(cache_dir, filename)


def _play_audio_file(path: str) -> None:
    player_cmd_raw = (TTS_PLAYER_COMMAND or "").strip()
    if not player_cmd_raw:
        raise RuntimeError("TTS audio player command is not configured")
    try:
        parts = shlex.split(player_cmd_raw)
        if not parts:
            raise RuntimeError("TTS audio player command is not configured")
        subprocess.Popen(  # noqa: S603,S607
            parts + [path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"TTS playback failed: {exc}") from exc


def _prune_cache_if_needed() -> None:
    try:
        cache_dir = _ensure_cache_dir()
        entries = [
            os.path.join(cache_dir, name)
            for name in os.listdir(cache_dir)
            if name.lower().endswith(".wav")
        ]
        max_files = TTS_CACHE_MAX_FILES if TTS_CACHE_MAX_FILES > 0 else 0
        if max_files <= 0:
            return
        if len(entries) <= max_files:
            return
        entries.sort(key=lambda p: os.path.getmtime(p))
        to_delete = entries[0 : len(entries) - max_files]
        for path in to_delete:
            try:
                os.remove(path)
            except OSError:
                continue
    except Exception:
        # Cache pruning should never break TTS playback.
        return


def play_text(text: Optional[str]) -> None:
    """Play short text via Google Cloud TTS on the Raspberry Pi.

    This is a fire-and-forget helper intended for short coaching prompts.
    It spawns the player command asynchronously and does not wait for completion.
    """

    if not text:
        return
    text = str(text).strip()
    if not text:
        return

    cache_path = _cache_path_for_text(text)
    if os.path.exists(cache_path):
        _play_audio_file(cache_path)
        return

    client = _get_tts_client()

    synthesis_input = texttospeech.SynthesisInput(text=text)
    if TTS_VOICE:
        voice = texttospeech.VoiceSelectionParams(
            language_code=TTS_LANGUAGE,
            name=TTS_VOICE,
        )
    else:
        voice = texttospeech.VoiceSelectionParams(
            language_code=TTS_LANGUAGE,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    audio_content = response.audio_content
    if not audio_content:
        raise RuntimeError("TTS synthesis returned empty audio content")

    cache_dir = _ensure_cache_dir()
    tmp_path = os.path.join(cache_dir, f".tmp_{_cache_key(text)}.wav")
    try:
        with open(tmp_path, "wb") as f:
            f.write(audio_content)
        os.replace(tmp_path, cache_path)
        _play_audio_file(cache_path)
        _prune_cache_if_needed()
    except Exception as exc:  # noqa: BLE001
        # Best effort to clean up temp file on errors.
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        raise RuntimeError(f"TTS playback failed: {exc}") from exc
