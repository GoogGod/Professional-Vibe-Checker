#!/usr/bin/env python3
"""mock_jury.py — репетиционный стенд A/D (класс jury/attack_data API), только stdlib.

Назначение: прогнать ВЕСЬ конвейер (farm.py + watch.py + эксплойты + сабмит +
Volga-петлю + откат патча) за день до турнира, без сети и жюри.

Поднимает на 127.0.0.1:
  :8020  jury-API: /api/v1/ctftime, /api/client/{config,teams,tasks}/,
        /api/v1/attack_data, PUT /api/v1/flags (X-Team-Token: mock-token),
        /public/scoreboard, /public/attacks, /public/scoreboard/teamtasks/<t>/<s>/logs
  :8021  сервис "notes" (CRUD-хранилище, уязвимость: проекция/LIKE-инъекция)
  :8022  сервис "vault" (секреты, уязвимость: предсказуемая сессия)
Плюс чекер-поток: каждый раунд кладёт флаги легитимным путём и читает их.

Симуляция боя (для тренировки Volga-петли и откатов):
  POST /admin/patch   {"service":"notes"}  → строгий режим: чекер падает (CORRUPT)
  POST /admin/rollback {"service":"notes"} → вернуть как было (статус восстанавливается)
  POST /admin/break   {"service":"vault"}  → сервис лежит (DOWN)
  POST /admin/fix     {"service":"vault"}  → поднять

Репетиция:
  python3 mock_jury.py &                       # стенд
  echo mock-token > token.txt
  AD_JURY=http://127.0.0.1:8020 AD_MY_IP=127.0.0.7 \
    AD_TOKEN_FILE=token.txt python3 farm.py    # молотилка (эксплойты в exploits/)
  AD_JURY=http://127.0.0.1:8020 AD_MY_IP=127.0.0.7 python3 watch.py
"""
import json, random, re, string, threading, time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROUND_SEC = 10          # раунд 10 с (в бою 60)
FLAG_ROUNDS = 5         # флаг живёт 5 раундов
TEAMS = [{"id": i, "name": f"team{i:02d}", "ip": f"127.0.0.{i}"} for i in range(1, 8)]
MY = TEAMS[-1]          # мы — последняя команда
TASKS = [{"id": 1, "name": "notes"}, {"id": 2, "name": "vault"}]
TOKEN = "mock-token"
FLAG_RE = re.compile(r"^[A-Z0-9]{8,64}=?$")

state = {  # всё состояние стенда
    "round": 0, "running": True,
    "flags": {},            # (team_id, task_id) -> {value, round, hint}
    "sla": {(t["id"], k["id"]): 0 for t in TEAMS for k in TASKS},
    "stolen_by": {t["id"]: 0 for t in TEAMS},
    "attacks": [],          # {round, victim_ip, task, data:{command, flag}}
    "patched": set(),       # задачи в строгом режиме
    "broken": set(),        # задачи «лежат»
    "checker_log": [],      # логи чекера для teamtasks/logs
}
NOTES, VAULT = {}, {}       # (team, title)->body ; (team, sess)->secret


