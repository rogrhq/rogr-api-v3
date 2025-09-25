import logging, json, sys
logger = logging.getLogger("rogr")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(h)
logger.setLevel(logging.INFO)
def jlog(event: str, **kw):
    logger.info(json.dumps({"event": event, **kw}))