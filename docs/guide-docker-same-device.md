# TTSParadeeModel: Docker Desktop on this PC

Run Paradee text to speech on the CPU in Docker Desktop on the machine you work on, so other programs on it can call it.

## Requirements
- Docker Desktop with Compose v2 (Windows: WSL2 backend).
- RAM for the model **per replica**. Keep `TTSPARADEE_REPLICAS=1` on a PC. Docker Desktop on Windows caps its engine at about half of your RAM unless you raise it in `.wslconfig`.
- Internet on the first start (8.5 MB of model files plus the phonemizer data).

## Steps
1. Configure. In `TTSParadeeModel/`:
   ```bash
   cp .env.example .env
   ```
   Set `TTSPARADEE_ADMIN_PASSWORD` (empty = no auth and no admin page, fine for a local test). Leave `TTSPARADEE_PORT=9160`. Leave `TTSPARADEE_REPLICAS=1`.
2. Start:
   ```bash
   docker compose up -d --build
   ```
   The first start downloads 8.5 MB of model files plus the phonemizer data into the `models` volume. `ttsparadee_lb` starts only after the service is healthy
   (up to 300 s grace). Watch with `docker compose ps` and `docker compose logs -f ttsparadee`.
3. Check:
   ```bash
   curl http://127.0.0.1:9160/health
   ```
   `ready` is `false` until the model has loaded, then `true`.
4. Open the admin page: `http://127.0.0.1:9160/admin/` (see [guide-web-ui.md](guide-web-ui.md)) and make a token for each caller.
5. Try a call:
   ```bash
   curl -X POST http://127.0.0.1:9160/v1/speak -H "Content-Type: application/json" -H "X-Internal-Token: ttsparadee_..." -d '{"text":"Hello from the model service."}' -o hello.wav
   ```
   Expect a WAV file, `hello.wav`.
6. Callers connect to the published port. The caller holds the URL and token:
   - Caller on the host: `http://127.0.0.1:9160`.
   - Caller in another Docker stack on the same host: `http://host.docker.internal:9160`.

## Daily use
```bash
docker compose ps          # state
docker compose logs -f ttsparadee
docker compose down        # stop (the weights volume is kept)
docker compose up -d --build && docker compose restart ttsparadee_lb   # after a code change
```

## Problems
| Symptom | Fix |
|---|---|
| `address already in use` on 9160 | Another copy (`run.bat`, or the same stack on another compose project) is running. Stop it or change `TTSPARADEE_PORT`. |
| `/health` shows `ready: false` for minutes | First start: the weights are downloading or loading. Check `docker compose logs -f ttsparadee`. |
| 401 Invalid token | The caller's token is missing or revoked; make one on `/admin/`. |

| Container restarts in a loop | Out of RAM. Raise the Docker Desktop memory limit or lower the replica count. |
