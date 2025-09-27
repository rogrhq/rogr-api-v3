#!/usr/bin/env python3
"""
Developer preview runner (no extra deps).
- Registers (email -> token)
- Calls /analyses/preview with your text
- Prints a compact summary and saves full JSON under outputs/<timestamp>.json

Usage:
  BASE=http://localhost:8000 python3 scripts/dev_preview.py --text "Your claim text"
  python3 scripts/dev_preview.py --file path/to/claim.txt
  python3 scripts/dev_preview.py --text "..." --email you@example.com
"""

import os, sys, json, argparse, datetime, pathlib, urllib.request, urllib.error

BASE = os.environ.get("BASE", "http://localhost:8000")

def _req(method: str, path: str, data=None, headers=None):
    url = f"{BASE}{path}"
    hdrs = {} if headers is None else dict(headers)
    body = None
    if data is not None:
        hdrs["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
        return resp.getcode(), json.loads(raw)

def register(email: str) -> str:
    code, body = _req("POST", "/auth/register", {"email": email})
    if code != 200 or "access_token" not in body:
        raise RuntimeError(f"register failed: {code} {body}")
    return body["access_token"]

def preview(token: str, text: str, test_mode: bool=True) -> dict:
    code, body = _req("POST", "/analyses/preview",
                      {"text": text, "test_mode": test_mode},
                      headers={"Authorization": f"Bearer {token}"})
    if code != 200:
        raise RuntimeError(f"preview failed: {code} {body}")
    return body

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", help="Claim/article text to analyze")
    ap.add_argument("--file", help="Path to a text file to analyze")
    ap.add_argument("--email", default="devpreview@example.com", help="Email used for registration")
    ap.add_argument("--no-test-mode", action="store_true", help="Disable test_mode flag")
    args = ap.parse_args()

    text = args.text
    if not text and args.file:
        p = pathlib.Path(args.file)
        if not p.exists(): sys.exit(f"File not found: {p}")
        text = p.read_text(encoding="utf-8")
    if not text:
        sys.exit("Provide --text or --file")

    token = register(args.email)
    data = preview(token, text, (not args.no_test_mode))

    # Print compact summary
    overall = data.get("overall", {})
    claims = data.get("claims", [])
    print(json.dumps({
        "overall": overall,
        "claims_len": len(claims),
        "first_claim": (claims[0] if claims else None)
    }, ensure_ascii=False, indent=2))

    # Save full JSON snapshot
    outdir = pathlib.Path("outputs"); outdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    outpath = outdir / f"preview_{ts}.json"
    outpath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved full result -> {outpath}")

if __name__ == "__main__":
    main()