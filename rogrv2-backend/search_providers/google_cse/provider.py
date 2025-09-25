import os, httpx
from typing import List, Dict, Optional
from search_providers.base import SearchProvider

CSE_URL = "https://www.googleapis.com/customsearch/v1"

class GoogleCSEProvider(SearchProvider):
    def __init__(self):
        self.key = os.environ.get("GOOGLE_CSE_API_KEY")
        self.cx = os.environ.get("GOOGLE_CSE_ENGINE_ID")
        if not self.key or not self.cx:
            raise RuntimeError("GOOGLE_CSE_API_KEY or GOOGLE_CSE_ENGINE_ID missing")
    def search(self, query: str, date_window: Optional[str] = None) -> List[Dict]:
        params = {"key": self.key, "cx": self.cx, "q": query, "num": 10}
        if date_window:
            # limited support; format 'YYYYMMDD:YYYYMMDD' if you use it
            params["sort"] = f"date:r:{date_window}"
        r = httpx.get(CSE_URL, params=params, timeout=15.0)
        r.raise_for_status()
        items = r.json().get("items", []) or []
        out: List[Dict] = []
        for i, it in enumerate(items[:10]):
            out.append({
                "provider": "google_cse",
                "rank": i + 1,
                "url": it.get("link"),
                "title": it.get("title") or "",
                "snippet": it.get("snippet") or ""
            })
        return out