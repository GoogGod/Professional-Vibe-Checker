#!/usr/bin/env python3
"""alpha_lsb.py - LSB extraction from alpha-marked pixels of a PNG (RGBA).

Field-proven mechanic (2026-10-22, hard stego): alpha channel is constant
(255) except N marked pixels; the marks are a MAP - the payload is LSB bits
of RGB channels of exactly those pixels, in row-major order.

Usage:
  python3 alpha_lsb.py IMG.png                  # report + auto battery
  python3 alpha_lsb.py IMG.png --expect "CTF{"  # exit 0 when prefix found
  python3 alpha_lsb.py IMG.png --show 64        # print first bytes of best
  python3 alpha_lsb.py IMG.png --alpha 254 --channels RGB --order row --bitorder msb --raw
"""
import sys, itertools

def load(path):
    from PIL import Image
    im = Image.open(path)
    return im.convert("RGBA")

def alpha_report(a):
    import numpy as np
    vals, counts = np.unique(a, return_counts=True)
    return list(zip(vals.tolist(), counts.tolist()))

def marked(a, bg):
    import numpy as np
    m = a != bg
    return m

def variants(px, ys, xs):
    """yield (name, bits) for a battery of decode variants; px=RGB plane, ys/xs sorted mark coords"""
    import numpy as np
    sel = px[ys, xs]  # rows in given order
    for chans in (("R", "G", "B"), ("B", "G", "R"), ("R",), ("G",), ("B",)):
        ci = {"R": 0, "G": 1, "B": 2}
        cols = [sel[:, ci[c]] for c in chans]
        if len(cols) == 1:
            plane = cols[0]
        else:
            plane = np.empty(sel.shape[0] * len(cols), dtype=sel.dtype)
            for k, c in enumerate(cols):
                plane[k::len(cols)] = c
        bits = plane & 1
        for bitorder in ("msb", "lsb"):
            n = (len(bits) // 8) * 8
            if n == 0:
                continue
            b = bits[:n].reshape(-1, 8)
            if bitorder == "msb":
                weights = 2 ** np.arange(7, -1, -1)
            else:
                weights = 2 ** np.arange(8)
            yield "ch=%s,bit=%s" % ("".join(chans), bitorder), (b * weights).sum(axis=1).astype("uint8").tobytes()

def order_indices(mask, order):
    import numpy as np
    ys, xs = np.nonzero(mask)
    if order == "row":      # row-major (default; matches scan order)
        key = np.lexsort((xs, ys))
    elif order == "col":
        key = np.lexsort((ys, xs))
    elif order == "byx":
        key = np.lexsort((ys, xs))
    elif order == "byy":
        key = np.lexsort((xs, ys))
    else:
        raise SystemExit("bad --order")
    return ys[key], xs[key]

def prefix_ratio(data):
    best = 0.0
    for w in (16, 24, 32, 64, 128, 256, 512):
        if len(data) < w:
            continue
        chunk = data[:w]
        pr = sum(32 <= c < 127 or c in (9, 10, 13) for c in chunk) / w
        best = max(best, pr)
    return best

MAGICS = (b"PK\x03\x04", b"\x89PNG", b"GIF8", b"%PDF", b"\x7fELF", b"flag", b"FLAG", b"CTF{", b"ctf{")

def main():
    import numpy as np
    args = sys.argv[1:]
    if not args:
        print(__doc__); return 2
    img_path = args[0]
    opt = {"--alpha": None, "--channels": None, "--order": "row", "--bitorder": None,
           "--expect": None, "--show": None, "--raw": False}
    i = 1
    while i < len(args):
        k = args[i]
        if k == "--raw":
            opt["--raw"] = True; i += 1; continue
        opt[k] = args[i + 1]; i += 2
    im = load(img_path)
    px = np.asarray(im)
    a = px[:, :, 3]
    rep = alpha_report(a)
    print("alpha histogram (value:count):", rep[:10], "..." if len(rep) > 10 else "")
    bg = max(rep, key=lambda t: t[1])[0]
    m = marked(a, bg)
    n = int(m.sum())
    print("background alpha=%d, marked pixels: %d -> max bits %d (=%d bytes)" % (bg, n, n * 3, n * 3 // 8))
    if n == 0:
        print("no alpha anomaly: payload is not alpha-mapped"); return 1
    results = []
    for order in ("row", "col", "byx", "byy"):
        ys, xs = order_indices(m, order)
        for name, data in variants(px[:, :, :3], ys, xs):
            pr = prefix_ratio(data)
            hit = next((mm for mm in MAGICS if data.startswith(mm) or mm in data[:64]), None)
            results.append((pr, order + "," + name, data, hit))
    if opt["--channels"]:
        # single explicit variant, raw output
        chans = opt["--channels"]
        bo = opt["--bitorder"] or "msb"
        ys, xs = order_indices(m, opt["--order"])
        sel = px[:, :, :3][ys, xs]
        ci = {"R": 0, "G": 1, "B": 2}
        cols = [sel[:, ci[c]] for c in chans]
        if len(cols) == 1:
            plane = cols[0]
        else:
            plane = np.empty(sel.shape[0] * len(cols), dtype=sel.dtype)
            for k, c in enumerate(cols):
                plane[k::len(cols)] = c
        bits = plane & 1
        nb = (len(bits) // 8) * 8
        b = bits[:nb].reshape(-1, 8)
        weights = 2 ** np.arange(7, -1, -1) if bo == "msb" else 2 ** np.arange(8)
        data = (b * weights).sum(axis=1).astype("uint8").tobytes()
        results = [(1.0, "explicit %s %s %s" % (chans, opt["--order"], bo), data, None)]
    results.sort(key=lambda t: -t[0])
    shown = 0
    exp = opt["--expect"]
    expb = exp.encode() if exp else None
    ok = False
    for pr, name, data, hit in results[:8]:
        if pr < 0.5 and not hit and not (expb and expb in data[:256]):
            continue
        printable = "".join(chr(c) if 32 <= c < 127 else "." for c in data[:48])
        print("[%0.2f] %s: %s" % (pr, name, printable))
        if expb and data.startswith(expb):
            print("PREFIX OK:", exp)
            ok = True
        shown += 1
    if opt["--show"]:
        k = int(opt["--show"])
        pr, name, data, hit = results[0]
        print("BEST %s:\n%s" % (name, data[:k].decode("utf-8", "replace")))
    if exp and not ok:
        print("prefix not found in top variants")
    return 0 if ok else (0 if shown else 1)

if __name__ == "__main__":
    sys.exit(main())
