# Урок: EVTX — DeviceName → DriveName (Volume GUID) по Microsoft-Windows-Ntfs 98

Дата: 2026-10-23 · Категория: forensics/windows-evtx · Уровень: easy

## Кейс

- Дан один .evtx (System-подобный журнал, 713 записей, смесь провайдеров: WindowsUpdateClient, Kernel-General, SCM, Ntfs и пр.). Задание: устройству `\Device\HarddiskVolume4` найти DriveName → ответ `ФОРМАТ{volume-id}`.
- Решение в один заход: `python-evtx` (pip install --break-system-packages) → дамп всех записей в XML → `grep -B3 -A3 'HarddiskVolume4'`.
- Искомая пара лежит в EventData одного события: `<Data Name="DriveName">\\?\Volume{GUID}</Data><Data Name="DeviceName">\Device\HarddiskVolume4</Data>` — провайдер **Microsoft-Windows-Ntfs, EventID 98** (том смонтирован/проверен), 3 вхождения, GUID идентичный — стабильно.
- Ловушка сравнения: у остальных событий DriveName = `C:` (системный том по букве) — «записывающее устройство» опознаётся именно по GUID-форме `\\?\Volume{...}` без буквы (внешний/съёмный том без назначенной буквы или вне mounted-letters).

## Команды-якоря

- `pip install --break-system-packages python-evtx`
- python: `from Evtx.Evtx import Evtx; [print(r.xml()) for r in Evtx(path).records()]`
- `grep -B3 -A3 'HarddiskVolume[0-9]' dump.xml` → соседний `<Data Name="DriveName">`
- Быстрая разведка канала: `grep -o '<Provider Name="[^"]*"' dump.xml | sort | uniq -c`

## Связь с базой

- Дополняет host-artifacts-playbook: для evtx не нужен Wevtutil/Windows — python-evtx в WSL достаточно; сопоставление DeviceName↔Volume GUID — стандартный пивот USB-форензики.
