import os
import subprocess
from typing import Optional


TTS_COMMAND = os.getenv("TTS_COMMAND", "espeak")


def play_text(text: Optional[str]) -> None:
    """Play short text via a local TTS command on the Raspberry Pi.

    This is a fire-and-forget helper intended for short coaching prompts.
    It spawns the command asynchronously and does not wait for completion.
    """

    if not text:
        return
    text = str(text).strip()
    if not text:
        return

    cmd = (TTS_COMMAND or "").strip()
    if not cmd:
        raise RuntimeError("TTS command is not configured")

    try:
        # Fire-and-forget; suppress stdout/stderr so it doesn't spam logs.
        subprocess.Popen(
            [cmd, text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"TTS playback failed: {exc}") from exc
