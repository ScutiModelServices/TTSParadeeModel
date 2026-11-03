# TTSParadeeModel

Paradee text to speech, an 8M-parameter model distilled from Kokoro-82M (Apache 2.0), served over HTTP so projects send text instead of loading a model themselves. It has the same admin page,
tokens, rate limits, metrics, settings and update checks as `LayaModel`, `MiniCPM52BModel` and `BitNet2BModel`.
`TTSPiperModel` is the same service with the other engine, so the two can be compared on the same sentences
(`tools/bench.py`).

The engine runs in this process on the CPU with onnxruntime. No GPU, no Ollama.

## API

| Call | Purpose |
|---|---|
| `POST /v1/speak` | `{"text", "voice", "speed"}` returns a WAV file (`audio/wav`, 16-bit mono). Headers: `X-Audio-Seconds`, `X-Duration-Ms`, `X-Voice`. |
| `GET /v1/voices` | `{"voices", "default"}`; with a token limited to voices, only those. |
| `GET /health` | `{"status": "ok", "model", "ready", "num_thread", "voices"}`; `ready` is true once the model is loaded. No token needed. |

`text` is 1 to 5000 characters; `speed` 0.5 to 2 (default 1; above 1 is faster). Speed is passed to the model's `speed` input. Other fields are refused
with 422, so a caller asking for `mp3` finds out instead of getting WAV silently.

**Voices.** Version 1.2 speaks `af_heart` (default), `bf_isabella`, `am_puck` and `bm_fable` from one 8.5 MB file; the
British voices use British phonemes. Versions 1.1 and 1.0 (the *Paradee version* setting) speak `af_heart` only.

A token's *projects* list on the admin page limits the voices it may use (the page calls them projects; here they
are voice names). A token without a list may use every served voice.

## Admin page

`/admin/` (password `TTSPARADEE_ADMIN_PASSWORD`): tokens with voice scope, rate limit and expiry, usage numbers, CPU
threads, the Settings card (update check hours, in-flight cap, Paradee version, load at start), and the Updates card (**Check now** and **Download new weights**).
New files are downloaded once into the shared models volume; the other replicas notice within a few seconds and
load them on their next request. `/metrics` (admin password) is Prometheus text per token.

## Run

```bash
docker compose up -d --build        # http://<host>:9160
python tools/bench.py http://127.0.0.1:9160 --save out
```

Without Docker: `run.bat` (uv, listens on `127.0.0.1:9160`). The first start downloads 8.5 MB plus the phonemizer data. Memory:
about 650 MB per replica, measured with both phonemizers loaded, so `TTSPARADEE_REPLICAS` multiplies it. See `deployment.md`.

## Tests

```bash
uv sync
uv run pytest
```

## Limits worth knowing

- One generation at a time per replica; extra calls wait, and more than the in-flight cap get 429.
- The rate limit is per replica.
- Output is WAV only (no ffmpeg in the image). Convert on the caller's side for MP3.
- There is no streaming: the whole clip is generated, then sent.
- The update check follows the release tag the `paradee` package pins (`v1.2`), so it reports a change only when the author moves that tag.
