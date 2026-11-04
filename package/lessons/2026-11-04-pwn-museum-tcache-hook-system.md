# PWN: tcache poisoning → __free_hook = system (heap menu, no PIE)

Суть: меню работы с объектами на куче (add/edit/inspect/remove). Каждый
объект: `malloc(0x18)` → `[name*][desc*][tag]`; name=`malloc(0x40)`,
desc=`malloc(1..0x100)`. `edit` делает `read_str(desc, 0xff)` — переполнение
кучи (затирает следующий чанк). `inspect` печатает `8` байт по `desc`
(произвольное чтение после подмены). No PIE, partial RELRO.

## Цепочка
1. `add A` (desc=`/bin/sh\0`, size=0x40), `add B` (size=0x40).
   Layout: `[objA][nameA][descA 0x50][objB][nameB][descB]`; из user-descA:
   +0x40 prev_size, +0x48 size(objB=0x20), +0x50 userB->name, +0x58 userB->desc.
2. Heap overflow из descA: payload = `CMD + padding до 0x40 + prev_size +
   p64(0x20) + p64(nameB) + p64(descB)` (ровно 0x60 байт).
3. Подмена `descB = puts@GOT` → inspect B → утечка puts → `libc_base`.
4. Подмена `descB = __free_hook` → edit B пишет `system` в hook (подтвердить
   readback'ом через inspect: ожидание 0).
5. `remove A` → `free(descA) = system(CMD)` → вывод флага.

## Ключевые ловушки
1. `read_str(desc)` читает максимум `0x3f` байт: команда для system()
   обязана быть ≤ 63 байт; длиннее — мусор в stdin → «Unknown option».
2. Вывод `system()` читать напрямую из сокета (`setblocking(False)` + цикл
   recv), а не через буферизованные обёртки — иначе «вывод молчит» и
   фантомный `": "`.
3. No PIE: адреса GOT статичны (0x602020…) — удобная мишень для leak.
4. Оффсеты libc проверять readback'ом hook ДО записи (ожидание 0).

## Ретроспектива (почему «спотыкались»)
- Двухэтапная подмена не приходила сразу: сначала думали «лечь» в name,
  потом поняли — надо менять desc соседнего объекта через overflow.
- Получив `/bin/sh` через `system`, упирались в интерактив: писать по
  одной команде за запуск (`system("ls")`) надёжнее, чем шелл.
- Десятки версий скриптов (t*, mini*, diag*, hexflow*) вместо эволюции
  одного — та же задача решалась локально 10 минутами, но «слепые»
  попытки на remote затягивали.
