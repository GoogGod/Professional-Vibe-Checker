# RSA LSB/parity oracle — решающий скрипт (эталон)

Суть: сервис раскрывает чётность расшифрованного сообщения (`even` для `ciphertext`).
Используя мультипликативное свойство RSA, можно сузить интервал `[0, n)` до одного
значения за `n.bit_length()` запросов.

## Протокол (типичный)
- `GET /public_key` → `{"n":..., "e":..., "ciphertext":...}` (RSA 2048, e=65537).
- `GET /oracle?ciphertext=<int>` → `{"even": true|false}`.

## Алгоритм (бинарный поиск по интервалу)
```python
import requests, json
BASE = 'http://host:port'
def get_int(url): return json.loads(requests.get(BASE+url, timeout=10).text)
pub = get_int('/public_key')
n, e, c = int(pub['n']), int(pub['e']), int(pub['ciphertext'])
def even(ct): return get_int(f'/oracle?ciphertext={ct}')['even']
lo, hi = 0, n
for i in range(n.bit_length()):
    c = c * pow(2, e, n) % n
    mid = (lo + hi) // 2
    if even(c): hi = mid
    else:       lo = mid
m = hi
print(m.to_bytes((m.bit_length()+7)//8, 'big'))
```
- Мультипликативность: `oracle(c * 2^e mod n)` соответствует `2m mod n`; если
  результат чётный → значение в нижней половине, иначе — в верхней.
- Запросы: `n.bit_length()` (2048 для 2048-битного RSA); ~0.1-0.2 с/запрос.

## Готовые имплементации
- `toolbox/платформа-limited/rsa_lsb_oracle.py` (использовать как эталон);
- ускорить можно пулом соединений (requests.Session / http.client keep-alive).

## Типичные грабли
- Не путать «чётность» с битовым значением mSB: здесь именно чётность (LSB).
- После последней итерации `m` может отличаться на 1 — проверить `lo`/`hi`.
- Если сервис однопоточный — не пихать параллельные запросы (можно получить
  таймаут/смешение ответов).
