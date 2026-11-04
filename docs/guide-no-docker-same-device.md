# TTSParadeeModel: without Docker, on Windows

Run Paradee text to speech on the CPU directly with Python: one process, no load balancer, listening on `127.0.0.1:9160`.

## Requirements
- Windows with Python 3.11 or newer and uv (`winget install astral-sh.uv`).
- Internet on the first start (8.5 MB of model files plus the phonemizer data).
- RAM for the model (one copy).

## Start
Double-click `run.bat`, or run it in a terminal from `TTSParadeeModel\`. It runs `uv sync` to create or update `.venv`, then starts
`python src/app.py`. The first start downloads 8.5 MB of model files plus the phonemizer data.

Linux or macOS:
```bash
cd TTSParadeeModel
uv sync
uv run python src/app.py
```


## Settings
`run.bat` and `app.py` read the real environment, **not** `.env`. Set variables before starting:

| Variable | Default | Effect |
|---|---|---|
| `TTSPARADEE_HOST` | `127.0.0.1` | Bind address. Use `0.0.0.0` only if other devices must reach it. |
| `TTSPARADEE_PORT` | `9160` | Port. |
| `TTSPARADEE_ADMIN_PASSWORD` | empty | Unlocks `/admin/` and requires tokens on every call but `/health`. Empty = no auth. |
| `TTSPARADEE_WARM` | `1` | Load the model at start; with `0` the first request pays the load time. |
| `TTSPARADEE_NUM_THREAD` | the library decides | CPU threads. Set it to the number of **physical** cores. |

PowerShell: `$env:TTSPARADEE_ADMIN_PASSWORD = "secret"; .\run.bat`
Bash: `TTSPARADEE_ADMIN_PASSWORD=secret uv run python src/app.py`

## Check
```bash
curl http://127.0.0.1:9160/health
```
`ready` is `false` until the model has loaded. Then open `http://127.0.0.1:9160/admin/` (see [guide-web-ui.md](guide-web-ui.md)),
make a token, and try a call:
```bash
curl -X POST http://127.0.0.1:9160/v1/speak -H "Content-Type: application/json" -H "X-Internal-Token: ttsparadee_..." -d '{"text":"Hello from the model service."}' -o hello.wav
```

## Stop
Ctrl+C in the terminal. Do not run this and the Docker stack together: both use port 9160.

## Tests
`uv run pytest`.
