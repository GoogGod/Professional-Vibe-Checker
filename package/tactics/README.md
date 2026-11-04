# Тактики и чек-листы по темам

Формат: один файл на тему; обновляй существующие, не создавай дубли.
Тактики — это «что пробовать и в каком порядке», уроки — детали приёмов.

| Тактика | Когда применять |
|---|---|
| `crypto-oracle-playbook.md` | Сервис отвечает да/нет или расшифровывает: padding/LSB/каскадный/ECB-оракулы, BSGS, length extension, many-time pad, LFSR |
| `web-injection-ssti-ssrf-bot.md` | Веб: SSTI, mass assignment, SSRF→RCE-цепочки, XSS + headless-бот |
| `pwn-exploitation-chain.md` | Бинарные сервисы: GOT overwrite, heap/ROP, фильтры, kernel/ioctl |
| `mobile-apk-analysis.md` | Android: APK, SharedPreferences/sealed-prefs, SQLite, stateful-крипта |
| `forensics-carving-memory-pcap.md` | pcap/память/диск/стего: объекты, OCR, covert-каналы, Volatility, карвинг, LSB/GAN/пазл |
| `hardware-fpga-radio-dsp.md` | FPGA iCE40, Verilog, радио-сэмплы, DSP |
| `hardware-embedded-iot.md` | Proteus/AVR-прошивки, логические схемы, SPI side-channel, MQTT |
| `reverse-vm-patching.md` | VM-протекторы, RISC-V VLE, PyInstaller, патчинг |

Правила: без значений флагов; без названий площадок; относительные пути;
ссылки на уроки — через `lessons/<имя>.md`.
