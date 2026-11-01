import html
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

import requests

BASE = "http://INSTANCE_URL"
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "cookies2.txt")


def load_cookie():
    with open(COOKIE_FILE, encoding="utf-8") as f:
        for line in f:
            if "docus_session" in line:
                return line.strip().split("\t")[-1]
    raise RuntimeError


COOKIE = load_cookie()


def main():
    ids = sys.argv[1:]
    os.makedirs("peek", exist_ok=True)
    s = requests.Session()
    s.cookies.set("docus_session", COOKIE, domain=urlparse(BASE).hostname)
    for raw in ids:
        did = raw if raw.startswith("d") else "d" + raw
        try:
            r = s.get(f"{BASE}/edit/{did}", timeout=15)
            m = re.search(r'<iframe[^>]+src="([^"]+)"', r.text, re.I)
            if not m:
                print(f"### {did}: no iframe ({r.status_code})")
                continue
            url = html.unescape(m.group(1))
            token = parse_qs(urlparse(url).query).get("access_token", [""])[0]
            info = s.get(f"{BASE}/wopi/files/{did}", params={"access_token": token}, timeout=15)
            c = s.get(f"{BASE}/wopi/files/{did}/contents", params={"access_token": token}, timeout=25)
            print(f"### {did}: info={info.status_code} size={len(c.content)} token={token[:12]}")
            try:
                print("INFO:", info.text[:400])
            except Exception:
                pass
            with open(os.path.join("peek", f"{did}.bin"), "wb") as f:
                f.write(c.content)
            txt = c.content.decode("utf-8", "replace")
            print("CONTENT:", txt[:1500].replace("\r", " "))
            print()
        except Exception as e:
            print(f"### {did}: ERR {e}")


if __name__ == "__main__":
    main()
