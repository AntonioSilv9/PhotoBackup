from pathlib import Path
from datetime import datetime
import uuid
import hashlib
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from app.db import init_db, SessionLocal, Photo
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from PIL import Image



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# Pasta onde as fotos são guardadas (vem do Docker volume)
PHOTOS_DIR = Path("/photos")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Photo Backup API"}


@app.post("/upload")
async def upload_photos(files: List[UploadFile] = File(...)):

    db = SessionLocal()
    results = []

    for file in files:
        file_bytes = await file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # verificar duplicado
        existing = db.query(Photo).filter(Photo.hash == file_hash).first()

        if existing:
            results.append({
                "status": "duplicate",
                "stored_path": existing.path,
                "sha256": file_hash
            })
            continue

        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_name = f"{uuid.uuid4()}.{ext}"

        now = datetime.now()
        folder = PHOTOS_DIR / str(now.year) / f"{now.month:02}" / f"{now.day:02}"
        folder.mkdir(parents=True, exist_ok=True)

        destination = folder / unique_name

        with open(destination, "wb") as f:
            f.write(file_bytes)
            img = Image.open(destination)

            img.thumbnail((300, 300))

            thumb_name = f"thumb_{unique_name}"
            thumb_path = folder / thumb_name

            img.save(thumb_path)

        relative_path = str(destination.relative_to(PHOTOS_DIR))

        photo = Photo(
            hash=file_hash,
            path=relative_path,
            thumb_path=str(thumb_path.relative_to(PHOTOS_DIR))
        )

        db.add(photo)

        results.append({
            "status": "uploaded",
            "stored_path": relative_path,
            "sha256": file_hash
        })

    db.commit()
    db.close()

    return results


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


@app.get("/photo/{photo_id}")
def get_photo(photo_id: int, db: Session = Depends(get_db)):

    photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    full_path = PHOTOS_DIR / photo.path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(full_path)


@app.get("/photo/{photo_id}/info")
def get_photo_info(photo_id: int, db: Session = Depends(get_db)):

    photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    result = {
        "id": photo.id,
        "path": photo.path,
        "hash": photo.hash,
        "created_at": photo.created_at
    }


    return result


@app.get("/photo/{photo_id}/thumb")
def get_thumbnail(photo_id: int, db: Session = Depends(get_db)):

    photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    full_path = PHOTOS_DIR / photo.thumb_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Thumb not found")

    return FileResponse(full_path)