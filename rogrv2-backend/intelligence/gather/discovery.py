from typing import List, Dict, Optional
from search_providers.factory import get_providers

def interleaved_candidates(query: str, date_window: Optional[str] = None) -> List[Dict]:
    provs = get_providers(skip_unconfigured=True)
    lists = [p.search(query, date_window) for p in provs]
    out: List[Dict] = []
    for rank in range(10):
        for lst in lists:
            if rank < len(lst):
                out.append(lst[rank])
    return out