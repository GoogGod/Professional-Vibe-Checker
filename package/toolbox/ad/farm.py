#!/usr/bin/env python3
"""farm.py — молотилка A/D (skipper/Forcad-класс API), полевая версия v2.

Цикл: config → ctftime(синхронизация с раундом) → attack_data → exploits/* →
      очередь флагов → батч PUT /api/v1/flags (дедуп, лимит/мин).
Эксплойты: exploits/exploit_<service>.py с SERVICE, PORT и
      def exploit(host, port, hints) -> str | list[str] | None
Запуск (демон, переживает таймауты платформы):
      setsid nohup python3 farm.py >> logs/farm.log 2>&1 &
Конфиг: env AD_JURY, AD_MY_IP, AD_TOKEN_FILE (или правь константы ниже).

Отличия v2 (уроки первого турнира):
  - синхронизация с границей раунда (флаг живёт N раундов — крадём в первые секунды);
  - статистика линий (попытки/флаги) + подсказка RETIRE для балласта
    (N циклов → 0 флагов → линия жрёт слоты и стареет чужие флаги);
  - счётчик дренажа из /public/attacks (нас доят, пока статус OK — ловим по flag_stolen);
  - seen персистится на диск (рестарт не теряет дедуп).
"""
import json, os, re, sys, time, threading, importlib.util
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
JURY = os.environ.get("AD_JURY", "http://10.10.10.10")
MY_IP = os.environ.get("AD_MY_IP", "10.80.1.2")
TOKEN_FILE = os.environ.get("AD_TOKEN_FILE", os.path.join(BASE, "..", "token.txt"))
SEEN_FILE = os.path.join(BASE, "logs", "seen_flags.txt")
FLAG_RE = re.compile(r"^[A-Z0-9]{31}=$")          # формат — из /api/client/config/!
CYCLE_SLEEP = 10                                    # сек между циклами (вне round-sync)
SUBMIT_PER_MIN = 100                                # лимит чести: <120/мин
RETIRE_AFTER = 25                                   # попыток без флагов → подсказка RETIRE
_seen = set()
_lock = threading.Lock()
_stats = {}  # fname -> {"try": n, "flag": n, "first": ts}
LOG = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)


