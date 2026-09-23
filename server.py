#!/usr/bin/env python3
"""
Interface web locale : connexion, téléchargement et transcription
des podcasts Unicast depuis le navigateur.

Usage:
    uv run python server.py

Ouvre automatiquement http://127.0.0.1:8000 (écoute uniquement en local).
"""

import os
import platform
import subprocess
import sys
import threading
import uuid
import webbrowser
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# auth.py / .env / cookies.json utilisent des chemins relatifs au projet.
os.chdir(ROOT)

import uvicorn  # noqa: E402
from dotenv import dotenv_values, load_dotenv  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import auth  # noqa: E402
import transcribe  # noqa: E402
import unicast  # noqa: E402
from run import COMMON_LANGUAGES, DEFAULT_LANGUAGE, default_output_dir  # noqa: E402

HOST, PORT = "127.0.0.1", 8000
ENV_FILE = ROOT / ".env"
DIST = ROOT / "frontend" / "dist"
ENV_KEYS = {"user": "ULIEGE_USER", "password": "ULIEGE_PASS", "deepgram_key": "DEEPGRAM_API_KEY"}

load_dotenv(ENV_FILE)


# --- Capture des print() des modules existants, par thread -----------------

class _ThreadTee:
    """Redirige les print() d'un thread vers une liste, en plus du terminal."""

    def __init__(self, stream):
        self._stream = stream
        self._local = threading.local()

    def write(self, s):
        sink = getattr(self._local, "sink", None)
        if sink is not None:
            for line in s.splitlines():
                if line.strip():
                    sink.append(line.strip())
        return self._stream.write(s)

    def flush(self):
        self._stream.flush()

    def __getattr__(self, name):
        # isatty(), encoding, fileno()… : utilisés par uvicorn pour ses logs.
        return getattr(self._stream, name)

    @contextmanager
    def capture(self, sink: list[str]):
        self._local.sink = sink
        try:
            yield sink
        finally:
            self._local.sink = None


tee = _ThreadTee(sys.stdout)
sys.stdout = tee


# --- Jobs de téléchargement + transcription ---------------------------------

jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()
# Fichiers / dossiers produits par l'app : seuls ceux-là sont lisibles ou ouvrables.
produced_files: set[Path] = set()
produced_dirs: set[Path] = set()


def _run_job(job: dict, student_id: str, output_dir: Path, language: str, do_transcribe: bool) -> None:
    cookies = auth.load_cookies()
    for item in job["items"]:
        if job["cancel"]:
            item["status"] = "cancelled"
            continue
        with tee.capture(item["log"]):
            item["status"] = "downloading"
            try:
                mp3 = unicast.download(item["podcast"], output_dir, cookies, student_id)
            except Exception as e:
                mp3 = None
                print(f"Erreur téléchargement : {e}")
            if not mp3:
                item["status"] = "error"
                continue
            item["mp3"] = str(mp3.resolve())
            produced_files.add(mp3.resolve())

            if not do_transcribe:
                item["status"] = "done"
                continue
            item["status"] = "transcribing"
            try:
                txt = transcribe.transcribe(mp3, language=language)
                item["txt"] = str(txt.resolve())
                produced_files.add(txt.resolve())
                item["status"] = "done"
            except Exception as e:
                print(f"Erreur transcription : {e}")
                item["status"] = "error"
    job["status"] = "finished"


# --- API -------------------------------------------------------------------

app = FastAPI(title="Unicast Transcriber")


class ConfigIn(BaseModel):
    user: str = ""
    password: str = ""
    deepgram_key: str = ""


class PodcastsIn(BaseModel):
    url: str


class Podcast(BaseModel):
    id: str
    title: str
    date: str


class JobIn(BaseModel):
    podcasts: list[Podcast]
    student_id: str = ""
    output_dir: str
    language: str = DEFAULT_LANGUAGE
    transcribe: bool = True


class PathIn(BaseModel):
    path: str


def _config_status() -> dict:
    return {
        "user": os.getenv("ULIEGE_USER", ""),
        "has_password": bool(os.getenv("ULIEGE_PASS")),
        "has_deepgram": bool(os.getenv("DEEPGRAM_API_KEY")),
        "has_session": auth.COOKIES_FILE.exists(),
        "languages": [{"code": c, "label": label} for c, label in COMMON_LANGUAGES],
        "default_language": DEFAULT_LANGUAGE,
    }


@app.get("/api/config")
def get_config() -> dict:
    return _config_status()


