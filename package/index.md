# Index — реестр записей базы

Формат строки: `дата · тип · путь · краткий итог`. Новые записи добавляй сверху.

## Записи
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-fmtstr-canary-leak-gets-ret2exec.md` · PWN: утечка canary через формат-строку и переполнение gets → готовый вызов system(cmd)
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-shellcode-open-read-write-bytewise.md` · PWN: shellcode open/read/write с построением пути посимвольно (bytewise)
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-transport-pty-canonical-xoff.md` · PWN: транспортные обёртки — pty canonical mode и scanf-буферизация
- 2026-11-04 · tool · `toolbox/pwn/pty_transport.py` · Транспорт pty (canonical/XOFF)
- 2026-11-04 · tool · `toolbox/pwn/bytewise_shellcode.py` · Генератор open/read/write bytewise shellcode
- 2026-11-04 · tool · `toolbox/pwn/fmt_leak_helper.py` · Скан позиций %N$p
- 2026-10-30 · tool · `toolbox/net_session.py` · Интерактивный TCP-клиент без PTY (Windows-safe) для netcat-челленджей: `host`/`port` + шаги `interactions` (`expect`-regex, `send`, `wait`); без шагов — читает до таймаута; возвращает журнал обмена.

## Как добавлять

1. Создай запись в `lessons/` (шаблон — в скилле `hermes-knowledge-loop`).
2. Добавь строку сюда (сверху списка).
3. Если приём повторяется — обнови файл в `tactics/`; если скрипт >20 строк — положи в `toolbox/`.

Правила: без значений флагов; без названий площадок; относительные пути.