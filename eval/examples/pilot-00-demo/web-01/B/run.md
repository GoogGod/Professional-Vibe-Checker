---
run_id: 2026-10-18-web-01-B
batch: pilot-00-demo
task: web-01
branch: B
model: demo-model
harness: demo-harness
params: t=0.2
limits: 90m / 150 steps
started: 2026-10-18T10:40:00+05:00
ended: 2026-10-18T11:37:00+05:00
solved: true
flag_confirmed: true
duration_min: 57
steps: 92
tokens:
first_useful_step: 21
first_correct_class_step: 11
slop_flags: 0
rabbit_holes: 1
false_claims: 1
progress: 2
isolation_check: ok
contaminated: false
invalid: false
notes: ДЕМО-данные; заметно медленнее выходил на рабочий путь.
---

# Прогон 2026-10-18-web-01-B

## Что делали

Демо-запись (обезличенные данные): контрольная ветка для проверки `score.py`.

## Ход (ключевые шаги)

1. Долгий перебор вариантов без разведки структуры.
2. Тупиковая серия (одна), затем смена гипотезы.
3. Найден рабочий маршрут; флаг подтверждён.

## Итог

Флаг подтверждён (демо). Стоп по достижению цели.

## Артефакты

- `work/` — демо
- транскрипт: не приложен (демо)