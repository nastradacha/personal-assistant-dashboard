import os
import shlex
import subprocess
import tempfile
from typing import Optional

from google.cloud import texttospeech


TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "en-US")
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-Standard-C")
TTS_PLAYER_COMMAND = os.getenv("TTS_PLAYER_COMMAND", "aplay")

_tts_client: Optional[texttospeech.TextToSpeechClient] = None


def _get_tts_client() -> texttospeech.TextToSpeechClient:
    global _tts_client
    if _tts_client is None:
        _tts_client = texttospeech.TextToSpeechClient()
    return _tts_client


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

    player_cmd = (TTS_PLAYER_COMMAND or "").strip()
    if not player_cmd:
        raise RuntimeError("TTS audio player command is not configured")

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
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    audio_content = response.audio_content
    if not audio_content:
        raise RuntimeError("TTS synthesis returned empty audio content")

    fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(audio_content)

        # Use a small shell wrapper so we can delete the temp file after playback
        quoted_cmd = player_cmd
        quoted_path = shlex.quote(tmp_path)
        shell_cmd = f"{quoted_cmd} {quoted_path} >/dev/null 2>&1; rm -f {quoted_path}"

        subprocess.Popen(  # noqa: S603,S607
            ["/bin/sh", "-c", shell_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"TTS playback failed: {exc}") from exc