def mkflag():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=31)) + "="


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def do_GET(self):
        u = self.path
        if u.startswith("/api/v1/ctftime"):
            self._json({"round": state["round"], "round_time": ROUND_SEC,
                        "round_time_left": max(0, ROUND_SEC - int(time.time() % ROUND_SEC))})
        elif u.startswith("/api/client/config/"):
            self._json({"game_running": state["running"], "real_round": state["round"],
                        "flag_lifetime": FLAG_ROUNDS, "round_time": ROUND_SEC})
        elif u.startswith("/api/client/teams/"):
            self._json(TEAMS)
        elif u.startswith("/api/client/tasks/"):
            self._json(TASKS)
        elif u.startswith("/api/v1/attack_data"):
            ad = {}
            for (tid, kid), f in state["flags"].items():
                name = TASKS[kid - 1]["name"]
                ad.setdefault(name, {})[TEAMS[tid - 1]["ip"]] = [f["hint"]]
            self._json(ad)
        elif u.startswith("/public/scoreboard/teamtasks/"):
            m = re.match(r"/public/scoreboard/teamtasks/(\d+)/(\d+)/logs", u)
            logs = [l for l in state["checker_log"] if l["team"] == int(m.group(1)) and l["task"] == int(m.group(2))][-20:]
            self._json({"logs": logs, "has_more": False})
        elif u.startswith("/public/attacks"):
            self._json(state["attacks"][-500:])
        elif u.startswith("/public/scoreboard"):
            teams = []
            for t in TEAMS:
                rows = []
                for k in TASKS:
                    if k["name"] in state["broken"]:
                        st, sname, msg = 105, "DOWN", "connection refused"
                    elif k["name"] in state["patched"]:
                        st, sname, msg = 104, "CORRUPT", "Could not put flag: strict mode"
                    else:
                        st, sname, msg = 101, "OK", ""
                    rows.append({"task_id": k["id"], "status": st, "status_name": sname,
                                 "public_message": msg})
                teams.append({"id": t["id"], "name": t["name"], "ip": t["ip"],
                              "score_display": state["stolen_by"][t["id"]] * 100 + state["sla"][(t["id"], 1)] + state["sla"][(t["id"], 2)],
                              "tasks": rows})
            self._json({"game": {"real_round": state["round"], "state": "running"}, "teams": teams, "tasks": TASKS})
        else:
            self._json({"error": "not found"}, 404)

    def do_PUT(self):
        if self.path.startswith("/api/v1/flags") and self.headers.get("X-Team-Token") == TOKEN:
            flags = self._body()
            resp = []
            for fl in flags if isinstance(flags, list) else []:
                hit = next(((tid, kid) for (tid, kid), f in state["flags"].items()
                            if f["value"] == fl and tid != MY["id"]), None)
                if not FLAG_RE.match(fl):
                    resp.append({"flag": fl, "msg": "Invalid flag format"})
                elif hit and MY["id"] not in (hit[0],):
                    state["stolen_by"][MY["id"]] += 1
                    state["attacks"].append({"round": state["round"], "victim_ip": TEAMS[hit[0] - 1]["ip"],
                                             "task": TASKS[hit[1] - 1]["name"],
                                             "data": {"command": f"exploit({TEAMS[hit[0]-1]['ip']}, 80XX)", "flag": fl}})
                    del state["flags"][hit]
                    resp.append({"flag": fl, "msg": "Flag accepted! Earned 100 flag points!"})
                elif next((f for (tid, kid), f in state["flags"].items() if f["value"] == fl and tid == MY["id"]), None):
                    resp.append({"flag": fl, "msg": "You can not submit your own flag"})
                else:
                    resp.append({"flag": fl, "msg": "Flag is too old or already stolen"})
            self._json(resp)
        else:
            self._json({"error": "auth"}, 403)

    def do_POST(self):
        u, b = self.path, self._body()
        if u.startswith("/admin/patch"):
            state["patched"].add(b.get("service")); self._json({"ok": True, "mode": "strict"})
        elif u.startswith("/admin/rollback"):
            state["patched"].discard(b.get("service")); self._json({"ok": True, "mode": "original"})
        elif u.startswith("/admin/break"):
            state["broken"].add(b.get("service")); self._json({"ok": True})
        elif u.startswith("/admin/fix"):
            state["broken"].discard(b.get("service")); self._json({"ok": True})
        else:
            self._json({"error": "not found"}, 404)


class NotesHandler(BaseHTTPRequestHandler):
    """Сервис notes: GET /notes?team=N&title=<LIKE-паттерн> — уязвимая проекция."""
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        team, title = int(q.get("team", ["1"])[0]), q.get("title", [""])[0]
        hits = [{"title": t, "body": v} for (tt, t), v in NOTES.items()
                if tt == team and (title in t or title == "*")]
        self._json({"notes": hits})

    def do_POST(self):
        b = self._body()
        NOTES[(int(b["team"]), b["title"])] = b["body"]
        self._json({"ok": True})

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}


class VaultHandler(NotesHandler):
    """Сервис vault: секреты по сессиям; сессия = md5(имя) — предсказуема."""
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        import hashlib
        q = parse_qs(urlparse(self.path).query)
        name = q.get("name", [""])[0]
        sess = hashlib.md5(name.encode()).hexdigest()[:12]
        self._json({"session": sess, "secret": VAULT.get((int(q.get("team", ["1"])[0]), sess))})


def checker():
    """Чекер: каждый раунд кладёт/читает флаги легитимным путём; режет SLA при поломке."""
    while True:
        time.sleep(ROUND_SEC)
        state["round"] += 1
        for t in TEAMS:
            for k in TASKS:
                key = (t["id"], k["id"])
                if k["name"] in state["broken"] or k["name"] in state["patched"]:
                    state["checker_log"].append({"team": t["id"], "task": k["id"],
                                                 "round": state["round"], "msg": "CHECK FAILED"})
                    continue
                # устаревшие флаги убираем (flag_lifetime)
                for fkey in [fk for fk, f in state["flags"].items()
                             if fk == key and state["round"] - f["round"] >= FLAG_ROUNDS]:
                    del state["flags"][fkey]
                hint, flag = "hint-" + "".join(random.choices(string.ascii_lowercase, k=6)), mkflag()
                if k["name"] == "notes":
                    NOTES[key[:1] + (hint,)] = flag
                else:
                    import hashlib
                    sess = hashlib.md5(hint.encode()).hexdigest()[:12]
                    VAULT[(t["id"], sess)] = flag
                state["flags"][key] = {"value": flag, "round": state["round"], "hint": hint}
                state["sla"][key] += 1
                state["checker_log"].append({"team": t["id"], "task": k["id"],
                                             "round": state["round"], "msg": "CHECK OK"})


def main():
    threading.Thread(target=checker, daemon=True).start()
    servers = []
    for port, h in ((8020, Handler), (8021, NotesHandler), (8022, VaultHandler)):
        srv = ThreadingHTTPServer(("127.0.0.1", port), h)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
    print("mock jury up: :8020 jury, :8021 notes, :8022 vault; token=mock-token; мы =", MY["ip"])
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    print("mock jury: :8020 jury, :8021 notes, :8022 vault; token=mock-token; мы =", MY["ip"])
    main()
