#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hf.py — конвейер работы с HC-датасетом Vyber07/cyber-security.

Подкоманды:
  manifest       — построить manifest.csv из списка файлов (AAAA.txt)
  fetch-desc     — скачать ВСЕ описания (A-arvo/oss-fuzz/nvd) параллельно
  index          — собрать index.json (cve_id -> текст описания) из desc/

Требования: Python 3, requests (системный python3 в Kali).
Токен: ~/.huggingface/token (только чтение). Сырьё — строго в data/raw/hf/ (вне git).
"""
import argparse, concurrent.futures as cf, json, os, sys

BASE_URL = 'https://huggingface.co/datasets/Vyber07/cyber-security/resolve/main'
DATASET_ID = 'Vyber07/cyber-security'

def token():
    p = os.path.expanduser('~/.huggingface/token')
    if not os.path.exists(p):
        print('FATAL: no HF token at ~/.huggingface/token', file=sys.stderr)
        sys.exit(2)
    return open(p).read().strip()

# ----------------------------------------------------------------- config
DEFAULT_ROOT = '/mnt/c/Users/Immortal/Desktop/ctf_tools/ARTEX-RU-Windows-x64/data/raw/hf'
DEFAULT_SRC = '/mnt/c/Users/Immortal/Desktop/fricking_ctf_trash/AAAA.txt'

# ----------------------------------------------------------------- manifest
def cmd_manifest(args):
    lines = open(args.src, encoding='utf-8', errors='replace').read().splitlines()
    names = [l.strip().lstrip('+').strip() for l in lines if l.strip().startswith('+')]
    files = [n for n in names if not n.endswith('/') and n not in ('', '.gitattributes', 'LICENSE')]
    out = os.path.join(args.root, 'manifest.csv')
    os.makedirs(args.root, exist_ok=True)
    with open(out, 'w', encoding='utf-8', newline='') as f:
        import csv as _csv
        w = _csv.writer(f)
        w.writerow(['path'])
        for n in sorted(files):
            w.writerow([n])
    print('manifest:', out, 'files:', len(files))

# ----------------------------------------------------------------- fetch-desc
def _pick_desc(files):
    out = []
    for n in files:
        low = n.lower()
        if low.endswith('__description.txt') and ('arvo' in low or 'oss' in low or 'nvd' in low):
            out.append(n)
    return out

def _dl_one(remote, dest, headers):
    p = os.path.join(dest, os.path.basename(remote))
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return remote, 'skip'
    import requests
    try:
        r = requests.get(BASE_URL + '/' + remote, headers=headers, timeout=30)
        if r.status_code == 200 and len(r.content) > 0:
            with open(p, 'wb') as f:
                f.write(r.content)
            return remote, 'ok:%d' % len(r.content)
        return remote, 'http:%d' % r.status_code
    except Exception as e:
        return remote, 'err:%s' % type(e).__name__

def cmd_fetch_desc(args):
    import csv as _csv
    files = []
    with open(os.path.join(args.root, 'manifest.csv'), encoding='utf-8') as f:
        for row in _csv.reader(f):
            if row and row[0] != 'path':
                files.append(row[0])
    targets = _pick_desc(files)
    if args.limit:
        targets = targets[:args.limit]
    dest = os.path.join(args.root, 'desc')
    os.makedirs(dest, exist_ok=True)
    headers = {'Authorization': 'Bearer ' + token()}
    print('fetching %d descriptions -> %s' % (len(targets), dest), flush=True)
    done = ok = 0
    with cf.ThreadPoolExecutor(max_workers=args.parallel) as ex:
        for remote, status in ex.map(lambda t: _dl_one(t, dest, headers), targets):
            done += 1
            if status.startswith('ok'):
                ok += 1
            if done % 200 == 0:
                print('... %d/%d (ok=%d)' % (done, len(targets), ok), flush=True)
    print('DONE: %d/%d ok' % (ok, len(targets)))

# ----------------------------------------------------------------- index
def cmd_index(args):
    desc = os.path.join(args.root, 'desc')
    idx = {}
    for fn in sorted(os.listdir(desc)):
        if not fn.endswith('.txt'):
            continue
        body = open(os.path.join(desc, fn), encoding='utf-8', errors='replace').read().strip()
        # cve_id из имени: ...__arvo__<ID>__description.txt
        core = fn[:-len('__description.txt')]
        idx[core] = body[:2000]
    out = os.path.join(args.root, 'index.json')
    json.dump(idx, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('index:', out, 'entries:', len(idx))

# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(prog='hf.py')
    ap.add_argument('--root', default=DEFAULT_ROOT)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('manifest')
    p.add_argument('--src', default=DEFAULT_SRC)
    p.set_defaults(func=cmd_manifest)

    p = sub.add_parser('fetch-desc')
    p.add_argument('--parallel', type=int, default=20)
    p.add_argument('--limit', type=int, default=0)
    p.set_defaults(func=cmd_fetch_desc)

    p = sub.add_parser('index')
    p.set_defaults(func=cmd_index)

    a = ap.parse_args()
    a.func(a)

if __name__ == '__main__':
    main()
