---
name: win-wsl-ctf-workbench
description: Рабочее окружение Windows+WSL для security-задач: паттерны команд PowerShell (curl.exe, System.IO, архивы, кодировки) и WSL (pip --break-system-packages, fpylll, пути /mnt/c, sudo), установка CTF-инструментов, типовые грабли и рецепты (ffmpeg, OCR, python-скрипты, фоновые задачи). Используй при подготовке и запуске любых команд в этом окружении.
---
# Windows + WSL CTF Workbench

Окружение задач: Windows x64, инструмент `Bash` исполняется через PowerShell; для Linux-тулинга — WSL с дистрибутивом (например, `kali-linux`). Большинство CTF-инструментов уже есть или быстро ставится. Пути ниже — относительные: «домашний каталог пользователя» = `C:\Users\<user>` и `/mnt/c/Users/<user>` в WSL.

## 1. Как запускать команды

- **PowerShell (основная оболочка)**: обычные команды (`cd`, `Get-ChildItem`, `python ...`) идут в Bash-инструменте напрямую. Учти: `&&` работает в PS7; при сомнениях используй `;`.
- **⛔ Жёсткий триггер для WSL-команд** (главная причина потерянных вызовов в полях): если команда содержит `$`, `>`, `|`, `&`, вложенные кавычки или длиннее одного простого вызова — **сразу пиши `.sh`/`.py` файлом (Write) и запускай `wsl -- bash /mnt/c/.../file.sh`**. Не чини экранирование инлайном: первая же ошибка кавычек = сигнал уйти на файл, а не вторая попытка. Ловушки PowerShell 5.1 (все реальные, из полевых треков):
  - `$var`, `$(...)`, `$1`, `$n` в двойных кавычках → PowerShell молча подставляет/съедает переменные bash;
  - `> file`, `2>/dev/null` снаружи `bash -c` → перехватывает PowerShell (пишет UTF-16 в несуществующий путь вида `C:\mnt\c\...`);
  - `| head/tail/grep/cut/wc`, `||`, `&&` снаружи `bash -c` → «not recognized» / «not a valid statement separator»;
  - вложенные кавычки `bash -c "...'...'..."` → syntax error у самого bash;
  - юникс-пайпы и редиректы живут ТОЛЬКО внутри `bash -c '...'` (или в файле).
- **WSL**: `wsl -d <дистрибутив> -- bash -lc '<команда>'`
  - установка пакетов: `wsl -d <дистрибутив> -- bash -lc 'sudo apt-get update && sudo apt-get install -y <pkg>'`
  - Python-пакеты: `wsl -d <дистрибутив> -- pip3 install --break-system-packages fpylll cysignals`
  - доступ к Windows-файлам: `/mnt/c/Users/<user>/...` (соответствует `C:\Users\<user>\...`)
- **Долгие задачи**: запускай в фоне (run_in_background/Task) и забирай через TaskOutput; не блокируйся на многочасовых процессах, веди параллельные линии.

## 2. PowerShell-рецепты (критично для точности)

- **HTTP**: только `curl.exe` (голый `curl` — алиас Invoke-WebRequest и ломает флаги/POST):
  - `curl.exe -s -i URL`
  - `curl.exe -s -X POST -H "Content-Type: application/json" -d "{\"a\":1}" URL`
  - куки: `-b "name=value"`, повторы: `-H "Cookie: ..."`.
- **Пайпы unix-утилит (`head`, `grep`, `cut`, `wc`) — только ВНУТРИ `bash -c '...'`**, не снаружи `wsl -- cmd | head` (PowerShell не знает head; снаружи рвётся обрезка вывода и `-o /dev/null`).
- **Сеть через локальный прокси** (реальность стенда): интернет ходит через `http_proxy`/`https_proxy`/`all_proxy` (обычно `127.0.0.1:<порт>`). Хосты задач доступны; произвольные внешние хосты могут отдавать `000`/timeout — **это норма среды, а не «нет интернета»**. Диагностика: `curl.exe -s -o NUL -w '%{http_code}' <хост-задачи>` против внешнего хоста; сравни с `--noproxy '*'`. **Внешние HTTPS надёжнее из WSL**: `wsl -d kali-linux -- bash -c "curl https://..."` — PowerShell-конвейер селективен (000), WSL-curl ходит (webhook.site, paste.rs, github).
- **Вебхук-приёмники для XSS/эксфильтрации**: не рассчитывай на сторонние сервисы (webhook.site/requestbin могут быть недоступны) — используй дроп-эндпоинты самой задачи, её API, или доступный хост инфраструктуры. Сначала проверь, ЧТО доступно, потом строй пейлоад.
- **TLS-перехват на стенде** (curl exit 60, git `schannel: SEC_E_UNTRUSTED_ROOT`): лечится `curl.exe -k` и `git config http.sslVerify false` (в каталоге репозитория).
- **Известные уязвимости по версии** (триггер — фингерпринт: `X-Powered-By`, баннер, заголовки; 30 секунд, до погружения в логику приложения). Полный офлайн-кэш CVE не ведём — точечные запросы:
  - NVD API 2.0: `curl -sk "https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=php+8.1" | python3 -m json.tool | findstr /i "cvelink description"` (без ключа ~5 запросов/30с);
  - точная запись CVE: `curl -sk https://cveawg.mitre.org/api/cve/CVE-2026-109618`;
  - GitHub Advisory (по продукту): `https://github.com/advisories?query=php`.
  Найденное фиксируй строкой в `knowledge-base/local/toolbox/vuln-notes.md` (продукт · диапазон версий · класс · ссылка) — это наш живой кэш. Прецедент: php2shell (см. `lessons/2026-10-22-php2shell-...`) — баннер PHP ≤ 8.1.x = pre-auth RCE.
