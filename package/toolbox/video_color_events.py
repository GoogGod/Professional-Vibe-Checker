#!/usr/bin/env python3
"""video_color_events.py — счёт цветовых объектов в видео и декод ASCII-флагов.

Для задач типа "информация в гейплее" (Subway-серия): красные вагоны = значение
символа, жёлтые = разделители; счётчик HUD на экране; и т.п. Работает с кадрами
(каталог PNG/JPG) или видео (режим --video сам зовёт ffmpeg). Блобы цвета
ищутся HSV-порогом, трекаются между кадрами по пересечению bbox; новое
появление = событие. Результат — счётчики по сегментам + ASCII-декод с
самопроверкой по префиксу флага из условия (--expect).

Использование:
  python3 video_color_events.py --frames DIR --hsv 0,120,80 10,255,255 --min-area 400 --expect "CTF{"
  python3 video_color_events.py --video v.mp4 --hsv 0,120,80 10,255,255 --sep-hsv 25,80,80 35,255,255
  python3 video_color_events.py --frames DIR ... --raw   # только числа, без chr()
HSV: "Hmin,Smin,Vmin" и "Hmax,Smax,Vmax" (OpenCV-шкала H 0-179; PIL-режим H 0-255).
"""
import argparse
import glob
import os
import subprocess
import sys

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

from PIL import Image


def parse_hsv(s):
    return tuple(int(x) for x in s.split(','))


def load_frames(frames_dir):
    files = sorted(
        f for f in glob.glob(os.path.join(frames_dir, '*'))
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
    )
    if not files:
        raise SystemExit(f'no frames in {frames_dir}')
    return files


def extract_frames(video, out_dir, fps):
    os.makedirs(out_dir, exist_ok=True)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', video,
           '-vf', f'fps={fps}', os.path.join(out_dir, '%05d.png')]
    subprocess.run(cmd, check=True)
    return load_frames(out_dir)


def hsv_mask(img, lo, hi):
    """Маска по HSV-диапазону. Носитель H: 0-255 (PIL)."""
    hsv = img.convert('HSV')
    w, h = hsv.size
    if HAS_NUMPY:
        a = np.asarray(hsv, dtype=np.int16)
        m = ((a[:, :, 0] >= lo[0]) & (a[:, :, 0] <= hi[0]) &
             (a[:, :, 1] >= lo[1]) & (a[:, :, 1] <= hi[1]) &
             (a[:, :, 2] >= lo[2]) & (a[:, :, 2] <= hi[2]))
        return m
    m = bytearray(w * h)
    d = hsv.getdata()
    for i, (hh, ss, vv) in enumerate(d):
        if lo[0] <= hh <= hi[0] and lo[1] <= ss <= hi[1] and lo[2] <= vv <= hi[2]:
            m[i] = 1
    return m


def blobs_from_mask(mask, w, h, min_area):
    """Connected components построчной сегментацией (без scipy).
    numpy-путь векторный: границы рангов через diff (C-скорость)."""
    runs = []          # (row, x0, x1)
    if HAS_NUMPY and isinstance(mask, np.ndarray):
        m = mask.astype(np.uint8)
        for y in range(h):
            row = m[y]
            if not row.any():
                continue
            d = np.diff(np.concatenate(([0], row, [0])))
            starts = np.flatnonzero(d == 1)
            ends = np.flatnonzero(d == -1)
            for s, e in zip(starts.tolist(), ends.tolist()):
                runs.append((y, s, e - 1))
    else:
        if not isinstance(mask, (bytes, bytearray)):
            mask = bytes(mask)
        for y in range(h):
            base = y * w
            row = mask[base:base + w]
            x = row.find(1) if isinstance(row, bytes) else -1
            x = row.find(b'\x01') if x < 0 and isinstance(row, bytes) else x
            pos = 0
            while True:
                s = row.find(1, pos) if isinstance(row, bytearray) else row.find(b'\x01', pos)
                if s < 0:
                    break
                e = row.find(0, s) if isinstance(row, bytearray) else row.find(b'\x00', s)
                if e < 0:
                    e = w
                runs.append((y, s, e - 1))
                pos = e
    # union-find: пересечение только с рангами предыдущей строки
    parent = list(range(len(runs)))
    runs_by_row = {}
    for idx, (y, _, _) in enumerate(runs):
        runs_by_row.setdefault(y, []).append(idx)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for y, idxs in runs_by_row.items():
        if (y - 1) not in runs_by_row:
            continue
        for idx in idxs:
            _, x0, x1 = runs[idx]
            for j in runs_by_row[y - 1]:
                _, px0, px1 = runs[j]
                if px0 <= x1 and px1 >= x0:
                    a, b = find(idx), find(j)
                    if a != b:
                        parent[a] = b
    comps = {}
    for idx in range(len(runs)):
        r = find(idx)
        y, x0, x1 = runs[idx]
        c = comps.setdefault(r, [x0, x1, y, y, 0])
        c[0] = min(c[0], x0); c[1] = max(c[1], x1)
        c[3] = max(c[3], y); c[2] = min(c[2], y)
        c[4] += x1 - x0 + 1
    out = []
    for c in comps.values():
        if c[4] >= min_area:
            cx = (c[0] + c[1]) / 2.0
            cy = (c[2] + c[3]) / 2.0
            out.append({'x0': c[0], 'x1': c[1], 'y0': c[2], 'y1': c[3],
                        'area': c[4], 'cx': cx, 'cy': cy})
    return out


