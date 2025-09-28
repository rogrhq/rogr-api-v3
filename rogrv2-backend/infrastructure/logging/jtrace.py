import traceback, json, sys, uuid

def error_event(event: str, **kw):
    rid = kw.pop("request_id", None) or str(uuid.uuid4())
    rec = {"event": event, "level": "error", "request_id": rid, **kw}
    try:
        print(json.dumps(rec), file=sys.stderr)
    except Exception:
        # last-ditch
        print({"event": event, "level": "error", "request_id": rid, **kw}, file=sys.stderr)
    return rid

def format_exc(e: BaseException) -> str:
    return "".join(traceback.format_exception(type(e), e, e.__traceback__))