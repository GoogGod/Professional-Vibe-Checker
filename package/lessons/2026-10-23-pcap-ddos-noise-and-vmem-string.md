# Урок: поиск уникального в шуме (pcap DDoS) и строка в дампе памяти (vmem)

Дата: 2026-10-23 · Категории: forensics/pcap, forensics/memory · Уровень: easy

## Кейс A — pcap с DDoS-шумом («найти хакера»)

- Дамп 82 МБ / 29k пакетов: ~1000 однотипных HTTP GET от `python-requests` к 5–6 эндпоинтам API (имитация DDoS), все ответы 200.
- Приём: агрегировать `ip.src + method + uri` через `sort | uniq -c | sort -rn` — шум даёт сотни повторов, а действия атакующего видны как строки со счётчиком **1**. Там оказались единичные `GET /api/login?username=...&password=<флаг urlencoded>` и `GET /api/get_flag`.
- Ловушка: эндпоинт `/api/get_flag` вернул явную приманку `No<format>{not_a_flag}` — реальное значение было в **параметре запроса** login (URL-декодировать `%7B%7D`). Не доверять «подарочным» эндпоинтам, проверять обе стороны транзакции (`follow,tcp,ascii`).

## Кейс B — дамп памяти VMware (.vmem, 1 ГБ), «шпион спрятал флаг»

- До volatility3: быстрый `grep -aob "PolyCTF"` по сыром дампу — единственный ASCII-хит на смещении ~0x9090000, рядом читаемая строка формата `Format{...}` (leetspeak-подтверждение темы «search string inside vmem»). UTF-16LE-хитов не было.
- Грабли bash: паттерн с `\x00` через `$'...'` **невозможен** — аргумент обрезается на первом NUL, grep молча ищет только `P`. UTF-16LE-поиск — только python (`pat.encode('utf-16-le')` + блочное чтение).
- Вывод: для easy-задач «флаг в памяти» raw-grep быстрее и надёжнее полного волатильности-пайплайна; volatility — когда строк нет (процессы, filescan, history).

## Команды-якоря

- `tshark -r x.pcapng -Y http.request -T fields -e ip.src -e http.request.method -e http.request.uri | sort | uniq -c | sort -rn`
- `tshark -r x.pcapng -q -z follow,tcp,ascii,<stream>`
- `grep -aob "Prefix" dump.vmem` → python: seek(offset), regex `Prefix\{[^}]{0,200}\}`
