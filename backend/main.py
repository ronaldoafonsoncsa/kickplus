import os
import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from video_utils import extract_frames
from analyzer import analyze_video_frames

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")
UPLOADS_DIR = BASE_DIR / "uploads"
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR.mkdir(exist_ok=True)

ALLOWED_SKILLS = {"shot", "pass", "control"}
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
MAX_FILE_SIZE_MB = 100

ERRORS = {
    "pt": {
        "invalid_skill": "Fundamento inválido. Use: shot, pass ou control.",
        "invalid_format": "Formato de vídeo não suportado: {}",
        "file_too_large": f"Vídeo muito grande. Máximo: {MAX_FILE_SIZE_MB}MB.",
        "processing_error": "Erro ao processar vídeo: {}",
    },
    "en": {
        "invalid_skill": "Invalid skill. Use: shot, pass, or control.",
        "invalid_format": "Unsupported video format: {}",
        "file_too_large": f"Video too large. Maximum: {MAX_FILE_SIZE_MB}MB.",
        "processing_error": "Error processing video: {}",
    },
}

app = FastAPI(title="KickPlus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


ALLOWED_LANGUAGES = {"pt", "en"}

@app.post("/api/analyze")
async def analyze(
    video: UploadFile = File(...),
    skill: str = Form(...),
    language: str = Form(default="pt"),
):
    if language not in ALLOWED_LANGUAGES:
        language = "pt"
    err = ERRORS[language]
    if skill not in ALLOWED_SKILLS:
        raise HTTPException(status_code=400, detail=err["invalid_skill"])

    ext = Path(video.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=err["invalid_format"].format(ext))

    video_id = uuid.uuid4().hex
    video_path = UPLOADS_DIR / f"{video_id}{ext}"

    try:
        with open(video_path, "wb") as f:
            content = await video.read()
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=413, detail=err["file_too_large"])
            f.write(content)

        frames = extract_frames(str(video_path), num_frames=4)
        result = analyze_video_frames(frames, skill, language)
        return {"success": True, "analysis": result}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=err["processing_error"].format(str(e)))
    finally:
        if video_path.exists():
            video_path.unlink()


@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
