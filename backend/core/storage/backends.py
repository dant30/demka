"""Private storage backend (not exposed via public URL)."""
from django.core.files.storage import FileSystemStorage


class PrivateStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", "media/private")
        kwargs.setdefault("base_url", None)
        super().__init__(*args, **kwargs)