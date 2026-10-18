---
run_id: example-000-A
batch: <batch-id>
task: <task-id>
branch: A
model: <model+version>
harness: <harness+version>
params: <temperature и пр.>
limits: <время/шаги/токены>
started: <ISO8601>
ended: <ISO8601>
solved: false
flag_confirmed: false
duration_min:
steps:
tokens:
first_useful_step:
first_correct_class_step:
slop_flags: 0
rabbit_holes: 0
false_claims: 0
progress: 0
isolation_check: pending
contaminated: false
invalid: false
notes:
---

# Прогон <run_id>

## Что делали

<кратко: ветка, условия, что дано на вход>

## Ход (ключевые шаги)

1. <шаг>
2. <шаг>
3. <шаг>

## Итог

<флаг подтверждён / не найден; причина остановки (лимит, сдача, инфрасбой)>

## Артефакты

- `work/` — рабочий каталог прогона
- транскрипт: `<путь или ссылка>`
- `knowledge-writeback/` — только для ветки A