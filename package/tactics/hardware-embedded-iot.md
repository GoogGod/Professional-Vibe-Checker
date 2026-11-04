# Hardware/Embedded/IoT: схемы, прошивки, шины, MQTT — тактика

Когда применять: задачи на проекты САПР (Proteus 8), прошивки
микроконтроллеров, логические схемы, SPI/I2C/UART, MQTT-брокеры.

## Порядок действий
1. **Распаковать проект**: `.pdsprj` = ZIP → `ROOT.DSN` (строки через
   парсер `\xff-len`) + XML/CDB/LYT. Извлечь МК, датчики, шины.
   `lessons/2026-11-04-hardware-proteus-avr-firmware.md`.
2. **Прошивка AVR** (Intel HEX): `avr-objdump -D -m avr5 code.hex`;
   искать скрытый массив данных (в SRAM) и ветку «ALERT»; перебрать
   однобайтовые XOR-ключи → флаг. Условие задачи может врать.
3. **SPI / side-channel**: PIN-извлечение по lit_windows (probe
   одинаковыми цифрами), rate-limit 429 → паузы; подмена регистра
   датчика (CORE_TEMP `0x08..0x0B` = `FF FF FF FF`) → критическая
   температура → флаг в tick-ответе. `lessons/2026-11-04-hardware-spi-master-injection.md`.
4. **Логическая схема**: таблица истинности (xlsx/pdf) → булевы
   выражения → вычисление выхода → битовый вектор → ASCII.
   `lessons/2026-11-04-hardware-logic-circuit-truth-table.md`.
5. **MQTT**: анонимное подключение, подписка `#`/`$SYS/#`, retained-
   флаг, will/takeover, persistent session; креды `admin:jennifer`
   и др. `lessons/2026-11-04-iot-mqtt-broker-retained.md`.

## Грабли
- Инстанс может быть битым (брокер не маршрутизирует) — проверить
  простым тестом «A подписан/B публикует»; если не работает — не
  перебирать вслепую, а пересоздать инстанс.
- Креды проверять ПОСЛЕ connect(), иначе ложный Success.
- В задачах на прошивку не доверять «условию» — флаг в данных.
