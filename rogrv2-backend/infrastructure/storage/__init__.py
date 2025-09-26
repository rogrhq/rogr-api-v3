from pathlib import Path
from typing import Optional
import os, hashlib
import pathlib
def save_html(path: str, html: str) -> str:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    return str(p)

def save_upload_bytes(*, filename: str, data: bytes, base_dir: Optional[str] = None) -> dict:
    """
    Persist raw upload bytes under storage/uploads/{sha256}{ext}.
    Returns dict: {"path": str, "sha256": str, "ext": str}
    """
    base = Path(os.getenv("UPLOAD_DIR") or base_dir or "storage/uploads")
    base.mkdir(parents=True, exist_ok=True)
    # derive extension from filename
    name = (filename or "").strip()
    ext = ""
    if "." in name:
        ext = "." + name.split(".")[-1].lower()[:8]
    sha = hashlib.sha256(data).hexdigest()
    path = base / f"{sha}{ext}"
    if not path.exists():
        path.write_bytes(data)
    return {"path": str(path), "sha256": sha, "ext": ext}