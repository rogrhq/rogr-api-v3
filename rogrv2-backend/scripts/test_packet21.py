#!/usr/bin/env python3
import json, sys, urllib.request, uuid

BASE = "http://localhost:8000"

def post_json(path, data, bearer=None, timeout=45):
    url = f"{BASE}{path}"
    headers = {"Content-Type":"application/json"}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def post_multipart(path, fields, files, bearer=None, timeout=45):
    """
    fields: list of (name, value)
    files: list of (name, filename, bytes, content_type)
    """
    boundary = "----pkt21" + uuid.uuid4().hex
    lines = []
    for (k, v) in fields:
        lines.append(f"--{boundary}\r\n".encode("utf-8"))
        lines.append(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
        lines.append((str(v)).encode("utf-8"))
        lines.append(b"\r\n")
    for (name, filename, content, ctype) in files:
        lines.append(f"--{boundary}\r\n".encode("utf-8"))
        lines.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode("utf-8"))
        lines.append(f"Content-Type: {ctype}\r\n\r\n".encode("utf-8"))
        lines.append(content)
        lines.append(b"\r\n")
    lines.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(lines)
    url = f"{BASE}{path}"
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    # auth
    code, reg = post_json("/auth/register", {"email":"packet21@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    # upload a small text file
    text_bytes = b"Austin increased its 2024 city budget by 8%."
    code, up = post_multipart(
        "/media/upload",
        fields=[("kind","text")],
        files=[("file","sample.txt", text_bytes, "text/plain")],
        bearer=tok
    )
    assert code == 200 and "media_id" in up and "analysis_id" in up, f"upload failed: {code} {up}"
    mid = up["media_id"]

    # preview from media
    code, pv = post_json("/mobile/preview_from_media", {"media_id": mid, "test_mode": True}, bearer=tok)
    assert code == 200 and "claims" in pv and "overall" in pv, f"preview_from_media bad: {code} {pv}"
    assert isinstance(pv["claims"], list) and len(pv["claims"]) >= 1, "no claims in preview"

    # commit from media
    code, cm = post_json("/mobile/commit_from_media", {"media_id": mid, "test_mode": True}, bearer=tok)
    assert code == 200 and "analysis_id" in cm, f"commit_from_media failed: {code} {cm}"

    print("PASS")

if __name__ == "__main__":
    main()