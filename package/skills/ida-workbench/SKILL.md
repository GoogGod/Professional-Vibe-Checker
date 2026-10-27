---
name: ida-workbench
description: Используй этот скилл, когда дан бинарник (ELF/PE) и нужен headless-реверс через IDA Pro (idat64 + IDAPython): recon-сегменты/импорты/строки/функции, декомпиляция по имени или адресу, xrefs к строке, патчи в IDB, экспорт данных. Применяй вместо GUI-анализа.
---
# IDA Workbench — реверс как tool-call

IDA запускается headless и управляется IDAPython-скриптами: агент пишет скрипт, вызывает `idat64`, читает файл-результат. Декомпилятор Hex-Rays доступен из коробки.

## 1. Вызов (проверенный паттерн)

PowerShell (рабочий каталог — любой, пути абсолютные):

```powershell
$w = '<WORKDIR>'
& 'C:\Program Files\IDA 7.7\idat64.exe' -A "-S$w\ida_script.py" "-L$w\ida.log" "$w\target.bin"
# $LASTEXITCODE == 0; результат — файл(ы) в $w, читай их напрямую
```

Железные правила IDAPython-скрипта:
- `import idaapi, idautils, idc` (+ `ida_hexrays` для псевдокода);
- первым делом `idaapi.auto_wait()` — иначе запросы по недоанализированной базе;
- вывод — ТОЛЬКО в файл (stdout в batch-режиме не читается);
- завершение — `idc.qexit(0)`;
- параметры скрипту — через JSON/текст-файл рядом (`params.json`), не через argv.

## 2. Шаблон recon.py — первый заход на любой бинарник

```python
import json, idaapi, idautils, idc, ida_nalt
idaapi.auto_wait()
P = json.load(open(r'<WORKDIR>\params.json'))  # {"minlen": 6}
out = open(r'<WORKDIR>\ida_recon.txt', 'w', encoding='utf-8')
out.write('file=%s ida=%s\n' % (idc.get_input_file_path(), idaapi.get_kernel_version()))
out.write('proc=%s bits=%d\n' % (idc.get_inf_attr(idc.INF_PROCNAME), idc.get_inf_attr(idc.INF_LFLAGS) & 0x100 and 64 or 32))
out.write('\n[SEGMENTS]\n')
for s in idautils.Segments():
    out.write('%s %x-%x %s\n' % (idc.get_segm_name(s), s, idc.get_segm_end(s), idc.get_segm_attr(s, idc.SEGATTR_PERM)))
nimps = ida_nalt.get_import_module_qty()
out.write('\n[IMPORTS] modules=%d\n' % nimps)
for i in range(nimps):
    m = ida_nalt.get_import_module_name(i)
    def cb(ea, name, ord): out.write('%s!%s\n' % (m, name or ord)); return True
    ida_nalt.enum_import_names(i, cb)
out.write('\n[EXPORTS/ENTRY]\n')
for i in range(ida_nalt.get_entry_qty()):
    ord_ = ida_nalt.get_entry_ordinal(i)
    out.write('%x %s\n' % (ida_nalt.get_entry(ord_), ida_nalt.get_entry_name(ord_)))
out.write('\n[FUNCTIONS] count=%d\n' % len(list(idautils.Functions())))
for ea in idautils.Functions():
    out.write('%x %s\n' % (ea, idc.get_func_name(ea)))
out.write('\n[STRINGS >= %d]\n' % P.get('minlen', 6))
for st in idautils.Strings():
    try:
        if len(str(st)) >= P.get('minlen', 6):
            out.write('%x %r\n' % (st.ea, str(st)))
    except Exception:
        pass
out.write('\n[CRYPTO_CONSTANTS]\n')
for name, pat in [('TEA/XXTEA', b'\xb9\x79\x37\x9e'), ('MD5/SHA1-init', b'\x01\x23\x45\x67'),
                  ('SHA256-init', b'\x67\xe6\x09\x6a'), ('CRC32', b'\x20\x83\xb8\xed'),
                  ('SHA1-K', b'\x99\x82\xa5\x5a'), ('AES-Sbox', b'\x63\x7c\x77\x7b')]:
    ea = idaapi.find_binary(0, idc.BADADDR, ' '.join('%02x' % b for b in pat), 16, 1)
    if ea != idc.BADADDR:
        out.write('%s @ %x\n' % (name, ea))
out.close()
idc.qexit(0)
```