@app.put("/api/config")
def put_config(body: ConfigIn) -> dict:
    """Écrit les champs non vides dans .env (les autres clés sont conservées)."""
    values = {k: v for k, v in dotenv_values(ENV_FILE).items() if v is not None} if ENV_FILE.exists() else {}
    for field, key in ENV_KEYS.items():
        new = getattr(body, field).strip()
        if new:
            values[key] = new
            os.environ[key] = new
    ENV_FILE.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    return _config_status()


@app.post("/api/login")
def login() -> dict:
    log: list[str] = []
    with tee.capture(log):
        try:
            ok = auth.login()
        except Exception as e:
            ok = False
            log.append(f"Échec de la connexion : {e}")
    if not ok:
        raise HTTPException(400, log[-1] if log else "Connexion impossible.")
    return _config_status()


@app.get("/api/courses")
def list_courses() -> list[dict]:
    log: list[str] = []
    with tee.capture(log):
        try:
            courses = unicast.list_courses()
        except Exception as e:
            raise HTTPException(400, f"Erreur : {e}")
    if courses is None:
        raise HTTPException(400, log[-1] if log else "Impossible de charger tes cours.")
    return courses


@app.post("/api/podcasts")
def list_podcasts(body: PodcastsIn) -> dict:
    if "unicast.uliege.be" not in body.url:
        raise HTTPException(400, "URL invalide (doit contenir 'unicast.uliege.be').")
    log: list[str] = []
    with tee.capture(log):
        try:
            student_id, podcasts, cookies = unicast.list_podcasts(body.url)
        except Exception as e:
            raise HTTPException(400, f"Erreur : {e}")
    if cookies is None:
        raise HTTPException(400, log[-1] if log else "Page du cours inaccessible.")
    if not podcasts:
        raise HTTPException(404, "Aucun podcast publié pour ce cours pour l'instant.")
    return {
        "student_id": student_id,
        "podcasts": podcasts,
        "default_output_dir": default_output_dir(body.url),
    }


@app.post("/api/jobs")
def create_job(body: JobIn) -> dict:
    if not body.podcasts:
        raise HTTPException(400, "Aucun podcast sélectionné.")
    if body.transcribe and not os.getenv("DEEPGRAM_API_KEY"):
        raise HTTPException(400, "Clé Deepgram manquante : ajoute-la dans les réglages.")
    with jobs_lock:
        if any(j["status"] == "running" for j in jobs.values()):
            raise HTTPException(409, "Un traitement est déjà en cours.")
        output_dir = Path(body.output_dir).expanduser()
        if not output_dir.is_absolute():
            output_dir = ROOT / output_dir
        output_dir = output_dir.resolve()
        produced_dirs.add(output_dir)
        job = {
            "id": uuid.uuid4().hex,
            "status": "running",
            "cancel": False,
            "output_dir": str(output_dir),
            "items": [
                {"podcast": p.model_dump(), "status": "pending", "log": [], "mp3": None, "txt": None}
                for p in body.podcasts
            ],
        }
        jobs[job["id"]] = job
    threading.Thread(
        target=_run_job,
        args=(job, body.student_id, output_dir, body.language, body.transcribe),
        daemon=True,
    ).start()
    return _public_job(job)


def _public_job(job: dict) -> dict:
    return {k: v for k, v in job.items() if k != "cancel"}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Traitement introuvable.")
    return _public_job(job)


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Traitement introuvable.")
    job["cancel"] = True
    return _public_job(job)


@app.post("/api/transcript")
def read_transcript(body: PathIn) -> dict:
    path = Path(body.path).resolve()
    if path not in produced_files or path.suffix != ".txt" or not path.exists():
        raise HTTPException(404, "Transcript introuvable.")
    return {"text": path.read_text(encoding="utf-8")}


@app.post("/api/open")
def open_path(body: PathIn) -> dict:
    """Ouvre un dossier de sortie (ou un fichier produit) dans l'explorateur."""
    path = Path(body.path).resolve()
    if path not in produced_dirs and path not in produced_files:
        raise HTTPException(403, "Chemin non autorisé.")
    if not path.exists():
        raise HTTPException(404, "Chemin introuvable.")
    system = platform.system()
    if system == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])
    return {"ok": True}


if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
else:
    @app.get("/", response_class=HTMLResponse)
    def missing_frontend() -> str:
        return (
            "<h1>Interface non compilée</h1>"
            "<p>Lance <code>cd frontend &amp;&amp; pnpm install &amp;&amp; pnpm build</code> puis relance le serveur.</p>"
        )


def main() -> None:
    # Navigateur utilisé par auth.py pour la connexion (no-op s'il est déjà installé).
    print("Vérification du navigateur de connexion…")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)

    url = f"http://{HOST}:{PORT}"
    print(f"Interface disponible sur {url}  (Ctrl+C pour arrêter)")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
