# -*- coding: utf-8 -*-
"""net_session: интерактивный TCP-клиент без PTY (Windows-safe).

Параметры — JSON в stdin (среда: TOOL_NET_SESSION). Схема:
  host  (str, обязательный)  — хост/IP
  port  (int, обязательный)  — TCP-порт
  timeout (float, опц.)      — общий таймаут сек (default 15)
  recv_bytes (int, опц.)     — размер буфера чтения (default 65536)
  interactions (list, опц.)  — шаги диалога:
      [{"expect": "regex промпта", "send": "строка (обычно с \\n)", "wait": 1.0}]
    Без interactions — просто читает всё, что придёт, до таймаута.

Внимание: серверы-челленджи ждут строки, заканчивающиеся переводом строки;
send почти всегда должен заканчиваться на "\\n".

Также принимается строка "host:port" либо "host port" (или "nc host port")
в поле args как уступка конвенциям netcat.
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
    """Минимальный fallback для строковых args: 'host:port'|'host port'|JSON."""
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
            "error": "callbackжны host и port: {\"host\":\"...\",\"port\":N} (или args: \"host:port\")"
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
    deadline = time.time() + timeout

    def pump(until):
        nonlocal buf
        while time.time() < until:
            try:
                chunk = s.recv(recv_bytes)
                if not chunk:
                    return False
                buf += chunk
            except socket.timeout:
                return True
        return True

    def drain():
        nonlocal buf
        if buf:
            out.append({"type": "recv", "data": buf.decode(errors="replace")})
            buf = b""

    if not interactions:
        pump(deadline)
        drain()
        s.close()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    alive = pump(deadline)
    drain()
    for step in interactions:
        expect = step.get("expect")
        send = step.get("send", "\n")
        wait = float(step.get("wait", 1))
        if expect:
            extra = time.time() + max(wait, 5)
            while time.time() < extra:
                if not pump(time.time() + 0.5):
                    break
                if re.search(expect, buf.decode(errors="replace"), re.S):
                    break
            if re.search(expect, buf.decode(errors="replace"), re.S):
                out.append({"type": "prompt_matched", "pattern": expect})
        if alive:
            s.sendall(send.encode() if isinstance(send, str) else send)
            out.append({"type": "send", "data": send})
        alive = pump(time.time() + wait) and alive
    try:
        s.settimeout(3)
        while True:
            chunk = s.recv(recv_bytes)
            if not chunk:
                break
            buf += chunk
    except Exception:
        pass
    drain()
    s.close()
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
