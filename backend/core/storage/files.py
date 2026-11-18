"""File path helpers."""
import uuid
from pathlib import Path


def build_upload_path(prefix: str, original_filename: str) -> str:
    ext = Path(original_filename).suffix
    return f"{prefix}/{uuid.uuid4().hex}{ext}"