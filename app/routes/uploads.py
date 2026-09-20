from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, Depends, File, UploadFile

from app.services.dependencies import require_admin

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


@router.post("/api/admin/upload")
def upload_image(
    file: UploadFile = File(...),
    admin_id: int = Depends(require_admin)
):
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    if file.content_type not in allowed_types:
        return {
            "error": "Only JPG, PNG and WEBP images are allowed"
        }

    extension = Path(file.filename or "").suffix.lower()
    expected_extensions = {
        "image/jpeg": {".jpg", ".jpeg"},
        "image/png": {".png"},
        "image/webp": {".webp"},
    }
    if extension not in expected_extensions.get(file.content_type, set()):
        return {"error": "The file extension does not match its image type"}

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_UPLOAD_SIZE:
        return {"error": "Images must be 10 MB or smaller"}

    filename = f"{uuid.uuid4()}{extension}"

    filepath = UPLOAD_DIR / filename

    with filepath.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "url": f"/uploads/{filename}"
    }