def overlaps(a, b):
    return not (a['x1'] < b['x0'] or b['x1'] < a['x0'] or
                a['y1'] < b['y0'] or b['y1'] < a['y0'])


def matches(a, b):
    """Продолжение объекта: пересечение bbox ИЛИ близость центров
    (быстрое движение при низком fps)."""
    if overlaps(a, b):
        return True
    th = max(a['x1'] - a['x0'], a['y1'] - a['y0'],
             b['x1'] - b['x0'], b['y1'] - b['y0']) * 1.2 + 8
    return abs(a['cx'] - b['cx']) <= th and abs(a['cy'] - b['cy']) <= th


def count_events(frames, lo, hi, min_area):
    """Счёт уникальных появлений объекта цвета; трек по bbox/центрам."""
    seen = 0
    active = []
    for path in frames:
        img = Image.open(path).convert('RGB')
        w, h = img.size
        mask = hsv_mask(img, lo, hi)
        cur = blobs_from_mask(mask, w, h, min_area)
        nxt_active = []
        for b in cur:
            if any(matches(b, p) for p in active):
                nxt_active.append(b)     # продолжение существующего
            else:
                seen += 1                # новое появление
                nxt_active.append(b)
        active = nxt_active
    return seen


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('--frames')
    ap.add_argument('--video')
    ap.add_argument('--fps', type=float, default=5)
    ap.add_argument('--out-frames', default='/tmp/vce_frames')
    ap.add_argument('--hsv', nargs=2, required=True,
                    metavar=('LO', 'HI'), type=parse_hsv)
    ap.add_argument('--sep-hsv', nargs=2, metavar=('LO', 'HI'), type=parse_hsv)
    ap.add_argument('--min-area', type=int, default=300)
    ap.add_argument('--expect', default='')
    ap.add_argument('--raw', action='store_true')
    args = ap.parse_args()

    if args.video:
        frames = extract_frames(args.video, args.out_frames, args.fps)
    elif args.frames:
        frames = load_frames(args.frames)
    else:
        raise SystemExit('нужен --frames или --video')

    lo, hi = args.hsv
    print(f'# frames: {len(frames)}; events for color {lo}..{hi}, min_area={args.min_area}')

    if not args.sep_hsv:
        n = count_events(frames, lo, hi, args.min_area)
        print(f'events: {n}')
        return

    # режим сегментов: значение-цвет между разделителями
    slo, shi = args.sep_hsv
    counts = []
    cur = 0
    seen_sep = False
    active_v, active_s = [], []
    for path in frames:
        img = Image.open(path).convert('RGB')
        w, h = img.size
        mv = blobs_from_mask(hsv_mask(img, lo, hi), w, h, args.min_area)
        ms = blobs_from_mask(hsv_mask(img, slo, shi), w, h, args.min_area)
        for b in mv:
            if not any(matches(b, p) for p in active_v):
                cur += 1
        active_v = mv
        sep_now = len(ms) > 0
        if active_s and not ms and seen_sep:
            # разделитель исчез: сегмент завершён
            counts.append(cur)
            cur = 0
        if ms:
            seen_sep = True
        active_s = ms
    if cur > 0:
        counts.append(cur)

    print('counts:', counts)
    if args.raw:
        return
    text = ''.join(chr(n) if 9 <= n < 127 else '?' for n in counts)
    print('decoded:', text)
    if args.expect:
        ok = text.startswith(args.expect)
        print(('PREFIX OK: ' if ok else 'PREFIX MISMATCH: ') + args.expect)
        sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
