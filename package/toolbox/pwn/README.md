# PWN toolbox — хелперы

Готовые кирпичики для бинарных задач. Без привязки к площадке;
без адресов/флагов (подставляйте из контекста задачи).

| Файл | Назначение |
|---|---|
| `pty_transport.py` | Транспорт к сервису за pty (canonical): строки ≤80 байт, фильтр XOFF (0x13), drain «лишнего \n», поэтапная отправка длинных payload |
| `bytewise_shellcode.py` | Генератор shellcode open/read/write с bytewise-записью пути (для лимитов read() 0x80 и проблем с push imm32) |
| `fmt_leak_helper.py` | Скан позиций формат-строки `%N$p` для поиска canary/libc |

## Быстрый старт
```python
from pty_transport import PTYTransport

t = PTYTransport(HOST, PORT)
t.recv_until(b"? ")
t.sendline(b"5")            # короткая строка
t.send_stage(payload)       # длинный ROP-пейлоад (режется по 80)
out = t.recv_clean(2)       # вывод с фильтром XOFF
```

```python
from bytewise_shellcode import bytewise_open_read_write
sc = bytewise_open_read_write(b"flag")   # len ~ 70-90 байт
```

## Рекомендации
- Не плодите `_v2/_v3` — эволюционируйте один скрипт.
- Сначала определите РЕАЛЬНЫЙ бинарник порта (баннер/хеш), потом эксплойт.
- Между стадиями используйте маркеры write() для диагностики.
