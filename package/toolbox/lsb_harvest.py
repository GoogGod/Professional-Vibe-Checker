#!/usr/bin/env python3
"""lsb_harvest.py — слепой перебор параметров LSB-извлечения (PNG/BMP, 24/32-bit).

Нейросеть не «видит» закономерности в бит-плоскостях — этот скрипт превращает
их в числа: перебирает комбинации (порядок пикселей, порядок каналов, номер
бита, порядок битов) и ранжирует по доле печатаемых символов + magic-паттернам.
Верхние строки вывода = кандидаты на payload; их hexdump отдаётся модели.

Использование:
  python3 lsb_harvest.py carrier.png                 # режим перебора (top-10)
  python3 lsb_harvest.py carrier.png --show 3        # hexdump топ-3
  python3 lsb_harvest.py carrier.png --runs          # метрика серий по плоскостям
  python3 lsb_harvest.py carrier.png --extract row,RGB,0,lsb,4096 > out.bin
Параметр --extract: порядок(row|col),каналы(RGB|BGR|G|R|B),бит(0-3),порядокбитов(lsb|msb),длина
"""
import sys
from PIL import Image

MAGICS = [b'PK\x03\x04', b'\x89PNG', b'GIF8', b'%PDF', b'\x7fELF', b'BM',
          b'\xff\xd8\xff', b'Rar!', b'7z\xbc\xaf', b'flag', b'FLAG', b'CTF{']

def gen_bits(px, w, h, order, chperm, bit, msb_first):
    """Генератор битов по выбранному порядку пикселей и каналов."""
    coords = []
    if order == 'row':
        coords = ((x, y) for y in range(h) for x in range(w))
    elif order == 'col':
        coords = ((x, y) for x in range(w) for y in range(h))
    for x, y in coords:
        p = px[x, y]
        for ch in chperm:
            b = (p[ch] >> bit) & 1
            yield b

def take_bytes(bitgen, n, msb_first):
    out = bytearray()
    acc = 0
    cnt = 0
    for b in bitgen:
        if msb_first:
            acc = (acc << 1) | b
        else:
            acc |= b << cnt
        cnt += 1
        if cnt == 8:
            out.append(acc)
            acc = 0; cnt = 0
            if len(out) >= n:
                break
    return bytes(out)

def printable_ratio(data):
    if not data:
        return 0.0
    ok = sum(1 for c in data if 32 <= c < 127 or c in (9, 10, 13))
    return ok / len(data)

def has_magic(data):
    return any(m in data[:64] for m in MAGICS)

def runs_ratio(im, ch, bit):
    """Доля серий одинаковых бит длиной >=8 в плоскости (индикатор вложения: у
    чистого фото серии короткие; текстовый payload даёт длинные серии)."""
    px = im.convert('RGB').load()
    w, h = im.size
    prev = None; run = 0; long_runs = 0; total = 0
    for y in range(h):
        for x in range(w):
            b = (px[x, y][ch] >> bit) & 1
            if b == prev:
                run += 1
            else:
                if run >= 8:
                    long_runs += 1
                run = 1
                prev = b
            total += 1
    return long_runs / max(1, total // 8)

def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return
    path = args[0]
    mode = args[1]
    im = Image.open(path)
    has_alpha = im.mode in ('RGBA', 'LA', 'PA')
    rgb = im.convert('RGBA' if has_alpha else 'RGB')
    px = rgb.load()
    w, h = rgb.size

    if mode == '--runs':
        print(f'# runs>=8 ratio per plane (аномалия против ровного фона соседних плоскостей = вложение)')
        for ch, cn in [(0, 'R'), (1, 'G'), (2, 'B')] + ([(3, 'A')] if has_alpha else []):
            for bit in (0, 1, 2, 3):
                r = runs_ratio(rgb, ch, bit)
                print(f'{cn} bit{bit}: {r:.4f}  {"<-- аномалия" if r > 0.05 else ""}')
        return

    if mode == '--extract':
        order, chans, bit, bitord, n = args[2].split(',')
        chmap = {'R': 0, 'G': 1, 'B': 2, 'A': 3}
        chperm = [chmap[c] for c in chans]
        bit = int(bit); n = int(n)
        bg = gen_bits(px, w, h, order, chperm, bit, bitord == 'msb')
        sys.stdout.buffer.write(take_bytes(bg, n, bitord == 'msb'))
        return

    # режим перебора
    show = 3
    if '--show' in args:
        show = int(args[args.index('--show') + 1])
    results = []
    orders = ['row', 'col']
    chan_sets = [(0, 1, 2), (2, 1, 0), (0,), (1,), (2,)] + ([(3,)] if has_alpha else [])
    for order in orders:
        for chperm in chan_sets:
            for bit in (0, 1):
                for msb in (False, True):
                    bg = gen_bits(px, w, h, order, chperm, bit, msb)
                    data = take_bytes(bg, 4096, msb)
                    pr = printable_ratio(data)
                    mg = has_magic(data)
                    if pr > 0.6 or mg:
                        results.append((pr, mg, order, ''.join(
                            'RGBA'[c] for c in chperm), bit, 'msb' if msb else 'lsb', data))
    results.sort(key=lambda r: (r[1], r[0]), reverse=True)
    if not results:
        print('# кандидатов с printable>0.6 или magic нет — LSB-текст маловероятен;')
        print('# проверь --runs, хвост после IEND, exif, другие контейнеры (см. скилл stego-workbench)')
        return
    print(f'# всего кандидатов: {len(results)}; топ:')
    for i, (pr, mg, order, chn, bit, bo, data) in enumerate(results[:10]):
        tag = ' MAGIC' if mg else ''
        print(f'{i+1}. printable={pr:.3f}{tag}  order={order} ch={chn} bit={bit} bits={bo}')
    for i, (pr, mg, order, chn, bit, bo, data) in enumerate(results[:show]):
        print(f'--- hexdump candidate {i+1} ({order},{chn},bit{bit},{bo}) ---')
        for off in range(0, min(256, len(data)), 16):
            chunk = data[off:off+16]
            hexs = ' '.join(f'{c:02x}' for c in chunk)
            asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)
            print(f'{off:04x}  {hexs:<47}  {asc}')

if __name__ == '__main__':
    main()
