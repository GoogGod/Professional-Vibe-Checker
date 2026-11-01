---
name: crypto-remote-oracle-services
description: Используй для криптографических сервисов с раскалыщими оракулами: RSA-«чётность»/LSB (endpoint /oracle?ciphertext=..., /public_key с n/e/ciphertext), HMAC с раскрываемым свернутым значением (block_xor), и любые сервисы, где сервер отвечает «да/нет»/«чётно/нечётно» и даёт публичные параметры.
---
# Крипто-сервисы с оракулами (RSA LSB / HMAC block_xor)

## Признаки
- `GET /public_key` → JSON `{n, e, ciphertext}` — RSA, e=65537, n 2048 бит.
- `GET /oracle?ciphertext=<int>` → `{"even": true|false}` — RSA LSB/parity oracle.
- `POST /oracle {"msg": ...}` → `{"block_xor":".."}` — HMAC, свернутый блок (4 байта).
- `POST /verify {"msg":..., "mac":...}` → флаг при успехе.
- «Булевый предсказатель», «Хмак! Будь здоров!» и т.п.

## Рабочий путь (кратко)
### RSA LSB oracle
1. `pub = /public_key`; `n,e,c`.
2. Повторить `n.bit_length()` раз:
   `c = c * pow(2,e,n) % n; mid=(lo+hi)//2; if oracle(c): hi=mid else lo=mid`.
3. `m=hi` → `m.to_bytes((m.bit_length()+7)//8,'big')` → флаг.
- Запросов: `n.bit_length()` (2048); ~0.1-0.2 с/запрос; использовать `requests.Session`.

### HMAC block_xor
1. `block_xor` = 4 байта («свёрнутый» MAC); mac 32 байта = 4 блока по 8.
2. Подделка: `mac_in = bx[0:1]+b'\x00'*7 + bx[1:2]+b'\x00'*7 + bx[2:3]+b'\x00'*7 + bx[3:4]+b'\x00'*7`.
3. Отправить `{"msg":..., "mac": mac_in.hex()}` → флаг.
- Forward всех с XOR блока = один значащий байт, остальное нули.

## Готовые имплементации
- `knowledge-base/local/lessons/2026-11-01-rsa-lsb-oracle.md`
- `knowledge-base/local/lessons/2026-11-01-hmac-blockxor-forge.md`
- `toolbox/duckerz-limited/rsa_lsb_oracle.py`, `toolbox/duckerz-limited/hmac_blockxor_forge.py`

## Грабли
- Сначала прочитать исходник сервиса (если есть) — он даёт точные поля/порты.
- Не перебирать «все возможные атаки» — определить тип по полям ответов.
- Для long-запросов — фон + прогресс; не блокироваться в 200 итераций.