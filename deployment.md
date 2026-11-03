# Deploying TTSParadeeModel

TTSParadeeModel is one HTTP service (port 9160). It runs as `ttsparadee` replicas behind an nginx load balancer,
`ttsparadee_lb`. Callers use `http://<host>:9160`; they never reach a replica directly.

## Requirements

- Docker with Compose v2.
- RAM per replica: about 650 MB (measured on Windows; each replica loads its own copy).
- Network access on the first start to download the files (8.5 MB plus the phonemizer data) from Hugging Face.
- CPU only, no GPU needed.

## Settings

In `.env` next to `docker-compose.yml`:

| Variable | Default | Effect |
|---|---|---|
| `TTSPARADEE_REPLICAS` | `1` | Number of `ttsparadee` containers. Read by Compose. |
| `TTSPARADEE_PORT` | `9160` | Host port `ttsparadee_lb` publishes. |
| `TTSPARADEE_ADMIN_PASSWORD` | empty | Password for `/admin/`. When set, every call except `/health` must send a token as `X-Internal-Token`. Empty = no auth. |
| `TTSPARADEE_NUM_THREAD` | onnxruntime decides | Starting value for the CPU threads card; a value saved on `/admin/` wins. |

On the **Settings** card of `/admin/` (saved in `settings.json` beside the tokens, shared by all replicas; a saved
value beats the environment variable named in brackets): update check hours (`TTSPARADEE_UPDATE_CHECK_HOURS`, 6),
in-flight cap (`TTSPARADEE_MAX_INFLIGHT`, 0 = 4), answers kept per replica (`TTSPARADEE_CACHE_SIZE`, 64, 0 = off; at most 1 MB each), Paradee version (`TTSPARADEE_VERSION`, restart; `1.2` has four voices, `1.1` and `1.0` only `af_heart`) and load at start (`TTSPARADEE_WARM`, restart). Compose does not pass these;
add the variable under `environment:` of `ttsparadee` to use one as a starting value.

## Start

```bash
docker compose up -d --build
curl http://127.0.0.1:9160/health
```

Expect `"ready": true` once a replica has loaded the model. The first start downloads the files into the `models`
volume, so `ttsparadee_lb` can take a minute to appear (the health check allows 300 s before failures count; run
`docker compose ps` and wait).

Try it and time it:

```bash
python tools/bench.py http://127.0.0.1:9160 --save out
```

## Scaling

```bash
TTSPARADEE_REPLICAS=3 docker compose up -d --build
docker compose restart ttsparadee_lb
```

The restart is needed because nginx resolves replica addresses once at start.

## Updating the files

The **Updates** card compares the downloaded revision of the Hugging Face repository with its newest one. **Download
new weights** fetches them into the models volume; every replica drops its old copy within a few seconds and loads the
new one on its next request. Updating the service itself: `docker compose up -d --build`, then
`docker compose restart ttsparadee_lb`.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `ttsparadee_lb` never starts | No replica is healthy yet (first download, or out of memory). `docker compose logs ttsparadee`. |
| Replicas restart in a loop | Out of RAM. Lower `TTSPARADEE_REPLICAS`. |
| 401 "Invalid token" | The caller sends no token, or a revoked one. |
| 403 "may not use voice" | The token's list on `/admin/` does not include that voice (or the default voice, when `voice` is left out). |
| 404 on `/v1/speak` | The voice is not served here. `GET /v1/voices` lists them. |
| 422 on `format` or another field | Only `text`, `voice` and `speed` exist; the reply is always WAV. |
| 429 | Over the token's rate limit, or too many calls waiting for the model. |
| nginx 502 after scaling | `ttsparadee_lb` not restarted after the replica count changed. |

## Releasing

A plain publish (`tools\deploy.bat` option 1) only updates the `live` branch. For a release set `VERSION` (and
`pyproject.toml` to the same number), commit, then run `tools\deploy.bat` option R or
`py tools\publish_live.py --release`. `tools\make_zip.bat` then builds `zip_versions\TTSParadeeModel-<VERSION>.zip`.