- **Байты файлов**: `[System.IO.File]::ReadAllBytes("C:\...\file")`, запись: `[System.IO.File]::WriteAllBytes(...)`; hex: `Format-Hex`.
- **Архивы**: `Expand-Archive` (zip); rar — `unrar x`/WinRAR; 7z — `7z.exe`. **Проверяй сигнатуру** (zip может оказаться 7z/rar/дисковым образом/LUKS-контейнером).
- **Поиск/текст**: `Select-String -Encoding UTF8`, `where.exe`, `Get-Command`; для рекурсивного поиска — Python-скрипт.
- **Кодировки**: консоль может быть cp1251/cp866 — при кракозябрах выводи в файл с `-Encoding UTF8` и читай файл; Python запускай как `python -X utf8 script.py` и задавай `PYTHONIOENCODING=utf-8`; в скриптах открывай файлы с `encoding='utf-8', errors='replace'`.
- **Кириллица в путях/именах**: работай через Python или кавычки; не переименовывай вслепую.

## 3. Типовой инструментарий

- Обычно доступны: `python` (+numpy/scipy/PIL/opencv/pycryptodome), `ffmpeg`/`ffprobe`, `node`/`npm`, `git`, `openssl`.
- Часто доустанавливается:
  - WSL: `binwalk`, `exiftool`, `tesseract-ocr`, `zbarimg`, `steghide`, `unrar`, `pngcheck`, `sox`, `sleuthkit`, `mtools`, `foremost`, `volatility3`, `fpylll`, `flint` (тяжёлые: `sagemath`).
  - Windows: `pip install --user pillow numpy scipy pycryptodome ggwave` и пр.
- **ffmpeg** — рабочая лошадка медиа-стего: кадры (`-vf select='eq(n\,123)'`), статистика сигнала (`-vf signalstats,metadata=print`), спектрограммы (`-lavfi showspectrumpic`), фильтры (`fps`, `scale`).
- **OCR**: tesseract в WSL; на Windows — WinRT OCR через PowerShell или ручной ASCII-рендер глифов.

## 4. Типовые грабли (проверено на практике)

1. `curl` без `.exe` тихо меняет поведение — всегда `curl.exe` для точного воспроизведения.
2. Долгие прогоны тяжёлых скриптов → ставь лимиты и сохраняй промежуточные JSON; не пересчитывай всё заново.
3. `fpylll`/`flint` без `gram='exact'` могут молча отказывать на больших числах — задавай точно.
4. Кириллица и JSONL: используй Python-обработку в UTF-8 (PowerShell показывает mojibake).
5. Дубликаты имён (распаковка с `(1)`) и пробелы в именах — бери в кавычки.
6. В WSL может не быть `sudo` без пароля — сначала проверь (`sudo -n true`); иначе ставь в user-space (`pip install --user`).
7. Windows Defender может тормозить/блокировать инжекторы (frida и т.п.) — предупреждай пользователя о рисковых действиях.
8. Фоновые процессы: фиксируй PID и выходные файлы (`Start-Process -PassThru`, `nohup` в WSL), убивай зомби.

## 5. Организация работы

- **Рабочий каталог сессии** (выданный платформой/пользователем): складывай туда скрипты (`solve_*.py`), выгрузки (`*_out.txt`), промежуточные артефакты.
- Веди `STATE.md` (цель / факты / гипотезы / следующий шаг) — при лимитах он спасает прогресс; обновляй после каждого важного вывода.
- Тяжёлые выгрузки (дампы, кадры, спектрограммы) — в подкаталоги (`frames/`, `audio/`), не заваливай корень.
- Перед длинным прогоном: оценка времени, лог в файл, чекпойнты каждые N итераций.
- Исходные материалы пользователя **не перезаписывай** — работай на копиях.