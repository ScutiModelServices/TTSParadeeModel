import asyncio

import pytest

from conftest import make_engine
from engine import EngineError, ParadeeEngine, Voices, repo_of


def speak(engine, text="hello", voice=None, speed=1.0):
    return asyncio.run(engine.synthesize(text, voice, speed))


def test_versions_map_to_repositories_and_unknown_ones_are_refused():
    assert repo_of("1.2") == "sahilmahendrakar/Paradee-8M-v1.2"
    with pytest.raises(ValueError):
        ParadeeEngine("9.9")


def test_the_default_voice_is_af_heart_and_the_model_loads_once():
    engine = make_engine()
    assert engine.default_voice == "af_heart" and not engine.ready
    first = speak(engine)
    speak(engine, "again")
    assert first["voice"] == "af_heart" and first["seconds"] == 0.5 and first["wav"][:4] == b"RIFF"
    assert engine.loads == [None] and engine.ready
    assert [call["text"] for call in engine.made[0].calls] == ["hello", "again"]


def test_every_voice_of_the_version_works_and_an_unknown_one_is_404():
    engine = make_engine()
    assert engine.voices == ["af_heart", "bf_isabella", "am_puck", "bm_fable"]
    assert speak(engine, voice="bm_fable")["voice"] == "bm_fable"
    with pytest.raises(EngineError) as error:
        speak(engine, voice="zz_nobody")
    assert error.value.status == 404


def test_older_versions_have_one_voice():
    assert make_engine(version="1.1").voices == ["af_heart"]


def test_speed_reaches_the_model():
    engine = make_engine()
    speak(engine, speed=1.5)
    assert engine.made[0].calls[0]["speed"] == 1.5


def test_changing_the_threads_reloads_with_the_new_count():
    engine = make_engine()
    speak(engine)
    engine.num_thread = 3
    engine.num_thread = 3  # same value: nothing to drop
    speak(engine)
    assert engine.loads == [None, 3]


def test_a_new_download_by_another_replica_drops_the_loaded_model(tmp_path):
    marker = tmp_path / "marker"
    one, two = make_engine(marker=marker), make_engine(marker=marker)
    speak(one)
    asyncio.run(two.unload())
    one.sync()
    assert not one.ready
    speak(one)
    assert len(one.loads) == 2


def test_the_revision_calls_use_the_version():
    engine = make_engine(cached_sha=lambda version: f"cached-{version}", remote_sha=lambda version: f"latest-{version}")
    assert asyncio.run(engine.cached_sha()) == "cached-1.2" and asyncio.run(engine.remote_sha()) == "latest-1.2"


def test_voices_write_a_24khz_wav_from_the_float_audio():
    import numpy

    class Tts:
        voices = ["af_heart"]

        def __call__(self, text, speed, voice):
            return numpy.zeros(12000, dtype="float32")

    wav, seconds = Voices(Tts()).speak("hi", "af_heart", 1.0)
    assert seconds == 0.5 and wav[:4] == b"RIFF"
