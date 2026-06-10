# EchoEcho

EchoEcho is one FastAPI app with one HTML/CSS/JavaScript frontend and two generation modes:

- Fast API Generation: uses the existing KieAI/Suno API backend.
- Copyright-free MusicGen Generation: uses the local `facebook/musicgen-small` model.

Both modes save audio files in `backend/generated/` and append records to `backend/song_history.json`.

## Final Structure

```text
APIV/EchoEcho/
|-- backend/
|   |-- __init__.py
|   |-- main.py
|   |-- api_generator.py
|   |-- music_generator.py
|   |-- generated/
|   |-- static/
|   |-- song_history.json
|   `-- kiai_callbacks.json
|-- frontend/
|   |-- index.html
|   |-- script.js
|   `-- styles.css
|-- tests/
|-- .env
|-- README.md
`-- requirements.txt
```

## Setup

```powershell
cd APIV\EchoEcho
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the merged app:

```powershell
python -m backend.main
```

Open:

```text
http://127.0.0.1:8000
```

The backend serves `frontend/index.html`, `frontend/styles.css`, `frontend/script.js`, static files, and generated audio files.

## Environment

Store local environment values in `.env`.

```env
SERPAPI_API_KEY=your_serpapi_key_here
GROQ_API_KEY=your_groq_key_here
KIEAI_API_KEY=your_key_here
PUBLIC_BASE_URL=https://your-public-domain-or-ngrok-url
KIEAI_CALLBACK_PATH=/api/kieai/callback
TRIM_DURATION_SECONDS=30
```

`SERPAPI_API_KEY` powers copyright search and `GROQ_API_KEY` powers lyrics and copyright LLM analysis.
`KIEAI_API_KEY` is required for Fast API Generation. `PUBLIC_BASE_URL` must be publicly reachable because KieAI posts callback events to it. For local development, expose port 8000 with a tunnel such as ngrok and put the HTTPS forwarding URL in `PUBLIC_BASE_URL`.

MusicGen mode does not need API keys, but it downloads and loads `facebook/musicgen-small` and needs enough CPU/GPU memory for local generation.

## API

Unified generation endpoint:

```http
POST /generate
```

```json
{
  "prompt": "lofi relaxing beat",
  "mode": "api",
  "duration": 15,
  "fast": true
}
```

Use `mode: "api"` for Fast API Generation. Use `mode: "musicgen"` for local MusicGen. If `mode` is missing, the backend defaults to `"musicgen"`. Unknown modes return a clear `400` error.

Successful response:

```json
{
  "success": true,
  "mode": "api",
  "audio_url": "/generated/ECHO_ABCD_original.mp3",
  "filename": "ECHO_ABCD_original.mp3"
}
```

Compatibility endpoints are still available, including `/history`, `/songs`, `/generation-status`, `/audio/{song_id}.wav`, `/download/{code}/original`, `/api/library/{code}/trim`, and KieAI callback routes.

## Tests

```powershell
pytest -q
```
