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
from PIL import Image, ImageOps

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

PHOTOS_DIR = Path("/photos")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/upload")
async def upload_photos(files: List[UploadFile] = File(...)):

    db = SessionLocal()
    results = []

    for file in files:
        file_bytes = await file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        existing = db.query(Photo).filter(Photo.hash == file_hash).first()

        if existing:
            continue

        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        name = f"{uuid.uuid4()}.{ext}"

        now = datetime.now()
        folder = PHOTOS_DIR / str(now.year) / f"{now.month:02}" / f"{now.day:02}"
        folder.mkdir(parents=True, exist_ok=True)

        path = folder / name

        # salva original
        with open(path, "wb") as f:
            f.write(file_bytes)

        # 🔥 CORRIGE ORIENTAÇÃO (IMPORTANTE)
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)

        # thumbnail
        thumb = img.copy()
        thumb.thumbnail((400, 400))

        thumb_path = folder / f"thumb_{name}"
        thumb.save(thumb_path)

        relative = str(path.relative_to(PHOTOS_DIR))
        relative_thumb = str(thumb_path.relative_to(PHOTOS_DIR))

        photo = Photo(
            hash=file_hash,
            path=relative,
            thumb_path=relative_thumb
        )

        db.add(photo)

    db.commit()
    db.close()

    return {"status": "ok"}


@app.get("/photos")
def photos(db: Session = Depends(get_db)):
    return db.query(Photo).order_by(Photo.id.desc()).all()


@app.get("/photo/{photo_id}")
def photo(photo_id: int, db: Session = Depends(get_db)):

    p = db.query(Photo).filter(Photo.id == photo_id).first()

    if not p:
        raise HTTPException(404)

    return FileResponse(PHOTOS_DIR / p.path)


@app.get("/photo/{photo_id}/thumb")
def thumb(photo_id: int, db: Session = Depends(get_db)):

    p = db.query(Photo).filter(Photo.id == photo_id).first()

    if not p:
        raise HTTPException(404)

    return FileResponse(PHOTOS_DIR / p.thumb_path)