import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from middlewares.auth import current_user

router = APIRouter(prefix="/upload", tags=["upload"])

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_ROOT = BASE_DIR / "uploads"
AVATARS_DIR = UPLOAD_ROOT / "avatars"
LOGOS_DIR = UPLOAD_ROOT / "logos"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  


def _ensure_dirs():
    """Create upload directories if they don't exist."""
    AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    LOGOS_DIR.mkdir(parents=True, exist_ok=True)


def _validate_image(file: UploadFile):
    """Validate file extension and content-type."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' is not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed.",
        )


async def _save_file(file: UploadFile, dest_dir: Path) -> str:
    """Read, validate size, save, and return the relative URL path."""
    _ensure_dirs()
    _validate_image(file)

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 5 MB limit.",
        )

    ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = dest_dir / unique_name

    with open(file_path, "wb") as f:
        f.write(contents)

    relative = file_path.relative_to(BASE_DIR)
    return f"/{relative.as_posix()}"


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    _: int = Depends(current_user),
):
    """Upload a user avatar image to local storage."""
    url = await _save_file(file, AVATARS_DIR)
    return {"url": url}


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    _: int = Depends(current_user),
):
    """Upload a business logo image to local storage."""
    url = await _save_file(file, LOGOS_DIR)
    return {"url": url}
