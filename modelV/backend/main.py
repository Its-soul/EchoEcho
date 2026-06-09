import json
import logging
import secrets
import string
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock, Thread
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from music_generator import GENERATED_DIR, TARGET_SECONDS, build_prompt, generate_music, load_model


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("echoecho.api")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
STATIC_DIR = Path(__file__).resolve().parent / "static"
HISTORY_PATH = Path(__file__).resolve().parent / "song_history.json"
DEFAULT_GENERATION_ESTIMATE_SECONDS = 120
ROTATING_STATUS_MESSAGES = [
    "Analyzing mood",
    "Composing melody",
    "Creating atmosphere",
    "Writing musical ideas",
    "Adding emotional texture",
    "Finalizing audio",
]

# Global model state
model = None
processor = None
model_status = "loading"
model_error = ""

model_lock = Lock()
generation_lock = Lock()
generation_status = {
    "stage": "Idle",
    "progress": 0,
    "started_at": None,
    "elapsed_seconds": 0,
    "estimated_remaining_seconds": 0,
    "active": False,
    "estimated_total_seconds": DEFAULT_GENERATION_ESTIMATE_SECONDS,
}


class GenerateRequest(BaseModel):
    moods: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    instruments: list[str] = Field(default_factory=list)
    tempo: int = Field(default=90, ge=60, le=160)
    complexity: Literal["Simple", "Moderate", "Rich"] = "Moderate"
    energy: int = Field(default=4, ge=1, le=10)
    custom_prompt: str = ""


def update_generation_status(stage: str, progress: int) -> None:
    progress = max(0, min(progress, 100))

    with generation_lock:
        started_at = generation_status.get("started_at")
        if started_at is None:
            started_at = time.perf_counter()
            generation_status["started_at"] = started_at

        elapsed = int(time.perf_counter() - started_at) if started_at else 0
        estimated_total = generation_status.get("estimated_total_seconds") or DEFAULT_GENERATION_ESTIMATE_SECONDS
        estimated_remaining = 0
        if progress < 100:
            estimated_remaining = max(1, int(estimated_total - elapsed))

        generation_status.update(
            {
                "stage": stage,
                "progress": progress,
                "elapsed_seconds": elapsed,
                "estimated_remaining_seconds": estimated_remaining,
                "active": progress < 100 and stage != "Failed",
            }
        )


def reset_generation_status() -> None:
    with generation_lock:
        generation_status.update(
            {
                "stage": "Idle",
                "progress": 0,
                "started_at": time.perf_counter(),
                "elapsed_seconds": 0,
                "estimated_remaining_seconds": DEFAULT_GENERATION_ESTIMATE_SECONDS,
                "active": True,
                "estimated_total_seconds": get_generation_estimate_seconds(),
            }
        )


def read_song_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []

    try:
        with HISTORY_PATH.open("r", encoding="utf-8") as history_file:
            data = json.load(history_file)
    except json.JSONDecodeError as error:
        logger.exception("Song history is not valid JSON")
        raise RuntimeError("Song history is not valid JSON.") from error

    if isinstance(data, list):
        return data
    return []


def write_song_history(history: list[dict]) -> None:
    HISTORY_PATH.write_text(
        json.dumps(history, indent=2),
        encoding="utf-8",
    )


def append_song_record(record: dict) -> None:
    history = read_song_history()
    history.append(record)
    write_song_history(history)


def get_generation_estimate_seconds() -> int:
    history = read_song_history()
    recent_times = [
        int(record["generation_time_seconds"])
        for record in history[-5:]
        if isinstance(record.get("generation_time_seconds"), (int, float))
        and record.get("generation_time_seconds", 0) > 0
    ]
    if recent_times:
        return max(60, int(sum(recent_times) / len(recent_times)))
    return DEFAULT_GENERATION_ESTIMATE_SECONDS


def create_song_id() -> str:
    existing_ids = {record.get("song_id") for record in read_song_history()}
    alphabet = string.ascii_uppercase

    for _ in range(1000):
        song_id = "".join(secrets.choice(alphabet) for _ in range(4))
        output_path = GENERATED_DIR / f"{song_id}.wav"
        if song_id not in existing_ids and not output_path.exists():
            return song_id

    raise RuntimeError("Could not create a unique song ID.")


