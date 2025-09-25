from typing import List
def get_providers(skip_unconfigured: bool = True):
    providers: List[object] = []
    for dotted in [
        "search_providers.google_cse.provider:GoogleCSEProvider",
        "search_providers.bing.provider:BingProvider",
    ]:
        mod, cls = dotted.split(":")
        try:
            m = __import__(mod, fromlist=[cls])
            C = getattr(m, cls)
            providers.append(C())
        except RuntimeError:
            if not skip_unconfigured:
                raise
        except Exception:
            # deterministically ignore unexpected import errors
            pass
    return providers