import httpx
def client():
    return httpx.Client(timeout=10.0, follow_redirects=True, headers={"User-Agent":"ROGR/1.0"})