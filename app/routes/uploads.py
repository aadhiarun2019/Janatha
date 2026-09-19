from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, Depends, File, UploadFile

from app.services.dependencies import require_admin

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


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

    extension = Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4()}{extension}"

    filepath = UPLOAD_DIR / filename

    with filepath.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "url": f"/uploads/{filename}"
    }