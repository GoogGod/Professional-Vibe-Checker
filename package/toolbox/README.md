# Toolbox: рабочие скрипты и заготовки

Требования: самодостаточность, кроссплатформенность (или два варианта Win/*nix),
заголовок-комментарий: назначение / использование / проверено на.

## Скрипты в корне

- `net_session.py` — интерактивный TCP-клиент без PTY (Windows-safe) для netcat-челленджей.
  Вход — JSON в stdin: `{"host": "...", "port": N, "timeout": 15, "interactions": [{"expect": "regex", "send": "строка\n", "wait": 1}]}`.
  Без `interactions` принимает и читает до таймаута. «Диалог»: ждёт `expect` (regex),
  затем шлёт `send`, слушает `wait` сек; в конце дочитывает остаток.
  Обновлено 2026-11-04: не чистит буфер перед первым шагом, `seek()` ждёт regex,
  `send` отправляется только после матчинга промпта, обрабатывается `OSError`, финальный recv.
- `py_run.py` — локальный запуск Python-кода (или файла) с stdin/args/таймаутом.
  Вход — JSON в stdin: `{"code": "...", "stdin": "...", "args": [], "timeout": 60}` или `{"file": "path.py"}`.
  Возвращает JSON `{stdout, stderr, exit, timed_out}`. Кодировка UTF-8, errors=replace.
- `alpha_lsb.py`, `lsb_harvest.py` — LSB-стеганография (alpha-канал, сбор).
- `video_color_events.py` — анализ цветных событий в видео.

## Подкаталоги

- `docus/` — разбор документов (PDF-потоки и т.п.), `docus_poc_run.py`.
- `crypto-limited/` — криптографические инструменты (частотный анализ, XOR, LFSR и др.).
- `pwn/` — эксплоиты и каркасы: `pty_transport.py`, `bytewise_shellcode.py`,
  `fmt_leak_helper.py`, `heap_tcache_hook.py`, `README.md`.
- `ad/` — рекламные/шумные артефакты (скрипты очистки).

## Тулзы платформы (пользовательские)

- `net_session` (script) — обёртка над `net_session.py`: путь к модулю берётся из
  `package/toolbox/net_session.py` (обновление кода = обновление тулзы; без дублирования).
- `py_run` (script) — автономная реализация (код встроен в тулзу).
