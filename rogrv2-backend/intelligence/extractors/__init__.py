from __future__ import annotations
from typing import Optional

def extract_text(kind: str, data: bytes, filename: Optional[str] = None, test_mode: bool = True) -> str:
    """
    Return extracted text from media bytes.
    - kind: "text" | "image" | "audio" | "video"
    - For MVP:
        * text: decode utf-8 (errors='ignore')
        * image/audio/video: return deterministic stub when test_mode=True
    """
    k = (kind or "text").lower()
    if k == "text":
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    # Deterministic stubs for non-text kinds (no external tools)
    base = {
        "image": "[OCR disabled in MVP]",
        "audio": "[Transcription disabled in MVP]",
        "video": "[ASR/AV disabled in MVP]",
    }.get(k, "[Unknown media kind]")
    if test_mode:
        return f"{base} filename={filename or ''} bytes={len(data)}"
    return ""