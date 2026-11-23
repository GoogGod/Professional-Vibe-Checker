# Index — реестр записей базы

Формат строки: `дата · тип · путь · краткий итог`. Новые записи добавляй сверху.

## Записи
- 2026-11-24 · lesson · `lessons/2026-11-24-iot-mqtt-announcements-user-bruteforce.md` · MQTT/IoT: «туман» сенсоров + редкие подсказки `/announcements` (зацепка сюжета); перебор пользователя CONNECT/CONNACK (успех 0x00, отказ 0x86) rockyou top-20k → `duck_fan:princess`; retained-секрет читается после логина; баги: Paho username_pw_set ДО connect(), PUBACK 0x87 на запись анонимом; флаг → [FLAG], инстанс → [instance].
- 2026-11-24 · lesson · `lessons/2026-11-24-re-cff-windows-client-protocol-blocks.md` · Сетевая CFF (REV medium): Windows-клиент, кастомный фрейм-протокол `[u32 len][тело]`; BlockImage-кадры, решение `[len=20][var=1][block_id][label]`, host-call fetch; полная спецификация кадров обеих сторон.
- 2026-11-23 · lesson · `lessons/2026-11-23-web-bank-uuidv1-idor.md` · Web easy «Винтажный банк»: IDOR через предсказуемый UUIDv1 (time=время аренды, clock_seq/node фиксированы) — книга вкладов даёт точные даты → восстановление UUID чужой ячейки → чтение флага без проверки владельца; ловушки: несуществующий uuid ≠ пустая ячейка; флаг → [FLAG].
- 2026-11-17 · lesson · `lessons/2026-11-17-web-telegram-phishing-petition-takedown.md` · Telegram-фишинг-воронка (Change.org-клон → клон Telegram Web K): признаки двухступенчатого кита, конфиг base64 в HTML (app_id/app_hash GramJS), статические ресурсы в уникальных хэш-каталогах, takedown-рекомендации; без адресов инстансов.
- 2026-11-15 · lesson · `lessons/2026-11-15-re-cff-vm-frame-protocol-proxy-substitution.md` · REV сетевая: клиент исполняет серверные образы кода (BlockImage), сервер валидирует результаты; формат кадра `[u32 len][payload]`, подмена результата вызова в прокси (смещение 12..20) как техника; перебор констант/ветвлений ACCEPTED; для финала — эмуляция VM локально; [instance]/[FLAG].
- 2026-11-13 · lesson · `lessons/2026-11-13-re-android-apk-bionic-rand-seed-xor-linear-cipher.md` · Android APK JNI (hard, РЕШЕНО): единственный JNI `processInput`, 4 ABI; seed-цепочка ah() (умножение 0x45D9F3B, truncate 64-бит), Bionic rand ≡ glibc random (signed int32 в init!); 16× `rand()&0xF` → hex-ключ; dwl: `out[36-i]=enc[i]^key[i%16]^0x5A`; паттерн ключа key[0:5]="76b9b", key[13:16]="08d" (баг: 15-й символ 'd' не путать с '0'); полный перебор 52^5 → единственный вход `kvErw` → флаг [FLAG].
- 2026-11-12 · lesson · `lessons/strange-winapi-hooks-dynamic-detours.md` · Windows RE (решено): MinHook-хуки (MessageBoxA/Process32FirstW/NextW), проверка через `SystemFunction033` (RC4) + детуры (mt19937 seed 0x1337, 0x1337*((buf^key)+0xAB0BA11)); инверсия блока по DWORD; NUL-ловушки и восстановление патента `call`ff 94...`.
- 2026-11-11 · lesson · `lessons/2026-11-11-re-zigzag-gpu-shader-rol-xor-chain.md` · RE hard: zigzag.exe — GPU-шейдерная проверка (GLFW/OpenGL 4.3): GLSL 430 фрагментный шейдер, ROL/ROR8-компоненты, формулы per-pixel; расшифровка путём инверсии выражений шейдера.
- 2026-11-11 · lesson · `lessons/2026-11-11-re-warmup-rol3-encrypted-string.md` · RE easy: warmup — ROL3 (`b=(b>>5)|(8*b)`) + strcmp со строкой из .rodata; реверс на трансформацию ввода; IDA-разведка по импортам.
- 2026-11-11 · lesson · `lessons/2026-11-11-re-asmython-pyinstaller-shellcode-xor-rol.md` · RE easy: asmython.exe — PyInstaller (onefile) + скрытый .pyc (обфускация имён); декомпиляция Python 3.12 через xdis; функция f1/f2/f3 = memcpy + XOR 0xCC + ROL7 + repe cmpsb; ловушка CRLF через PowerShell-пайп.
- 2026-11-23 · lesson · `lessons/ctf-network-protocol-ring-accept.md` · RE сетевая (продолжение 2026-11-15, accepted достигнут): сервер генеративен (`[2][id]` отдаёт любой блок); кадры `[u32 len][тело]`; кольцо accepted из 18 блоков пройдено решениями напрямую; клиент при подмене ответов падает (0xC0000005).
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