---
name: ad-rehearsal
description: Используй этот скилл за день до Attack/Defense-турнира или сразу после изменений в farm/watch/эксплойтах, чтобы прогнать всю боевую связку на локальном мок-жюри: молотилка крадёт и сдаёт флаги, вахтёр видит статусы и дренаж, Volga-петля тренируется патчем и откатом. Также применяй, если скрипты кита ведут себя странно на реальном API — стенд ловит те же ошибки.
---
# Предбоевая репетиция A/D (mock_jury)

Файлы кита: `toolbox/ad/` → `farm.py`, `watch.py`, `mock_jury.py`, `README.md`. Только stdlib Python 3, без сети и жюри.

## Когда (триггеры)

- За день до турнира — обязательный ритуал (входит в preflight скилла `attack-defense-ctf`).
- После любого изменения `farm.py` / `watch.py` / контракта эксплойта.
- При подозрении на поломку связки перед боем: стенд воспроизводит ту же ошибку за минуту.

## Шаги (чек-лист)

1. [ ] Развернуть стенд: `python3 mock_jury.py &` → ожидаем строку `mock jury up: :8020 jury, :8021 notes, :8022 vault; token=mock-token; мы = 127.0.0.7`.
2. [ ] Собрать рабочую папку репетиции: копия `farm.py`/`watch.py`/`mock_jury.py`, `token.txt` = `mock-token`, эксплойты `exploits/exploit_notes.py` и `exploit_vault.py` (контракт `SERVICE/PORT/exploit(host,port,hints)`).
3. [ ] Запустить ферму и вахтёра с env: `AD_JURY=http://127.0.0.1:8020`, `AD_MY_IP=127.0.0.7`, `AD_TOKEN_FILE=<абс.путь>/token.txt`; в фоне с логами на диск.
4. [ ] Дать 3–5 раундов (раунд = 10 с) → проверить логи:
   - `farm.log` содержит `FLAG!` и `SUBMIT … Flag accepted! Earned 100 flag points!`;
   - `watch.log` тикает `round=N … notes=OK vault=OK`, счёт растёт;
   - нет `exploit err`, нет `Flag is too old` в большом объёме.
5. [ ] **Учение Volga** (руками, через curl): `POST /admin/patch {"service":"notes"}` → в течение раунда watch алертит `CORRUPT`; затем `POST /admin/rollback` → `OK`. Отрабатываем рефлекс «откат → статус».
6. [ ] **Балласт**: переименовать `exploit_notes.py` → рестарт фермы → ферма продолжает жить на vault, в логе `RETIRE?`-подсказка для notes.
7. [ ] Поднять стенд на своём боевом API (замена AD_JURY на реальный) → прогнать 1 цикл перед открытием сети: проверка токена, формата флага (`FLAG_RE`), лимитов.

## Эталоны вывода (валидация)

- Сабмит-ответ: `Flag accepted! Earned 100 flag points!` (не `Invalid`, не `too old`).
- Вахтёр при патче: `ALERT! MY SERVICE notes -> CORRUPT`.
- scoreboard мока: у `127.0.0.7` растёт `score_display`, у всех `status_name=OK`.

## Готча (довушки) — из реального дебага

- **Локальный прокси**: urllib на Windows упирается в системный прокси → `502 Bad Gateway` на `127.0.0.1`. Лечение: `no_proxy=127.0.0.1,localhost` или `urllib.request.ProxyHandler({})`.
- **Старые процессы**: перед стартом убить прошлые `python mock_jury/farm/watch` (иначе старый jury без сервисных портов — `netstat -ano | findstr ":802"`).
- **BOM**: PowerShell `Set-Content` пишет UTF-8 с BOM → `import` падает. Писать скрипты без BOM; проверять `ast.parse(open(f, encoding='utf-8-sig').read())`.
- **Порты молчат**: если слушается только `:8020` — `main()` крутит `serve_forever` последовательно; нужен thread на каждый сервер.
- **CRLF**: пароль/токен из файла режет сравнение → `tr -d '\r\n'`.
- **env не передаётся**: `Start-Process`/демоны не наследуют `$env:` — задавать переменные внутри команды запуска.

## Связки

- Полный боевой контекст — скилл `attack-defense-ctf`.
- Разбор прошедшего турнира и ранбук соло-топ-1 — урок `lessons/2026-10-25-ad-solo-top1-runbook.md`.
- Молотилка/вахтёр общего назначения — `toolbox/ad/README.md`.
