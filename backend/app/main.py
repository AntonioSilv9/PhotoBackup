from pathlib import Path
from datetime import datetime
import uuid
import hashlib

from fastapi import FastAPI, UploadFile, File
from app.db import init_db, SessionLocal, Photo


app = FastAPI()

init_db()

# Pasta onde as fotos são guardadas (vem do Docker volume)
PHOTOS_DIR = Path("/photos")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# Hash set to avoid duplicates
known_hashes = set()

@app.get("/")
def root():
    return {"message": "Photo Backup API"}


@app.post("/upload")
async def upload_photo(file: UploadFile = File(...)):

    file_bytes = await file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    db = SessionLocal()

    # verificar duplicado
    existing = db.query(Photo).filter(Photo.hash == file_hash).first()

    if existing:
        return {
            "status": "duplicate",
            "stored_path": existing.path,
            "sha256": file_hash
        }

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_name = f"{uuid.uuid4()}.{ext}"

    now = datetime.now()
    folder = PHOTOS_DIR / str(now.year) / f"{now.month:02}" / f"{now.day:02}"
    folder.mkdir(parents=True, exist_ok=True)

    destination = folder / unique_name

    with open(destination, "wb") as f:
        f.write(file_bytes)

    relative_path = str(destination.relative_to(PHOTOS_DIR))

    # guardar na DB
    photo = Photo(
        hash=file_hash,
        path=relative_path
    )

    db.add(photo)
    db.commit()
    db.close()

    return {
        "status": "uploaded",
        "stored_path": relative_path,
        "sha256": file_hash
    }


@app.get("/photos")
def list_photos():

    db = SessionLocal()

    photos = db.query(Photo).all()

    result = [
        {
            "id": p.id,
            "path": p.path,
            "hash": p.hash,
            "created_at": p.created_at
        }
        for p in photos
    ]

    db.close()

    return result