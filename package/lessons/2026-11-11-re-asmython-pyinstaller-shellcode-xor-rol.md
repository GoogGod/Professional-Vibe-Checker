# RE easy: asmython.exe — PyInstaller + самодельный shellcode (XOR/ROL + memcmp)

Дата: 2026-11-11. Категория: reverse (easy). Платформа: обобщённо.

## Суть
exe = PyInstaller (onefile, Python 3.12, статический bootloader без импортов). Скрытый скрипт `payload_obf.pyc` обфусцирован: имена переменных/функций — случайные base64-подобные строки. Логика: три ассемблерные функции (base64-константы в модуле) выделяются в исполняемую память (Windows: VirtualAlloc PAGE_EXECUTE_READWRITE + memmove; Linux: mmap PROT_EXEC) и вызываются через ctypes.CFUNCTYPE.

## Ключевые приёмы
- PyInstaller: найти cookie `MEI\x0c\x0b\x0a\x0b\x0e` в конце файла; распаковка — `pyinstxtractor-ng` (pip), entry point `boot.pyc`; главное — `payload_obf.pyc`.
- Декомпиляция Python 3.12: `xdis.disasm.disassemble_file` (дизассемблер, не декомпилятор) — достаточно для восстановления логики.
- Шаблон: `import base64, ctypes, mmap, os` + `CFUNCTYPE` + `VirtualAlloc`/`mmap` = self-modifying/машинный код; decode base64 и дизассемблируй (objdump -b binary -m i386:x86-64).
- Функции: f1 = memcpy + XOR 0xCC по каждому байту; f2 = ROL 7; f3 = `repe cmpsb` (равенство). Флаг: `s[i] = ror(data[i],7) ^ 0xCC`.
- Ловушка запуска: передача ввода через PowerShell-пайп добавляет CRLF → длина != 41 → «NO». Запуск — через Python subprocess с точными байтами.

## Вывод
Флаг → [FLAG] (41 символ, DUCKERZ{...}).

## Анти-деанон
Без названий площадок/доменов/имён. Флаг → [FLAG].
