# БОЕВОЙ РЕГЛАМЕНТ быстрого старта (проверка «сложная задача»)

Цель: **максимум 2 часа** от получения задачи до ответа (флаг/решение).
Если решение занимает ~3 часа — это считается провалом. Ниже — порядок,
инструменты и «чеклист граблей» для каждой категории.

## 0. Общие правила (30 сек)
- Работать в WSL: `wsl -d kali-linux`, Python = `/home/immortal/ctfenv/bin/python`.
- Пароль/токены — никогда в код и репо.
- Результат каждого шага — коротко в `log_local.md` (в каталоге задачи).
- Не менять системные файлы. Флаг → сразу в `FLAG.txt` + отчёт.

## 1. Триаж (первые 15 минут — ОБЯЗАТЕЛЬНО)

| Шаг | Команда/инструмент | Что выясняем |
|---|---|---|
| тип файла | `file *` | ELF/PE/APK/PCAP/zip/скрипт |
| защита | `checksec --file=chall` | PIE/NX/Canary/RELRO |
| строки | `strings -n 6` | подсказки, пути, имена функций |
| импорты | `objdump -T` / `readelf --dyn-syms` | какие libc-функции (GOT) |
| баннер/сервис | `nc <host> <port>` | протокол, меню, подсказки |
| размер/формат | `xxd`, `binwalk` | для файлов (не бинарников) |

**Решение за 15 минут:** если видно «простое» (fmtstr+overflow, ROP с феопен, XOR-строки, индексация) — сразу писать эксплойт по шаблону (см. §3).

## 2. Маршруты по категориям

### PWN (самый вероятный тест)
1. `checksec` → если NO PIE + Partial RELRO: GOT-перезапись, ret2libc.
2. `objdump -d` найти уязвимую функцию (fgets/gets/scanf/printf/strcpy).
3. Локально: `gdb -q ./chall`, брейкпоинт на printf → посмотреть стек (`x/40gx $rsp`).
4. Шаблон: `templates/pwn_fmtstr_rop.py` (см. ниже) — адаптировать.
5. Leak libc → `one_gadget`/`ROPgadget --binary` → шелл.
6. Грабля: **RET-выравнивание** (rsp%16) перед system/movaps → добавить RET-гаджет.
7. Грабля: alarm(60) → всё в одном соединении (ret2vuln).

### RE
1. `r2 -A ./chall` / `objdump -d` → найти main/func.
2. Если виртуальная машина/байткод: искать интерпретатор.
3. Строки + Xrefs (r2: `axt @ sym.str...`).
4. Если сложный алгоритм: `angr` (символьное исполнение) или `unicorn` (эмуляция).
5. Грабля: **лишние проверки/ловушки** — не доверять первому «простому» пути.

### Crypto
1. `strings` + типы (RSA/DH/AES/stream).
2. Определить уязвимость: маленький e/секрет → BSGS; oracle → padding; nonce reuse → many-time pad.
3. Скрипты: `~/ctfenv/bin/python` (Crypto, z3, numpy).
4. Грабля: signed/unsigned, 32/64-bit, байтовый порядок.

### Web
1. `curl -v`, `sqlmap`, `ffuf -w <wordlist>`.
2. Смотреть cookie/заголовки, IDOR, SSTI, SSRF, JWT (алгоритм confusion).
3. Грабля: не пропускать скрытые параметры/эндпоинты.

### Forensics
1. `binwalk`, `tshark -r`, `strings`, `xxd`.
2. Если PCAP: `tshark -r file.pcapng -Y "http"`, извлечь объекты (`tshark --export-objects`).
3. Если память: `vol -f mem.dmp` (volatility3).
4. Если stego: `steghide`, `zsteg`, анализ LSB.

### Hardware/IoT
1. MQTT: `mosquitto_sub` / python paho; брут кредов (CONNACK 0x00/0x86).
2. Прошивки: `binwalk -e`, извлечение файловой системы.
3. FPGA/Verilog: симуляция, поиск уязвимых модулей.

## 3. Шаблоны быстрых эксплойтов (лежат в `templates/`)
- `pwn_fmtstr_rop.py` — fmtstr-лак + GOT-перезапись + ret2libc.
- `pwn_ret2libc_rop.py` — простой ROP (без канарейки).
- `pwn_heap_house.py` — tcache/fastbin-poison (каркас).
- `rev_angr_solve.py` — поиск «правильного» ввода (angr/SymbolicExecution).
- `crypto_oracle_bsgs.py` — маленький секрет / BSGS.
- `web_ffuf_scan.sh` — фаззинг эндпоинтов.

## 4. Кнопки быстрого старта
```bash
cd <task_dir>
export PATH="$HOME/.local/bin:$PATH"
alias ctpy="$HOME/ctfenv/bin/python"
ctpy /mnt/c/.../tools/triage.py chall    # авторазведчик
```

## 5. Проверка «я потратил не больше 2 часов»
- T+0:00 задача получена
- T+0:15 триаж завершён, гипотеза сформулирована
- T+0:45 первая версия эксплойта/решения локально
- T+1:30 remote-прогон, минимум 2 попытки
- T+2:00 финал (флаг/отчёт) — **критерий успеха**
