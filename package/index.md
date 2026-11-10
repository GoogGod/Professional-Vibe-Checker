# Index — реестр записей базы

Формат строки: `дата · тип · путь · краткий итог`. Новые записи добавляй сверху.

## Записи
- 2026-11-10 · lesson · `lessons/2026-11-10-pwn-format-string-bytewise-write.md` · Restricted-alphabet format string: проверка фильтра, позиционные аргументы, `%hhn`, modulo-256 padding и синхронный trigger.
- 2026-11-10 · lesson · `lessons/2026-11-10-pwn-interpreter-cyclic-structure-dos.md` · OOB-индексация + флип тегов в интерпретаторе DSL → arbitrary read/write, PIE/stack-утечки, stack-pivot ROP → RCE; флаг [FLAG].
- 2026-11-05 · lesson · `lessons/2026-11-05-pwn-castle-srop-heap-pivot.md` · PWN hard: SROP через heap-пивот (нет pop rdi/CSU — syscall-гаджет, rax=15; SigreturnFrame; execve("/bin/sh")); ловушки: strace/rt_sigreturn, sync-чтение read (EOF); флаг → [FLAG].
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-menu-read-getc-newline-trap.md` · PWN: меню на read()/fgets() без перевода строки (getc()/scanf()-парсеры): payload до len без '\n', затем prompt; диагностика strace/LD_PRELOAD; не отправлять команды заранее.
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-ruckzak-vtable-partial-overwrite.md` · PWN: heap overflow + частичная перезапись vtable (C++ объект 0x28, ruckzak[16], edit 0x50/0x30, Flag::Display=system("cat flag")); поиск vtable objdump -s .data.rel.ro / IDA; payload без '\n'.
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-museum-tcache-hook-system.md` · PWN: tcache poisoning → __free_hook = system (heap menu, no PIE)
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-post-exploitation-single-command.md` · PWN: пост-эксплуатация — одна команда за запуск вместо интерактивного шелла
- 2026-11-04 · lesson · `lessons/2026-11-04-pwn-debugging-discipline.md` · PWN: дисциплина отладки — как НЕ растрачивать время (разбор сессии)
- 2026-11-04 · tool · `toolbox/pwn/heap_tcache_hook.py` · Каркас heap-menu: leak GOT → free_hook=system
- 2026-10-30 · tool · `toolbox/net_session.py` · Интерактивный TCP-клиент без PTY (Windows-safe) для netcat-челленджей: `host`/`port` + шаги `interactions` (`expect`-regex, `send`, `wait`); без шагов — читает до таймаута; возвращает журнал обмена. Обновлён 2026-11-04: не чистит буфер перед первым шагом, `seek()` ждёт regex, `send` — после матчинга промпта, обработка `OSError`, финальный recv; пользовательская тулза платформы `net_session` — обёртка над этим файлом.
- 2026-11-04 · tool · `toolbox/py_run.py` · Локальный запуск Python-кода/файла с stdin/args/таймаутом; пользовательская тулза платформы `py_run`.

## Как добавлять

1. Создай запись в `lessons/` (шаблон — в скилле `hermes-knowledge-loop`).
2. Добавь строку сюда (сверху списка).
3. Если приём повторяется — обнови файл в `tactics/`; если скрипт >20 строк — положи в `toolbox/`.

Правила: без значений флагов; без названий площадок; относительные пути.