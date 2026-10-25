#!/usr/bin/env python3
"""watch.py — вахтёр A/D v2: статусы своих сервисов + АНТИ-ДРЕНАЖ.

Уроки турнира: (1) Volga — свой сервис не-OK → флаги с него сгорают, алерт немедленно;
(2) статус OK ≠ нас не доят (у нас выкачали 609 флагов при зелёных статусах) —
поэтому следим за /public/attacks: flag_stolen против нас = кормушка открыта.
Запуск: setsid nohup python3 watch.py >> logs/watch.log 2>&1 &
Конфиг: env AD_JURY, AD_MY_IP.
Логи: logs/alerts.log.
"""
import json, os, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
JURY = os.environ.get("AD_JURY", "http://10.10.10.10")
MY_IP = os.environ.get("AD_MY_IP", "10.80.1.2")
ALERTF = os.path.join(BASE, "logs", "alerts.log")
LOG = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)


def alert(msg):
    print("ALERT!", msg, flush=True)
    os.makedirs(os.path.dirname(ALERTF), exist_ok=True)
    with open(ALERTF, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def get(url, timeout=15):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_err": str(e)[:120]}


def main():
    last_bad, lost_total, last_rnd = {}, 0, None
    while True:
        sb = get(JURY + "/public/scoreboard")
        if "_err" in sb:
            LOG("scoreboard err", sb["_err"])
            time.sleep(30)
            continue
        game, me = sb.get("game", {}), next(
            (t for t in (sb.get("teams") or []) if t.get("ip") == MY_IP), None)
        rnd = game.get("real_round")
        if me:
            tasks = {t["id"]: t["name"] for t in (sb.get("tasks") or [])}
            line = []
            for tt in me.get("tasks", []):
                name = tasks.get(tt["task_id"], tt["task_id"])
                stname = tt.get("status_name", "?")
                line.append(f"{name}={stname}")
                if tt.get("status") != 101:  # 101 = OK (Forcad-класс; сверяй с полем)
                    key = f"{name}:{stname}"
                    if last_bad.get(name) != key:
                        alert(f"MY SERVICE {name} -> {stname} "
                              f"({tt.get('public_message','')}) round={rnd} | Volga: флаги с него сгорают; откат патча?")
                        last_bad[name] = key
                else:
                    last_bad.pop(name, None)
            LOG(f"round={rnd} state={game.get('state')} score={me.get('score_display')} | " + " ".join(line))
        # анти-дренаж: считаем кражи у нас даже при зелёных статусах
        if rnd is not None and (last_rnd is None or rnd != last_rnd):
            a = get(JURY + f"/public/attacks?since_round={last_rnd or 0}&limit=1000")
            lost_now = 0
            for ev in a if isinstance(a, list) else (a.get("attacks") or a.get("events") or []):
                data = ev.get("data") or {}
                if str(data.get("victim") or data.get("team_ip") or ev.get("victim")) == MY_IP:
                    lost_now += 1
            if lost_now:
                lost_total += lost_now
                if lost_now >= 3:  # порог: 3+ кражи за раунд = систематический дренаж
                    svc = next((ev.get("task") or (ev.get("data") or {}).get("task")
                                for ev in (a if isinstance(a, list) else a.get("attacks", []))
                                if str((ev.get("data") or {}).get("victim") or ev.get("victim")) == MY_IP), "?")
                    alert(f"DRAIN: украли {lost_now} за раунд (всего {lost_total}), сервис={svc} — "
                          f"статус может быть OK! Закрыть кормушку / канализировать хранилище.")
            last_rnd = rnd
        time.sleep(30)


if __name__ == "__main__":
    main()
