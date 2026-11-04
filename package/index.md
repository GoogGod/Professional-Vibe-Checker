# Index — реестр записей базы

Формат строки: `дата · тип · путь · краткий итог`. Новые записи добавляй сверху.

## Записи
- 2026-11-04 · lesson · `lessons/2026-11-04-hardware-logic-circuit-truth-table.md` · Логическая схема: восстановление булевой логики по таблице истинности
- 2026-11-04 · lesson · `lessons/2026-11-04-hardware-proteus-avr-firmware.md` · Proteus 8 + AVR: разбор проекта САПР и прошивки (Intel HEX)
- 2026-11-04 · lesson · `lessons/2026-11-04-hardware-spi-master-injection.md` · SPI / аппаратная инъекция: side-channel PIN + подмена firmware регистра
- 2026-11-04 · lesson · `lessons/2026-11-04-iot-mqtt-broker-retained.md` · MQTT/IoT: разведка брокера, креды и retained-флаг
- 2026-11-04 · tactic · `tactics/hardware-embedded-iot.md` · Hardware/Embedded/IoT: схемы, прошивки, шины, MQTT
- 2026-10-30 · tool · `toolbox/net_session.py` · Интерактивный TCP-клиент без PTY (Windows-safe) для netcat-челленджей: `host`/`port` + шаги `interactions` (`expect`-regex, `send`, `wait`); без шагов — читает до таймаута; возвращает журнал обмена.

## Как добавлять

1. Создай запись в `lessons/` (шаблон — в скилле `hermes-knowledge-loop`).
2. Добавь строку сюда (сверху списка).
3. Если приём повторяется — обнови файл в `tactics/`; если скрипт >20 строк — положи в `toolbox/`.

Правила: без значений флагов; без названий площадок; относительные пути.