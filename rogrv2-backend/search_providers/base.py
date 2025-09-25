from typing import List, Dict, Optional

class SearchProvider:
    def search(self, query: str, date_window: Optional[str] = None) -> List[Dict]:
        raise NotImplementedError