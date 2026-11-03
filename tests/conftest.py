import io
import wave

import pytest

from engine import ParadeeEngine


@pytest.fixture(autouse=True)
def _tmp_tokens_file(tmp_path, monkeypatch):
    """Keeps tokens.json and settings.json out of the repo, and a saved setting from leaking into the next test."""
    monkeypatch.setenv("TTSPARADEE_TOKENS_FILE", str(tmp_path / "tokens.json"))


def silence(seconds: float = 0.5, rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\0\0" * int(seconds * rate))
    return buf.getvalue()


class FakeVoices:
    """Stands in for the loaded model: answers half a second of silence and records every call."""

    def __init__(self, version, threads, names):
        self.version, self.threads, self.names, self.calls = version, threads, names, []

    def speak(self, text, voice, speed):
        self.calls.append({"text": text, "voice": voice, "speed": speed})
        return silence(), 0.5


def make_engine(**options):
    """An engine whose loader builds FakeVoices; `engine.loads` lists the thread counts it was asked for."""
    from paradee.tts import VOICES

    loads, made = [], []
    version = options.pop("version", "1.2")

    def loader(ver, threads):
        loads.append(threads)
        model = FakeVoices(ver, threads, list(VOICES[ver]))
        made.append(model)
        return model

    options.setdefault("loader", loader)
    engine = ParadeeEngine(version, **options)
    engine.loads, engine.made = loads, made
    return engine
