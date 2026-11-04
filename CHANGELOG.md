# Changelog

## Unreleased

- `run.bat`: runs `uv sync` directly; `python -m uv` failed when uv was installed only as a program (winget).
- Docker: `.dockerignore` keeps `.git`, `.venv`, tests and local state out of the build context (the same file in every model service).
- Docs: set CPU threads to the number of physical cores, not logical CPUs.
- `/metrics` also returns `ttsparadee_request_seconds`, a histogram of how long `/v1` calls took on that replica.

- Answer cache: the last answers for the same text, voice and speed are sent again without speaking (`TTSPARADEE_CACHE_SIZE`, default 64, 0 = off; `X-Cache` header).
- `POST /v1/speak` accepts `"stream": true`: the WAV is sent sentence by sentence, so the first audio arrives sooner.
- `tools/bench.py` varies the speed per run (to skip the cache) and has `--stream`.
- First version: Paradee text to speech, an 8M-parameter model distilled from Kokoro-82M (Apache 2.0) served on the CPU, with the admin page, tokens (scope, rate limit, expiry), metrics,
  Settings card, update checks and file downloads shared with the other model services.
- `POST /v1/speak` takes `text`, `voice` and `speed` and returns a WAV file. `GET /v1/voices` lists the voices.
- `tools/bench.py` times a service so `TTSPiperModel` and `TTSParadeeModel` can be compared.
