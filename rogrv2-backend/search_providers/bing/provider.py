import os, httpx
from typing import List, Dict, Optional
from search_providers.base import SearchProvider

BING_URL = "https://api.bing.microsoft.com/v7.0/search"

class BingProvider(SearchProvider):
    def __init__(self):
        self.key = os.environ.get("BING_API_KEY")
        if not self.key:
            raise RuntimeError("BING_API_KEY missing")
    def search(self, query: str, date_window: Optional[str] = None) -> List[Dict]:
        headers = {"Ocp-Apim-Subscription-Key": self.key}
        params = {"q": query, "count": 10, "textDecorations": "false", "textFormat": "Raw"}
        r = httpx.get(BING_URL, headers=headers, params=params, timeout=15.0)
        r.raise_for_status()
        web = (r.json().get("webPages") or {}).get("value", []) or []
        out: List[Dict] = []
        for i, it in enumerate(web[:10]):
            out.append({
                "provider": "bing",
                "rank": i + 1,
                "url": it.get("url"),
                "title": it.get("name") or "",
                "snippet": it.get("snippet") or ""
            })
        return out