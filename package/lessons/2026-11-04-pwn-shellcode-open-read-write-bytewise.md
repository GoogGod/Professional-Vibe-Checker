# PWN: shellcode open/read/write с построением пути посимвольно (bytewise)

Суть: переполнение на исполняемом стеке (PIE, NX off, GNU_STACK RWE); гаджет
`jmp rsi`; место записи shellcode ограничено (read 0x80).

## Алгоритм
1. Утечка базы PIE: меню/функция печатает адрес (например, showTechnicalInfo)
   → `base = leak - offset_функции`.
2. Восстановить адрес возврата: `base + jmp_rsi`; payload:
   `jmp rel +0x1e` + NOP*14 + 'B'*8 (saved rbp) + p64(base+jmp_rsi) + shellcode.
3. Shellcode: `lea rbx,[rsp+0x200]`; bytewise запись пути в rbx:
   `mov byte [rbx+i], ch` ... `mov byte [rbx+N], 0`;
   затем `open(path,0,0)`, `read(fd,rbx,0xff)`, `write(1,rbx,n)`.

## Грабли
- **scanf буферизует ввод**: после `scanf` (`read()` не получает данные,
  отправленные одним куском. Отправлять поэтапно — дожидаясь промптов.
- `push imm32` кладёт байты без реверса и ограничен 4 байтами: для пути
  длиннее 4 символов надёжнее bytewise `mov byte [reg+i], ch`.
- `execve("/bin/sh")` с NULL argv/envp часто падает; open/read/write без
  argv — стабильно.
- Буфер чтения ниже RSP (rsp-0x100) упирается в guard page: писать выше
  (rsp+0x200).
- Маркеры write() между стадиями (например, KOW/O/R) подтверждают
  выполнение shellcode.
