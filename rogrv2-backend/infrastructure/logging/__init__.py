import logging, json, sys
try:
    from .ctx import get_request_id
except Exception:  # fallback if ctx not yet importable
    def get_request_id():
        return None
logger = logging.getLogger("rogr")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(h)
logger.setLevel(logging.INFO)
def jlog(event: str, **kw):
    rid = get_request_id()
    base = {"event": event, **kw}
    if rid:
        base["request_id"] = rid
    logger.info(json.dumps(base))