def format_seconds(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    minutes = total_seconds // 60
    remainder = total_seconds % 60
    if minutes:
        return f"{minutes}m {remainder:02d}s"
    return f"{remainder}s"


def warm_model() -> None:
    """
    Load MusicGen once in the background immediately after startup.
    """

    global model
    global processor
    global model_status
    global model_error

    logger.info("Loading MusicGen model...")

    try:
        loaded_model, loaded_processor = load_model()

        with model_lock:
            model = loaded_model
            processor = loaded_processor
            model_status = "ready"
            model_error = ""

        logger.info("MusicGen loaded once and cached in memory.")

    except Exception as error:
        logger.exception("Model warmup failed")

        with model_lock:
            model = None
            processor = None
            model_status = "error"
            model_error = str(error)


app = FastAPI(
    title="EchoEcho API",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """
    Start loading MusicGen immediately after FastAPI launches.
    """

    logger.info("Starting MusicGen warmup thread")

    Thread(
        target=warm_model,
        daemon=True
    ).start()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ----------------------------
# Frontend
# ----------------------------

@app.get("/")
def serve_frontend():
    index_path = FRONTEND_DIR / "index.html"

    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend index.html not found."
        )

    return FileResponse(index_path)


@app.get("/styles.css")
def serve_styles():
    return FileResponse(
        FRONTEND_DIR / "styles.css",
        media_type="text/css"
    )


@app.get("/script.js")
def serve_script():
    return FileResponse(
        FRONTEND_DIR / "script.js",
        media_type="application/javascript"
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(STATIC_DIR / "favicon.ico")


# ----------------------------
# Status
# ----------------------------

@app.get("/health")
def health():
    with model_lock:
        return {
            "status": model_status
        }


@app.get("/status")
def status():
    with model_lock:
        return {
            "status": model_status,
            "model_loaded": model is not None,
            "processor_loaded": processor is not None,
            "error": model_error
        }


@app.get("/generation-status")
def get_generation_status():
    with generation_lock:
        status_snapshot = dict(generation_status)
        started_at = status_snapshot.get("started_at")

    if status_snapshot.get("active") and started_at:
        elapsed = int(time.perf_counter() - started_at)
        progress = int(status_snapshot.get("progress", 0))
        estimated_total = int(
            status_snapshot.get("estimated_total_seconds")
            or DEFAULT_GENERATION_ESTIMATE_SECONDS
        )

        if 20 <= progress < 85:
            generation_window = max(1, estimated_total - 20)
            generated_progress = 20 + int(min(65, (elapsed / generation_window) * 65))
            progress = max(progress, min(generated_progress, 84))
            message_index = elapsed % len(ROTATING_STATUS_MESSAGES)
            status_snapshot["stage"] = ROTATING_STATUS_MESSAGES[message_index]

        status_snapshot["progress"] = progress
        status_snapshot["elapsed_seconds"] = elapsed
        status_snapshot["estimated_remaining_seconds"] = max(
            1,
            estimated_total - elapsed,
        )

    status_snapshot.pop("started_at", None)
    return status_snapshot


@app.get("/songs")
def get_songs():
    try:
        return {
            "songs": list(reversed(read_song_history()))
        }
    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error


# ----------------------------
# Generate
# ----------------------------

@app.post("/generate")
def generate(request: GenerateRequest):
    total_start = time.perf_counter()
    reset_generation_status()
    update_generation_status("Preparing prompt", 0)
    try:
        song_id = create_song_id()
        output_path = GENERATED_DIR / f"{song_id}.wav"
        logger.info("Song ID assigned: %s", song_id)
    except Exception as error:
        logger.exception("Song ID assignment failed")
        update_generation_status("Failed", 100)
        raise HTTPException(
            status_code=500,
            detail=f"Song ID assignment failed: {error}"
        ) from error

    with model_lock:
        ready_model = model
        ready_processor = processor
        current_status = model_status

    if (
        current_status != "ready"
        or ready_model is None
        or ready_processor is None
    ):
        update_generation_status("Failed", 100)
        raise HTTPException(
            status_code=503,
            detail="MusicGen is still loading."
        )

    try:
        prompt_start = time.perf_counter()
        prompt = build_prompt(
            moods=request.moods,
            genres=request.genres,
            themes=request.themes,
            instruments=request.instruments,
            tempo=request.tempo,
            complexity=request.complexity,
            energy=request.energy,
            custom_prompt=request.custom_prompt,
        )
        logger.info("Prompt built: %s", prompt)
        logger.info("Prompt generation took %.2f seconds", time.perf_counter() - prompt_start)
    except Exception as error:
        logger.exception("Prompt creation failed")
        update_generation_status("Failed", 100)
        raise HTTPException(
            status_code=500,
            detail=f"Prompt creation failed: {error}"
        ) from error

    try:
        generation_result = generate_music(
            ready_model,
            ready_processor,
            prompt,
            output_path,
            progress_callback=update_generation_status,
        )

    except RuntimeError as error:

        logger.exception("Generation failed")
        update_generation_status("Failed", 100)

        if "out of memory" in str(error).lower():
            raise HTTPException(
                status_code=500,
                detail="MusicGen ran out of memory."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Music generation failed: {error}"
        )

    except Exception as error:

        logger.exception("Unexpected error")
        update_generation_status("Failed", 100)

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected generation error: {error}"
        )

    total_seconds = time.perf_counter() - total_start
    record = {
        "song_id": song_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "mood": " + ".join(request.moods),
        "theme": " + ".join(request.themes),
        "instruments": request.instruments,
        "tempo": request.tempo,
        "duration": TARGET_SECONDS,
        "energy": request.energy,
        "generation_time_seconds": round(total_seconds),
        "generation_time": format_seconds(total_seconds),
        "output_file": f"generated/{song_id}.wav",
        "audio_url": f"/audio/{song_id}.wav",
    }
    try:
        append_song_record(record)
    except Exception as error:
        logger.exception("Song history append failed")
        update_generation_status("Failed", 100)
        raise HTTPException(
            status_code=500,
            detail=f"Song history append failed: {error}"
        ) from error
    update_generation_status("Completed", 100)
    audio_url = record["audio_url"]

    logger.info("Generation completed in %.2f seconds", total_seconds)
    logger.info("Song ID: %s", song_id)
    logger.info("Saved: %s", generation_result["output_path"])
    logger.info("Response returned in %.2f seconds", time.perf_counter() - total_start)
    logger.info("Audio URL sent to frontend: %s", audio_url)

    return {
        "song_id": song_id,
        "audio_url": audio_url,
        "prompt_used": prompt,
        "generation_time_seconds": record["generation_time_seconds"],
        "generation_time": record["generation_time"],
        "output_file": record["output_file"],
        "download_filename": f"{song_id}.wav",
        "record": record,
    }


@app.get("/audio/{song_id}.wav")
def get_audio(song_id: str):
    cleaned_song_id = song_id.strip().upper()
    if len(cleaned_song_id) != 4 or not cleaned_song_id.isalpha():
        raise HTTPException(
            status_code=400,
            detail="Invalid song ID."
        )

    output_path = GENERATED_DIR / f"{cleaned_song_id}.wav"

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Audio file not found."
        )

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename=f"{cleaned_song_id}.wav"
    )
