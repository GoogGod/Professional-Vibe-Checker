# 2026-11-01 — Память/forensics: базовый разбор дампа (Volatility 3)

Источник: задача с платформы — начат, не доведён.

## Профилирование
- Linux: `vol -q -f <mem> banner` → «Windows 10 x64 (19041)» и т.п.
- Основные плагины vol3: `windows.pstree` (дерево процессов), `windows.filescan`
  (файлы, включая удалённые), `windows.cmdline`, `windows.pslist`, `windows.dumpfiles`
  (выгрузка найденного), `windows.registry.userassist`, `windows.malfind`.
- Ищи нетипичные процессы (то, что открыто пользователем) и флаг/имя файла
  в cmdline/filescan.

## Среда и ошибки
- WSL доступен (см. win-wsl-ctf-workbench): vol3 запускается и в WSL (python3 + pip
  --break-system-packages), и на Windows. Вывод с кириллицей из `wsl` иногда бывает UTF-16
  («w s l : ...») — читай через `iconv -f UTF-16 -t UTF-8` или запускай `wsl bash -lc "..."`
  с корректной кодировкой.
- pstree: не пугайся «нерешаемых» WSL-ошибок — они в основном про сеть, для файла-дампа
  работают.
- При задаче «Был флаг, рассыпался/удалился»: активно ищи в `filescan` **удалённые**
  файлы и их выгрузку, в `cmdline` — нетипичные пути, в `userassist` — запуск
  «блокнота»/архиватора.

## Артефакты (архив)
- `puzzle.zip.opdownload`, `puzzle.vmem` (дамп), `scan_fs.json`, `pslist.json`,
  `vol_scan_*.py`, `wsl_*.sh` (ошибочные), `output_*.txt` (результаты плагинов).
