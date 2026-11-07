# TTS_Paradee_Model: Docker Desktop on this PC

Run Paradee text to speech on the CPU in Docker Desktop on the machine you work on, so other programs on it can call it.

## Requirements

- Docker Desktop with Compose v2 (Windows: WSL2 backend).
- RAM per replica: about 650 MB (measured on Windows; each replica loads its own copy). Keep `TTSPARADEE_REPLICAS=1` on a PC. Docker Desktop on Windows caps its engine at about half of your RAM unless you raise it in `.wslconfig`.
- Network access on the first start to download the files (8.5 MB plus the phonemizer data) from Hugging Face.
- CPU only, no GPU needed.

## Steps

1. Configure. In `TTS_Paradee_Model/`:
   ```bash
   cp .env.example .env
   ```
   Set `TTSPARADEE_ADMIN_PASSWORD` (empty = no auth and no admin page, fine for a local test). Leave `TTSPARADEE_PORT=29321`. Leave `TTSPARADEE_REPLICAS=1`.
2. Start:
   ```bash
   docker compose up -d --build
   ```
   The first start downloads 8.5 MB of model files plus the phonemizer data into the `tts_paradee_model_models` volume. `tts_paradee_model_lb` starts only after the service is healthy
   (up to 300 s grace). Watch with `docker compose ps` and `docker compose logs -f tts_paradee_model`.
3. Check:
   ```bash
   curl http://127.0.0.1:29321/health
   ```
   `ready` is `false` until the model has loaded, then `true`.
4. Open the admin page: `http://127.0.0.1:29321/admin/` (see [guide-web-ui.md](guide-web-ui.md)) and make a token for each caller.
5. Try a call:
   ```bash
   curl -X POST http://127.0.0.1:29321/v1/speak -H "Content-Type: application/json" -H "X-Internal-Token: ttsparadee_..." -d '{"text":"Hello from the model service."}' -o hello.wav
   ```
   Expect a WAV file, `hello.wav`.
6. Callers connect to the published port. The caller holds the URL and token:
   - Caller on the host: `http://127.0.0.1:29321`.
   - Caller in another Docker stack on the same host: `http://host.docker.internal:29321`.

## Settings

In `.env` next to `docker-compose.yml`:

| Variable | Default | Effect |
|---|---|---|
| `TTSPARADEE_REPLICAS` | `1` | Number of `tts_paradee_model` containers. Read by Compose. |
| `TTSPARADEE_PORT` | `29321` | Host port `tts_paradee_model_lb` publishes. |
| `TTSPARADEE_ADMIN_PASSWORD` | empty | Password for `/admin/`. When set, every call except `/health` must send a token as `X-Internal-Token`. Empty = no auth. |
| `TTSPARADEE_NUM_THREAD` | onnxruntime decides | Starting value for the CPU threads card; a value saved on `/admin/` wins. Use the number of physical cores (`lscpu`: cores x sockets), not logical CPUs; more threads than cores slows every call. |

On the **Settings** card of `/admin/` (saved in `settings.json` beside the tokens, shared by all replicas; a saved
value beats the environment variable named in brackets): update check hours (`TTSPARADEE_UPDATE_CHECK_HOURS`, 6),
in-flight cap (`TTSPARADEE_MAX_INFLIGHT`, 0 = 4), answers kept per replica (`TTSPARADEE_CACHE_SIZE`, 64, 0 = off; at most 1 MB each), Paradee version (`TTSPARADEE_VERSION`, restart; `1.2` has four voices, `1.1` and `1.0` only `af_heart`) and load at start (`TTSPARADEE_WARM`, restart). Compose does not pass these;
add the variable under `environment:` of `tts_paradee_model` to use one as a starting value.

## Daily use

```bash
docker compose ps          # state
docker compose logs -f tts_paradee_model
docker compose down        # stop (the weights volume is kept)
docker compose up -d --build && docker compose restart tts_paradee_model_lb   # after a code change
```

## Time it

Try it and time it:

```bash
python tools/bench.py http://127.0.0.1:29321 --save out
```

## Problems

| Symptom | Fix |
|---|---|
| `address already in use` on 29321 | Another copy (`run.bat`, or the same stack on another compose project) is running. Stop it or change `TTSPARADEE_PORT`. |
| `/health` shows `ready: false` for minutes | First start: the weights are downloading or loading. Check `docker compose logs -f tts_paradee_model`. |
| 401 Invalid token | The caller's token is missing or revoked; make one on `/admin/`. |
| Container restarts in a loop | Out of RAM. Raise the Docker Desktop memory limit or lower the replica count. |
| `tts_paradee_model_lb` never starts | No replica is healthy yet (first download, or out of memory). `docker compose logs tts_paradee_model`. |
| Replicas restart in a loop | Out of RAM. Lower `TTSPARADEE_REPLICAS`. |
| 403 "may not use voice" | The token's list on `/admin/` does not include that voice (or the default voice, when `voice` is left out). |
| 404 on `/v1/speak` | The voice is not served here. `GET /v1/voices` lists them. |
| 422 on `format` or another field | Only `text`, `voice` and `speed` exist; the reply is always WAV. |
| 429 | Over the token's rate limit, or too many calls waiting for the model. |
| nginx 502 after scaling | `tts_paradee_model_lb` not restarted after the replica count changed. |

The load balancer also joins external `citadel_core` as `tts_paradee_model_lb`. Start the Citadel stack first so that network exists; tool services on it use `http://tts_paradee_model_lb:29321`. Docker project and API image are `tts_paradee_model` and `tts_paradee_model:latest`; persistent volumes have explicit `tts_paradee_model_*` names. Volume migration and rollback instructions are in [CHANGELOG.md](../CHANGELOG.md).
