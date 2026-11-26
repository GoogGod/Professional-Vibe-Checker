#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
triage.py — быстрая автоматическая разведка файла/бинарника.
Использование: python3 triage.py <path> [--remote host port]
"""
import argparse, os, subprocess, sys

def sh(cmd, **kw):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=kw.pop('timeout', 30), **kw).stdout
    except Exception as e:
        return '[err %s]' % e

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--remote', nargs=2)
    a = ap.parse_args()
    p = a.path
    if not os.path.exists(p):
        print('no such file:', p); sys.exit(1)
    print('=' * 60)
    print('FILE :', sh('file "%s"' % p).strip())
    print('SIZE :', os.path.getsize(p), 'bytes')
    # ELF details
    if open(p, 'rb').read(4) in (b'\x7fELF',) or 'ELF' in sh('file "%s"' % p):
        print('CHECKSEC:')
        print(sh('checksec --file="%s" 2>/dev/null || /usr/bin/checksec --file="%s" 2>/dev/null' % (p, p)).strip() or '  (checksec not found)')
        print('IMPORTS (dyn-sym):')
        print(sh('objdump -T "%s" 2>/dev/null | grep -E "UND|GLOBAL" | head -30' % p).strip())
        print('FUNCTIONS (non-stripped):')
        print(sh('objdump -d -M intel "%s" 2>/dev/null | grep -E "^[0-9a-f]+ <" | head -30' % p).strip())
    print('STRINGS (interesting):')
    strs = sh('strings -n 6 "%s" | grep -iE "flag|pass|secret|key|/bin|sh|http|admin|user|usage|%|\\$|0x" | head -40' % p)
    print(strs.strip() or '  (none)')
    print('MAGIC/BINWALK:')
    print(sh('binwalk "%s" 2>/dev/null | head -20' % p).strip())
    if a.remote:
        h, port = a.remote
        print('REMOTE BANNER:')
        print(sh('timeout 8 nc %s %s' % (h, port)).strip()[:500])
    print('=' * 60)

if __name__ == '__main__':
    main()