def http(method, url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if data is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, data, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


def jget(url, timeout=20):
    st, body = http("GET", url, timeout=timeout)
    if st == 200 and body.strip():
        try:
            return json.loads(body)
        except Exception:
            return {}
    return {}


def token():
    return open(TOKEN_FILE).read().strip()


def load_seen():
    try:
        return set(open(SEEN_FILE).read().split())
    except FileNotFoundError:
        return set()


def save_seen(flags):
    with open(SEEN_FILE, "a") as f:
        for fl in flags:
            f.write(fl + "\n")


def submit_batch(flags):
    if not flags:
        return 0
    flags = [f for f in flags if FLAG_RE.match(f)][:60]
    if not flags:
        return 0
    st, body = http("PUT", JURY + "/api/v1/flags", data=flags,
                    headers={"X-Team-Token": token()})
    LOG("SUBMIT", len(flags), "->", st, body[:200])
    try:  # rejected → seen (не слать повторно; «already/too old/own» — не ошибки)
        for item in json.loads(body):
            fl, msg = item.get("flag"), str(item.get("msg", ""))
            if fl and any(k in msg for k in ("too old", "already", "own flag", "unknown", "Invalid")):
                _seen.add(fl)
    except Exception:
        pass
    return len(flags)


def load_exploits():
    exps, d = [], os.path.join(BASE, "exploits")
    if not os.path.isdir(d):
        return exps
    for fn in sorted(os.listdir(d)):
        if not (fn.startswith("exploit_") and fn.endswith(".py")):
            continue
        try:
            spec = importlib.util.spec_from_file_location(fn[:-3], os.path.join(d, fn))
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            exps.append((m.SERVICE, m.PORT, m.exploit, fn))
            LOG("exploit loaded:", fn, m.SERVICE, m.PORT)
        except Exception as e:
            LOG("exploit load FAIL", fn, repr(e)[:120])
    return exps


def round_sync():
    """Ждём границу раунда: кража в первые секунды раунда = не «already stolen»."""
    ct = jget(JURY + "/api/v1/ctftime")
    left = ct.get("round_time_left") or ct.get("time_left") or ct.get("seconds_to_next_round")
    if isinstance(left, (int, float)) and 1 < left < 60:
        LOG(f"round-sync: sleep {int(left)}s до границы раунда {ct.get('round', '?') + 1}")
        time.sleep(int(left))
        return True
    return False


def drain_report(since_round):
    """Анти-дренаж: статус OK ≠ нас не доят. Считаем flag_stolen против нас."""
    a = jget(JURY + f"/public/attacks?since_round={since_round}&limit=500")
    lost = 0
    for ev in a if isinstance(a, list) else (a.get("attacks") or a.get("events") or []):
        data = ev.get("data") or {}
        victim = data.get("victim") or data.get("team_ip") or ev.get("victim")
        if str(victim) == MY_IP:
            lost += 1
    if lost:
        LOG(f"DRAIN: у нас украли {lost} флагов (since round {since_round}) — чинить кормушку, а не смотреть на статус!")
    return lost


def main():
    global _seen
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    _seen = load_seen()
    exploits = load_exploits()
    LOG("farm start; exploits:", len(exploits), "seen:", len(_seen))
    last_submit_min, submitted_this_min = 0, 0
    last_drain_round = None
    while True:
        if int(time.time() // 60) != last_submit_min:
            last_submit_min, submitted_this_min = int(time.time() // 60), 0
        try:
            cfg = jget(JURY + "/api/client/config/")
            if not cfg.get("game_running", True):
                LOG("game not running; sleep 20")
                time.sleep(20)
                continue
            rnd = cfg.get("real_round") or jget(JURY + "/api/v1/ctftime").get("round")
            if last_drain_round is None:
                last_drain_round = max(0, (rnd or 0) - 2)
            round_sync()
            drain_report(last_drain_round)
            last_drain_round = rnd or last_drain_round

            ad = jget(JURY + "/api/v1/attack_data")
            if ad:
                LOG("round", rnd, "attack_data:", {k: len(v) for k, v in ad.items()})

            jobs = []
            for service, ipmap in ad.items():
                for ip, hints in ipmap.items():
                    if ip == MY_IP:
                        continue
                    for (svc, port, fn, fname) in exploits:
                        if svc == service:
                            jobs.append((ip, port, hints, fn, fname))

            def run_job(job):
                ip, port, hints, fn, fname = job
                out = []
                with _lock:
                    s = _stats.setdefault(fname, {"try": 0, "flag": 0})
                    s["try"] += 1
                try:
                    r = fn(ip, port, hints)
                    got = [r] if isinstance(r, str) else list(r) if isinstance(r, (list, tuple)) else []
                    for fl in got:
                        if FLAG_RE.match(fl):
                            out.append((fname, ip, fl))
                except Exception as e:
                    LOG("exploit err", fname, ip, repr(e)[:100])
                return out

            flags_now = []
            with ThreadPoolExecutor(max_workers=14) as pool:
                for res in pool.map(run_job, jobs):
                    for fname, ip, fl in res:
                        with _lock:
                            if fl not in _seen:
                                _seen.add(fl)
                                flags_now.append(fl)
                                _stats[fname]["flag"] += 1
                                LOG("FLAG!", fname, ip, fl)
            if flags_now and submitted_this_min < SUBMIT_PER_MIN:
                submitted_this_min += submit_batch(flags_now)
                save_seen(flags_now)
            # линиям-балластом — подсказка (правило: N попыток → 0 флагов → отключить)
            for fname, s in _stats.items():
                if s["try"] >= RETIRE_AFTER and s["flag"] == 0:
                    LOG(f"RETIRE? {fname}: {s['try']} попыток, 0 флагов — балласт, стареет чужие флаги")
                    s["try"] = 0  # не спамить; через RETIRE_AFTER снова напомнит
        except Exception as e:
            LOG("cycle error", repr(e)[:200])
        time.sleep(CYCLE_SLEEP)


if __name__ == "__main__":
    main()
