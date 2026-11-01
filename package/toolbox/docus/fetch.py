import os
import sys
from urllib.parse import urlparse

import requests

BASE = "http://INSTANCE_URL"
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "cookies2.txt")


def load_cookie():
    with open(COOKIE_FILE, encoding="utf-8") as f:
        for line in f:
            if "docus_session" in line:
                return line.strip().split("\t")[-1]
    raise RuntimeError


def main():
    s = requests.Session()
    s.cookies.set("docus_session", load_cookie(), domain=urlparse(BASE).hostname)
    path = sys.argv[1]
    method = sys.argv[2].upper() if len(sys.argv) > 2 else "GET"
    data = sys.argv[3] if len(sys.argv) > 3 else None
    headers = {"Content-Type": "application/x-www-form-urlencoded"} if data else {}
    r = s.request(method, BASE + path, data=data, headers=headers, timeout=30)
    print("STATUS", r.status_code, "LEN", len(r.content), "URL", r.url)
    print("HDR", dict(r.headers))
    sys.stdout.write(r.text[:20000])


if __name__ == "__main__":
    main()
