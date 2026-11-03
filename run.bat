@echo off
REM Starts the ttsparadee service on port 9160 (syncs .venv with uv on each run). The first start downloads 8.5 MB plus the phonemizer data.
REM LABEL: TTSParadee Service
REM DESCRIPTION: Shared HTTP service that runs Paradee text to speech on the CPU for every project.

cd /d "%~dp0"

python -m uv sync
if errorlevel 1 (
    echo uv sync failed. Install uv: python -m pip install uv
    pause
    exit /b 1
)
call .venv\Scripts\activate

python src/app.py
pause
