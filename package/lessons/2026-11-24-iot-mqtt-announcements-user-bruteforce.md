# MQTT/IoT: «туман» из сенсоров, подсказки announcements и перебор пользователя

Дата: 2026-11-24. Класс: hardware/IoT (easy). Статус: РЕШЕНО.
Платформа: обобщённо; инстанс → [instance].

## Суть
MQTT-брокер (Mosquitto 2.1.x, plain TCP). Флаг лежит в **retained**-сообщении
в защищённом топике `/users/<user>/secret`, доступном только после логина.

## Разведка
1. Анонимное подключение (allow_anonymous=true, но ACL read-only).
2. Подписка на `#` → виден «шум»: поток сенсоров `/sensors/{temperature,humidity,pressure}/data`
   и **редкий** топик `/announcements` (раз в ~20 с).
3. В announcements — подсказки сюжета: «i'm in /users/duck/secret»,
   «has anyone seen duck_fan?» → нужен **другой пользователь**, а не duck.
4. `$SYS/#` пустой; `/users/#` анонимно подписывается (SUBACK Granted),
   но доставки нет (ACL deny).
5. Запись анонимом запрещена: MQTT5 → PUBACK 0x87 (Not authorized);
   v3.1.1 — молчаливый дроп.

## Получение доступа (перебор пользователя)
- Брут по MQTT: множество параллельных CONNECT с парой (username, password)
  из rockyou (top-20k). Специфика: на успешный CONNECT брокер отвечает
  CONNACK reason 0x00; на неверные креды — 0x86 (Bad user name or password).
- Восприимчивость: ~90-100 попыток/с при 32 параллельных соединениях.
- Результат: `duck_fan : princess` (пароль из top-20k rockyou).
- ВАЖНО: Paho — `username_pw_set()` вызывать ДО `connect()`, иначе соединение
  анонимное и даёт ложный Success. MQTT5 CONNACK разбирать по remaining length,
  не читать байт вслепую.

## Чтение флага
```bash
mosquitto_sub -h [instance] -p [port] -u duck_fan -P princess \
  -t '/users/duck/secret' -v -C 1
```
Retained-сообщение приходит мгновенно: `{"message": "You found me!", "flag": "[FLAG]", ...}`.

## Уроки и грабли
- **Не отвлекаться на шум**: сенсоры (`value` 20–30) — декоративный «туман»,
  в них ничего не закодировано. Настоящая зацепка — подсказки (announcements),
  которые легко пропустить (редкие).
- Имена в подсказках — это указание на цель (duck vs duck_fan).
- Retained-сообщение читается после логина сразу.
- Инстанс может быть нестабилен: при пустом `#` проверить живость брокера,
  а не строить теории.
- Консистентный чек «жив ли брокер»: CONNACK v5 properties
  (ReceiveMaximum=20, TopicAliasMaximum=10) — сигнатура Mosquitto 2.1.x.

## Связанные уроки
- `lessons/2026-11-04-iot-mqtt-broker-retained.md` — базовые MQTT-приёмы
  (retained, will, креды, проверка «битого» инстанса).
