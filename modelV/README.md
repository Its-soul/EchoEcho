# EchoEcho

EchoEcho is a FastAPI, MusicGen, HTML, CSS, and JavaScript app for saving musical inspiration sketches as a persistent notebook. Every generated idea receives a four-letter song ID, a permanent WAV file, and a history entry that remains available after refresh.

## Project Structure

```text
project/
|-- frontend/
|   |-- index.html
|   |-- styles.css
|   `-- script.js
|-- backend/
|   |-- main.py
|   |-- music_generator.py
|   |-- requirements.txt
|   |-- song_history.json
|   |-- static/
|   |   `-- favicon.ico
|   `-- generated/
`-- README.md
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

Open:

```text
http://localhost:8000
```

The backend loads `facebook/musicgen-small` once during startup and keeps the model cached in memory. Generation requests reuse that model instead of reloading it.

## Frontend

The FastAPI server serves the EchoEcho page at `/`. The page calls the backend asynchronously, prevents form reloads, and updates the existing audio element with the returned song URL:

```javascript
audioPlayer.src = audioURL + "?t=" + Date.now();
audioPlayer.load();
```

## API

### POST `/generate`

Requires `/health` to return `{"status": "ready"}`.

Request body:

```json
{
  "moods": ["Romantic", "Nostalgic"],
  "genres": ["Lo-fi"],
  "themes": ["Love", "Memories"],
  "instruments": ["Flute"],
  "tempo": 109,
  "complexity": "Moderate",
  "energy": 4,
  "custom_prompt": ""
}
```

Response:

```json
{
  "song_id": "FJDK",
  "audio_url": "/audio/FJDK.wav",
  "prompt_used": "30-second instrumental inspiration sketch...",
  "generation_time_seconds": 84,
  "generation_time": "1m 24s",
  "output_file": "generated/FJDK.wav",
  "download_filename": "FJDK.wav"
}
```

### GET `/audio/{song_id}.wav`

Serves a specific saved song, such as:

```text
/audio/FJDK.wav
```

### GET `/songs`

Returns saved song records from `backend/song_history.json`, newest first.

### GET `/generation-status`

Returns progress data while a generation is running:

```json
{
  "stage": "Composing melody",
  "progress": 65,
  "elapsed_seconds": 52,
  "estimated_remaining_seconds": 38
}
```

### GET `/health`

Returns the model readiness state:

```json
{"status": "loading"}
```

or:

```json
{"status": "ready"}
```

## Persistence

EchoEcho never overwrites previous songs. Each generation creates:

```text
backend/generated/FJDK.wav
```

and appends a registry record to:

```text
backend/song_history.json
```

The Song Library page reads this registry and displays song IDs, dates, moods, themes, instruments, prompts, generation times, audio players, download buttons, and copy buttons.
