# Урок: ext4 «файлы удалены, папки остались» — карвинг gzip из unallocated

Дата: 2026-10-23 · Категории: forensics/fs, forensics/crypto · Уровень: easy

## Кейс

- Образ 2 МБ, ext4. `fls -rp` показал только папки + `$OrphanFiles` (удалённые inode). `istat`: у удалённых inode **size=0 и пустые Direct Blocks** (extents стёрты при удалении) — `icat` даёт 0 байт. Путь «вытащить по иноду» закрыт.
- Рабочий путь: `blkls` → выгрузить unallocated → `binwalk` нашёл 4 gzip-потока с **FNAME-заголовками** (`flag.odt`, `flag.png`, `flag.txt` ×2 разных версий). Имена и типы восстанавливаются прямо из gzip-заголовка — даже когда directory entries стёрты.
- Извлекать потоки: python `zlib.decompressobj(16+MAX_WBITS)` по смещению из binwalk (считает `unused_data` → реальную длину потока). **Не `dd bs=1`** — на мегабайтных блоках виснет намертво (>3 мин, убит).
- Crypto-цепочка в одном из файлов (приманка-близнец была рядом): base32 (без `=`, паддинг дополнить) → внутри base64 → внутри tar (`ustar`-заголовок читается в base64 как `MDAwMDY0NE...`) → `flag.txt.gz` → gunzip → флаг.
- Приманки-маркеры формата: соседний файл со строкой `Not<Формат>{...}` подтвердил формат флага до расшифровки основного; ODT с «NO FLAG» и чистый PNG — шум. Проверяй все восстановленные файлы, флаг — в самом «многослойном».

## Команды-якоря

- `fls -rp img` / `istat img <inode>` — если Direct Blocks пуст, icat бесполезен
- `blkls img > unalloc.bin; binwalk unalloc.bin`
- python: `zlib.decompressobj(16+zlib.MAX_WBITS).decompress(blob[off:])`
- base32 без паддинга: `s + "=" * ((8 - len(s) % 8) % 8)`

## Связь с базой

- Дополняет host-artifacts-playbook §4 (FAT-кейс): для ext4 directory entries после удаления не восстановить — уповай на данные в unallocated и journal.
