# A/D Kit — полевой комплект молотилки (v2) и репетиционный стенд

Обновляется из пакета (public). Секретов и адресов реальных турниров нет — всё через env.

## Файлы

- `farm.py` — молотилка: ctftime-синхронизация с раундом → attack_data → `exploits/exploit_<service>.py` → батч PUT `/api/v1/flags` (дедуп на диске, лимит/мин). Считает статистику линий, напоминает `RETIRE?` балласту, репортит дренаж из `/public/attacks`.
- `watch.py` — вахтёр: статусы своих (Volga-алерт при не-OK) + **анти-дренаж** (кражи у нас при зелёном статусе → `DRAIN`-алерт).
- `mock_jury.py` — репетиционный стенд: jury-API + 2 уязвимых сервиса + чекер + симуляция патча/поломки. **Прогонять за день до боя.**

## Контракт эксплойта (для farm.py)

```python
# exploits/exploit_notes.py
SERVICE, PORT = "notes", 8021
def exploit(host, port, hints):
    # host = ip жертвы из attack_data, hints = список подсказок
    ...
    return "FLAG..."        # или список, или None
```

## Репетиция (5 минут, обязательно перед каждым A/D)

```bash
python3 mock_jury.py &                 # стенд (jury :8020, notes :8021, vault :8022)
echo mock-token > token.txt
# положи exploits/exploit_notes.py и exploit_vault.py (см. ниже смысл уязвимостей)
AD_JURY=http://127.0.0.1:8020 AD_MY_IP=127.0.0.7 AD_TOKEN_FILE=token.txt \
  setsid nohup python3 farm.py >> logs/farm.log 2>&1 &
AD_JURY=http://127.0.0.1:8020 AD_MY_IP=127.0.0.7 python3 watch.py
```

Тренируемые ситуации (все — руками через curl, смотри реакцию watch/farm):
1. `curl -X POST http://127.0.0.1:8020/admin/patch -d '{"service":"notes"}' -H 'Content-Type: application/json'`
   → статус notes=CORRUPT у ВСЕХ команд → watch кричит → «откатывай патч» → `/admin/rollback` → OK. Это и есть Volga-петля на практике.
2. `/admin/break` + `/admin/fix` — DOWN и восстановление.
3. Отключи эксплойт-файл → farm должен жить без него (балласт-детект).
4. Отправь свой флаг/мусор в сабмит → rejected → seen.

## Уязвимости стенда (для тренировочных эксплойтов)

- **notes** (:8021): `GET /notes?team=N&title=<подстрока>` — проекция по подстроке; флаг лежит в заметке, чекер кладёт с `title=hint-XXXXXX` (hint есть в attack_data) → `GET /notes?team=N&title=<hint>` отдаёт флаг.
- **vault** (:8022): сессия = `md5(name)[:12]` — предсказуема; `GET /vault?team=N&name=<hint>` → session + secret(=флаг).

## В бою

- `AD_JURY`, `AD_MY_IP`, `AD_TOKEN_FILE` — из брифинга турнира (local/tactics).
- Формат флага в `farm.py` (`FLAG_RE`) сверить с `/api/client/config/`.
- Код статуса `101 = OK` в `watch.py` сверить с реальным API.
