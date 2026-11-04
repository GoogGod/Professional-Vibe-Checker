# Index — реестр записей базы

Формат строки: `дата · тип · путь · краткий итог`. Новые записи добавляй сверху.

## Записи
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-museum-tcache-hook-system.md` · PWN: tcache poisoning → __free_hook = system (heap menu, no PIE)
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-post-exploitation-single-command.md` · PWN: пост-эксплуатация — одна команда за запуск вместо интерактивного шелла
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-debugging-discipline.md` · PWN: дисциплина отладки — как НЕ растрачивать время (разбор сессии)
- 2026-11-04 · tool · `toolbox/pwn/heap_tcache_hook.py` · Каркас heap-menu: leak GOT → free_hook=system
- 2026-10-30 · tool · `toolbox/net_session.py` · Интерактивный TCP-клиент без PTY (Windows-safe) для netcat-челленджей: `host`/`port` + шаги `interactions` (`expect`-regex, `send`, `wait`); без шагов — читает до таймаута; возвращает журнал обмена.

## Как добавлять

1. Создай запись в `lessons/` (шаблон — в скилле `hermes-knowledge-loop`).
2. Добавь строку сюда (сверху списка).
3. Если приём повторяется — обнови файл в `tactics/`; если скрипт >20 строк — положи в `toolbox/`.

Правила: без значений флагов; без названий площадок; относительные пути.