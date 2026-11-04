# -*- coding: utf-8 -*-
"""net_session: интерактивный TCP-клиент без PTY (Windows-safe).

Параметры — JSON в stdin. Схема:
  host (str, обяз.), port (int, обяз.), timeout (float, опц., default 15),
  recv_bytes (int, опц., default 65536),
  interactions (list, опц.): [{"expect": "regex", "send": "строка (обычно с \n)", "wait": 1.0}]
Без interactions — просто читает данные до таймаута.
Также принимается "host:port" / "host port" / "nc host port" в поле args.
Возвращает журнал обмена: recv, prompt_matched, send.
"""
import json
import re
import socket
import sys
import time
from urllib.parse import urlparse

DEFAULT_TIMEOUT = 15.0
DEFAULT_RECV = 65536


def parse_args_string(s):
    s = (s or "").strip()
    if not s:
        return {}
    if s.startswith("{"):
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    if "://" in s:
        try:
            u = urlparse(s)
            if u.hostname:
                return {"host": u.hostname, "port": u.port} if u.port else {"host": u.hostname}
        except Exception:
            pass
    toks = s.split()
    while toks and toks[0].lower() in ("nc", "ncat", "netcat", "nc.exe"):
        toks.pop(0)
    toks = [t for t in toks if not t.startswith("-")]
    if not toks:
        return {}
    if ":" in toks[0]:
        h, _, p = toks[0].rpartition(":")
        if p.isdigit():
            return {"host": h, "port": int(p)}
    if len(toks) >= 2 and toks[-1].isdigit():
        return {"host": toks[0], "port": int(toks[-1])}
    return {"host": toks[0]}


def resolve_params(params):
    d = {}
    args = params.get("args")
    if isinstance(args, str) and args.strip():
        d.update(parse_args_string(args))
    for k in ("host", "port", "timeout", "interactions", "recv_bytes"):
        if k in params and params[k] is not None:
            d[k] = params[k]
    host = d.get("host", "")
    try:
        port = int(d.get("port", 0))
    except (TypeError, ValueError):
        port = 0
    timeout = float(d.get("timeout", DEFAULT_TIMEOUT))
    recv_bytes = int(d.get("recv_bytes", DEFAULT_RECV))
    interactions = d.get("interactions") or []
    if isinstance(interactions, str):
        try:
            interactions = json.loads(interactions)
        except Exception:
            interactions = []
    if not isinstance(interactions, list):
        interactions = []
    return host, port, timeout, recv_bytes, interactions


def main():
    raw = sys.stdin.buffer.read().decode("utf-8-sig")
    try:
        params = json.loads(raw) if raw.strip() else {}
    except Exception:
        params = {}
    host, port, timeout, recv_bytes, interactions = resolve_params(params)
    if not host or not port:
        print(json.dumps({
            "error": 'нужны host и port: {"host":"...","port":N} (или args: "host:port")'
        }, ensure_ascii=False))
        return

    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
    except Exception as e:
        print(json.dumps({"error": f"connect: {e}"}, ensure_ascii=False))
        return

    buf = b""
    out = []

    def pump(duration):
        nonlocal buf
        until = time.time() + duration
        while time.time() < until:
            try:
                chunk = s.recv(recv_bytes)
                if not chunk:
                    return False
                buf += chunk
            except socket.timeout:
                return True
        return True

    def drain_all():
        nonlocal buf
        if buf:
            out.append({"type": "recv", "data": buf.decode(errors="replace")})
            buf = b""

    def seek(pat, budget):
        until = time.time() + budget
        while time.time() < until:
            if re.search(pat, buf.decode(errors="replace"), re.S):
                return True
            if not pump(0.5):
                return bool(re.search(pat, buf.decode(errors="replace"), re.S))
        return re.search(pat, buf.decode(errors="replace"), re.S) is not None

    if not interactions:
        pump(timeout)
        drain_all()
        s.close()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    alive = True
    for step in interactions:
        expect = step.get("expect")
        send = step.get("send", "\n")
        wait = float(step.get("wait", 1))
        if expect:
            found = seek(expect, max(wait, 5.0))
            if found:
                out.append({"type": "prompt_matched", "pattern": expect})
        if alive:
            try:
                s.sendall(send.encode() if isinstance(send, str) else send)
                out.append({"type": "send", "data": send})
            except OSError:
                alive = False
        if alive:
            alive = pump(wait)
    try:
        s.settimeout(3)
        while True:
            chunk = s.recv(recv_bytes)
            if not chunk:
                break
            buf += chunk
    except Exception:
        pass
    drain_all()
    s.close()
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