Читай `ida_recon.txt` и решай, что декомпилировать.

## 3. Шаблон decompile.py — псевдокод по имени/адресу

`params.json`: `{"targets": ["main", "check_*", "0x401000"], "max_funcs": 30}` (поддерживается `*`-маска имени).

```python
import json, fnmatch, idaapi, idautils, idc, ida_hexrays
idaapi.auto_wait()
P = json.load(open(r'<WORKDIR>\params.json'))
ok = ida_hexrays.init_hexrays_plugin()
out = open(r'<WORKDIR>\ida_decomp.txt', 'w', encoding='utf-8')
out.write('hexrays_available=%s\n' % ok)
targets, chosen = P.get('targets', []), []
for ea in idautils.Functions():
    n = idc.get_func_name(ea)
    for t in targets:
        if (t.startswith('0x') and int(t, 16) == ea) or fnmatch.fnmatch(n, t if '*' in t else t + '*'):
            chosen.append((ea, n)); break
for ea, n in chosen[: P.get('max_funcs', 30)]:
    out.write('\n===== %x %s =====\n' % (ea, n))
    try:
        out.write(str(ida_hexrays.decompile(ea)))
    except Exception as e:
        f = idaapi.get_func(ea)
        a = f.start_ea if f else ea
        while a < (f.end_ea if f else a + 0x100):
            out.write('%x  %s\n' % (a, idc.generate_disasm_line(a, 0)))
            a = idc.next_head(a)
out.close()
idc.qexit(0)
```

## 4. Шаблон xrefs.py — кто использует строку/функцию

`params.json`: `{"needle": "Correct", "addr": "0x401000"}` — ищет строку по подстроке или точный адрес; выводит ссылки + контекст дизассма ±4 строки. Ключевой приём реверса: нашёл строку-подсказку → смотри функцию рядом (сравнение/проверка).

```python
import json, idaapi, idautils, idc
idaapi.auto_wait()
P = json.load(open(r'<WORKDIR>\params.json'))
out = open(r'<WORKDIR>\ida_xrefs.txt', 'w', encoding='utf-8')
addrs = []
if P.get('addr'):
    addrs.append(int(P['addr'], 16))
for st in idautils.Strings():
    if P.get('needle') and P['needle'] in str(st):
        addrs.append(st.ea)
for a in addrs:
    out.write('\n=== %x ===\n' % a)
    refs = list(idautils.CodeRefsTo(a, 0)) or list(idautils.DataRefsTo(a))
    for r in refs:
        out.write('ref from %x (%s)\n' % (r, idc.get_func_name(r)))
        for d in range(max(0, r - 16), r + 32):
            line = idc.generate_disasm_line(d, 0)
            if line:
                out.write('  %x  %s\n' % (d, line))
out.close()
idc.qexit(0)
```

## 5. Практика и грабли

- ELF из WSL/Linux-части — сначала скопируй файл на Windows-сторону в рабочий каталог.
- Паковка (UPX и др.) — распакуй до IDA (`upx -d`), иначе recon покажет мусор.
- `.NET`-сборки IDA почти бесполезна — это случай для dnSpy/ILSpy (вне пакета).
- Рядом с бинарником плодится `*.i64`-кэш — это нормально, ускоряет повторные прогоны; для чистого пересоздания удали `.i64`.
- Подозрительные Windows-цели не запускать на хосте; динамика — только в изолированной VM.
- Долгий анализ больших бинарников: сначала recon (секунды–минуты), потом точечная декомпиляция 5–30 функций, а не «всё сразу».

## 6. Сетап с нуля (если чистая машина)

1. IDA Pro 7.7 x64 установлена (лицензия принята одним запуском GUI).
2. Python 3.9 x64 (например, `winget install Python.Python.3.9`); Store-Python 3.12 не подходит.
3. Реестр: `HKCU\Software\Hex-Rays\IDA\Python3TargetDLL` = путь к `python39.dll`.
4. Для PyQt5 в GUI — `idapyswitch.exe` от администратора; headless-режиму это не требуется.
