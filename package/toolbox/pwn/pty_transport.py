#!/usr/bin/env python3
"""
pty_transport.py — транспорт для сервисов за pty (canonical mode).
Проблемы, которые решает:
  * строки <= 80 байт (MaxCanon): длинные ROP-строки ломаются;
  * байт 0x13 (XOFF) останавливает вывод — его нужно фильтровать;
  * после строки в 80 байт в очереди остаётся «лишний» \\n (drain);
  * scanf-буферизация: отправлять поэтапно после промптов.
Использование:
    t = PTYTransport(HOST, PORT)
    t.recv_until(b"? ")          # ждать промпт
    t.sendline(b"5")              # короткая строка
    t.send_stage(b"AAAA...")      # длинный payload ЧАСТЯМИ по 80 байт
    out = t.recv_clean(2)         # прочитать с фильтром XOFF
"""

import socket
import time

XOFF = b"\x13"


class PTYTransport:
    def __init__(self, host, port, timeout=10):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)
        self.buf = b""
        self.timeout = timeout

    def recv_until(self, marker, max_wait=10):
        deadline = time.time() + max_wait
        while marker not in self.buf:
            if time.time() > deadline:
                raise TimeoutError(f"no marker {marker!r} in {self.buf[-200:]!r}")
            try:
                chunk = self.s.recv(4096)
                if not chunk:
                    raise ConnectionError("closed")
                self.buf += chunk
            except socket.timeout:
                raise TimeoutError(f"timed out waiting for {marker!r}")
        idx = self.buf.index(marker) + len(marker)
        data, self.buf = self.buf[:idx], self.buf[idx:]
        return data

    def sendline(self, line: bytes):
        # pty canonical: строка до 80 байт + \n
        if len(line) > 80:
            raise ValueError("line > 80 bytes, use send_stage")
        self.s.sendall(line + b"\n")

    def send_stage(self, payload: bytes):
        # длинный payload: режем по 80 байт, между кусками recv-команда
        for i in range(0, len(payload), 80):
            self.s.sendall(payload[i:i + 80])
            self.s.sendall(b"\n")
            time.sleep(0.1)
            # drain оставшихся \n из очереди
            self.s.sendall(b"\n")
            time.sleep(0.1)

    def drain(self, wait=0.3):
        """Слить всё, что скопилось (в т.ч. лишние \n)."""
        time.sleep(wait)
        self.s.setblocking(False)
        try:
            while True:
                chunk = self.s.recv(4096)
                if not chunk:
                    break
                self.buf += chunk
        except BlockingIOError:
            pass
        finally:
            self.s.setblocking(True)

    def recv_clean(self, seconds=2.0):
        """Прочитать с фильтром XOFF."""
        self.drain(seconds)
        data = self.buf
        self.buf = b""
        return data.replace(XOFF, b"")

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
