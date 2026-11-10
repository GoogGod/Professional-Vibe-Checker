# PWN: heap overflow + частичная перезапись vtable (небольшой объект)

Задача: «Рюкзак» (площадка, pwn medium — C++). Решено: флаг `[FLAG]`.

## Бинарник
- C++ (std::cin/cout, `operator new`), ELF64. `Toy`-объекты по 0x28 байт:
  `[vptr 8][name 32]`; глобальный массив указателей `ruckzak[16]`.
- Меню: 1 — add_toy, 2 — edit_toy, 3 — show_toy.
- `add_toy`: `place < 16`; `scanf("%30s", name)`; `Toy *t = new(0x28)`; `ruckzak[place]=t`.
- `edit_toy`: вызывает второй метод vtable — `(*(vtbl+8))(obj)` → перезапись name
  **без ограничения длины** (классический heap overflow в соседний чанк).
- `show_toy`: вызывает первый метод vtable — `(*vtbl)(obj)` → Display.

## Уязвимость и эксплойт
1. Создай toy0 и toy1 (соседние чанки 0x28).
2. edit toy0 payload: `b'X'*0x28 + b'\x30'` — перезапись **младшего байта**
   vtable toy1 на 0x30 (vtable toy1 указывала на 0x50; 0x30 = 0x50 − 0x20).
3. show toy1 → первый метод vtable теперь указывает в соседнюю запись vtable
   (на 0x20 раньше) → `Flag::Display` → `system("cat flag")` → флаг.

## Как находить vtable-методы
- IDA headless (`ida-workbench`): декомпиляция `add/edit/show_toy`, методов `Toy::*`;
  ищи вызовы `system("cat flag")` (в функции `Flag::Display`).
- `elf_scan.py`: разбор секций ELF, поиск qword `0x179c` (адрес `Flag::Display`)
  в `.data.rel.ro`; дамп `.data.rel.ro` qword'ами — увидишь соседние vtable-записи
  (Toy/Item/Flag) и смещения 0x20/0x28/0x30.

## Ключевые точки внимания
- **Частичная перезапись vtable** — меняй только младший байт (нет PIE/ASLR
  разница 0x10–0x50) — компактнее, проще, стабильнее полного указателя.
- При edit **не добавляй `\n`** после payload: `read()` пишет ровно байты;
  перевод строки уходит в меню (см. урок `menu-read-getc-newline-trap`).
- Локальная проверка до remote: `exploit_local.py` (subprocess, select recv)
  флагу «example_flag»; заглушка на сервере — `[FLAG]` (не путать).

## Артефакты
- Рабочие скрипты сессии: elf_scan.py, inspect.py, exploit_local.py, exploit_remote.py,
  ida_decomp.txt, ruckzak.i64, flag (локальная заглушка).
