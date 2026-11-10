# 2026-11-01 — Windows reverse: VM-протектор и патч VMMCALL-fallback

Источник: задача с платформы — НЕ доведена.

## Сюжет
- Игра (Windows PE) использует VM: `VMMCALL` с `rcx="BALVHBCC"`, `rdx=команда`,
  возврат проверяется через `rax`; если 0 → fallback (данные `[rip+…]`).
- Нужно понять протокол VM, восстановить «настоящий» код/флаг.

## Практические приёмы
1. **Сопоставление BAD_OPCODE**: если VM-диспетчер ругается на opкод — найди Xrefs на строку
   `BAD_OPCODE` → это диспетчер; читай таблицу обработчиков.
2. **Патчинг бинарника** по месту для обхода веток (например, заставить VMMCALL всегда
   «успешно» через NOP/`jmp` на fallback-путь); НО:
   - `movabs rcx, 0x43434248564C4142` кодируется как immediate **8 байт LE** — при поиске
     байт-паттерна пиши именно 8-байтовый LE (а не 4-байтовый).
   - После патча проверь количество замен: `patched sites: 8` — критерий успеха.
3. **Accounts**: если `rax=0` — fallback; если `rax!=0` — штатный путь. Это ключевая развилка.
4. **Дампинг/профиль**: `memdump.py` из сессии помог найти константы/строки в памяти.

## Среда: типовые ошибки (эта машина)
- Нет `pefile`/`capstone`/`jsbeautifier` в Windows-Python → `pip install pefile capstone jsbeautifier`.
- `ls -la`/`find` не работают (это PowerShell) → `Get-ChildItem`, `Glob`/`Grep` тулы.
- WSL есть; но для Windows-PE-анализа удобнее Windows-инструменты (pefile/capstone ставятся
  через pip --break-system-packages). localhost из WSL2 — через адрес хоста.
- WebFetch не читает `.js`/статику — цитируй только страницы, не ассеты.
- Read-тул требует `file_path` — отсутствие → `missing required property "file_path"`.

## Артефакты (архив)
- `archive/` — zip, exe, `patch_vmm_fallback.py`, `memdump.py`, `peinfo.py`
  (не создан — pefile), `cmd-output/` (много пустых файлов — не читать без проверки).
