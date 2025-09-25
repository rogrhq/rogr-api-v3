from __future__ import annotations
import os
from pathlib import Path

_DEFAULT_DIR = "storage/snapshots"

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)
    keep = p / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")

def save_snapshot_html(*, html: str, sha256: str, base_dir: str | None = None) -> str:
    base = Path(os.getenv("SNAPSHOT_DIR") or (base_dir or _DEFAULT_DIR))
    ensure_dir(base)
    path = base / f"{sha256}.html"
    if not path.exists():
        path.write_text(html, encoding="utf-8", errors="ignore")
    return str(path)