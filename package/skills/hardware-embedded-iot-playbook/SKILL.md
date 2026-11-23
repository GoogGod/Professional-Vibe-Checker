---
name: hardware-embedded-iot-playbook
description: Используй этот скилл, когда задача относится к аппаратному обеспечению, встроенным системам или IoT: проекты САПР (Proteus .pdsprj, схемы), прошивки микроконтроллеров (ATmega AVR, Intel HEX), шины (SPI, I2C, UART), логические схемы, MQTT-брокеры и сенсорные сети. Содержит проверенные кейсы: извлечение флага из данных flash, side-channel PIN, инъекция в регистры через SPI, retained-сообщения MQTT.
---
# Hardware / Embedded / IoT — playbook

Опыт прошедших серий; без привязки к конкретному соревнованию.
Флаги не хранятся, только приёмы.

## 1. Проекты САПР — Proteus 8
- `.pdsprj` = ZIP: распаковать (`7z x`, `unzip`).
- Внутри `ROOT.DSN` (бинарный, строки читаются парсером `\xff-len`),
  `ROOT.CDB`, `GRAPHS.DAT`, `ROOT.LYT`, `PROJECT.XML`.
- Извлечь: МК (ATmega32, частота), датчики/шины (I2C LM75AD, SPI,
  UART), подтяжки/делители, виртуальный терминал.
- Схема часто «внутри» названия задачи: логика, температура, свет и т.п.

## 2. Прошивки AVR (Intel HEX)
- `avr-objdump -D -m avr5 code.hex` → листинг.
- Искать main, инициализацию UART/TWI, циклы опроса датчиков,
  условную печать (ALERT) и скрытый массив (копируется из flash в SRAM).
- Перебрать однобайтовые XOR-ключи по данным flash — флаг читается.
- Внимание: условие в задаче может быть ложным («HEX не влияет»).

## 3. SPI / side-channel
- Ограниченные попытки: probe `[d,d,d,d]` → lit_windows → извлечение PIN.
- Уважать rate limit (429) — паузы, retry, точные финальные probe.
- Дамп firmware → найти адрес регистра датчика (напр. CORE_TEMP
  `0x08..0x0B`) → подменить его (`FF FF FF FF`) → спровоцировать
  «критическую» ветку → флаг в ответе.

## 4. Логические схемы
- Таблица истинности xlsx/pdf → восстановить булевы выражения
  (NOT/AND/OR/XOR/XNOR) → вычислить выход → битовый вектор → ASCII.
- Порядок битов MSB-first по строкам; пустые строки не ломают вектор.

## 5. MQTT/IoT
- Анонимный вход → подписка `#`, `$SYS/#`, `+/+`, точные топики.
- Retained-сообщения (часто флаг), Last Will/takeover, persistent session.
- Креды: `admin:jennifer` (rockyou), `admin:admin`, тематические пары.
- Проверять креды корректно: username/password **после** connect().
- Если брокер не маршрутизирует (B получает PUBACK, A — нет): вероятно,
  инстанс битый — не тратить время, пересоздать/ждать рестарт.
- **Подсказки (announcements)**: редкий топик вида `/announcements`
  (раз в ~20 с) — настоящая зацепка сюжета; поток сенсоров
  (`/sensors/...`) часто декоративный «туман». Имена из подсказок —
  прямые указания на цель (напр. `duck` vs `duck_fan`).
- **Перебор пользователя MQTT**: параллельные CONNECT с парами (user, pass)
  из rockyou (top-20k); успех = CONNACK 0x00, неверные креды = 0x86
  (v3.1.1: ошибка/отказ). ~90–100 попыток/с при 32 соединениях.
- **Paho**: `username_pw_set()` вызывать ДО `connect()` — иначе соединение
  анонимное (ложный успех). MQTT5 CONNACK разбирать с учётом remaining length.
- Запрет записи анонимом: MQTT5 → PUBACK 0x87 (Not authorized); v3.1.1 —
  молчаливый дроп. Retained-секрет читается после логина мгновенно.

## Связанные уроки
- `lessons/2026-11-04-hardware-proteus-avr-firmware.md`
- `lessons/2026-11-04-hardware-spi-master-injection.md`
- `lessons/2026-11-04-hardware-logic-circuit-truth-table.md`
- `lessons/2026-11-04-iot-mqtt-broker-retained.md`
- `lessons/2026-11-01-hardware-fpga-ice40-bitstream-21centuryman.md`
- `lessons/2026-11-01-hardware-fpga-verilog-sim.md`
