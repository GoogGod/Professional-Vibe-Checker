import argparse
import html
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

import requests

BASE = "http://INSTANCE_URL"
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "cookies2.txt")


def load_cookie():
    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "docus_session" in line:
                parts = line.strip().split("\t")
                return parts[-1]
    raise RuntimeError("cookie not found")


def session():
    s = requests.Session()
    s.cookies.set("docus_session", load_cookie(), domain=urlparse(BASE).hostname)
    return s


def get_editor(s, did):
    r = s.get(f"{BASE}/edit/{did}", timeout=20)
    m = re.search(r'<iframe[^>]+src="([^"]+)"', r.text, re.I)
    if not m:
        raise RuntimeError(f"no iframe in {r.status_code}")
    url = html.unescape(m.group(1))
    qs = parse_qs(urlparse(url).query)
    return {
        "iframe": url,
        "token": qs.get("access_token", [""])[0],
        "wopisrc": qs.get("WOPISrc", [""])[0],
        "permission": qs.get("permission", [""])[0],
    }


def cmd_edit(s, args):
    info = get_editor(s, args.id)
    print(info["iframe"])


def cmd_token(s, args):
    info = get_editor(s, args.id)
    print(info["token"])


def cmd_get(s, args):
    info = get_editor(s, args.id)
    r = s.get(f"{BASE}/wopi/files/{args.id}/contents", params={"access_token": info["token"]}, timeout=30)
    if args.out:
        with open(args.out, "wb") as f:
            f.write(r.content)
        print(f"saved {len(r.content)} bytes to {args.out}")
    else:
        sys.stdout.write(r.content.decode("utf-8", "replace"))


def cmd_put(s, args):
    info = get_editor(s, args.id)
    with open(args.file, "rb") as f:
        data = f.read()
    r = s.post(
        f"{BASE}/wopi/files/{args.id}/contents",
        params={"access_token": info["token"]},
        data=data,
        headers={"X-WOPI-Override": "PUT", "Content-Type": "application/octet-stream"},
        timeout=30,
    )
    print("PUT", r.status_code, r.text[:300])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("edit", cmd_edit), ("token", cmd_token), ("get", cmd_get), ("put", cmd_put)):
        p = sub.add_parser(name)
        p.add_argument("id")
        if name == "get":
            p.add_argument("--out")
        if name == "put":
            p.add_argument("file")
        p.set_defaults(func=fn)
    args = ap.parse_args()
    s = session()
    args.func(s, args)


if __name__ == "__main__":
    main()

