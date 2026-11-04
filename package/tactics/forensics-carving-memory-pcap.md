# Форензика: pcap, память, диск, стего — тактика

Когда применять: дампы трафика, образы памяти, файловые системы, картинки.

## Порядок действий
1. **pcap**: сначала stats/протоколы; «важные файлы» = HTTP-объекты
   (вытащить, посмотреть OCR). `lessons/2026-10-23-mitm-pcap-http-object-ocr-flag.md`.
   Covert-каналы: порядок/значения srcport/dstport, LSB в данных.
   `lessons/2026-10-23-udp-port-covert-channel.md`, `lessons/2026-10-23-pcap-lsb-col0-custom-b64-alphabet.md`.
2. **Память**: Volatility 3 (pslist, memdump, netscan, filescan); искать
   уникальные строки в vmem; следы ALPC/IPC (окна, объекты).
   `lessons/2026-11-01-memory-forensics-volatility-basics.md`,
   `lessons/2026-11-01-forensics-alpc-memory-puzzle.md`.
3. **Диск**: ext4/ntfs, удалённые файлы (gzip-карвинг из unallocated),
   evtx (DeviceName→DriveName). `lessons/2026-10-23-ext4-deleted-files-gzip-carving.md`,
   `lessons/2026-10-23-evtx-devicename-drivename-ntfs98.md`.
4. **Стего**: проверить метаданные, alpha-канал, LSB по карте, GAN-инверсию
   (MSE недостаточен), пазл-сборку по краям.
   `lessons/2026-10-23-stego-alpha-map-lsb.md`, `lessons/2026-10-28-cursed-stego-gan-inversion.md`,
   `lessons/2026-11-01-stego-jigsaw-reconstruct.md`.

## Грабли
- Шум (DDoS) скрывает сигнал — искать *уникальное*, а не самое частое.
- Флаг может быть разбит между кучей процесса и недоступным сервисом.
- Сначала разложить задачу на «хвосты» (что осталось необъяснённым).
