#!/usr/bin/env python3
"""Vibe Check — агрегация прогонов и сводка A/B (без внешних зависимостей).

Читает runs/**/run.md (front matter шаблона run-log), пишет в --out: runs.csv и summary.md,
печатает сводку в stdout.

Usage:
  python -X utf8 eval/scripts/score.py --runs eval/runs --out eval/results
  python -X utf8 eval/scripts/score.py --runs eval/examples --out eval/results-demo
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import pathlib
import statistics


def parse_run(path: str):
    d = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        lv = v.lower()
        if lv in ("true", "false"):
            d[k] = lv == "true"
        elif v == "":
            d[k] = None
        else:
            try:
                d[k] = float(v) if "." in v else int(v)
            except ValueError:
                d[k] = v
    d["_path"] = str(path)
    return d


def med(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return round(statistics.median(vals), 2) if vals else None


def sign_p(wins: int, losses: int):
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n) * 2
    return round(min(p, 1.0), 4)


def fmt(x):
    return "" if x is None else x


COLS = [
    "run_id", "batch", "task", "branch", "model", "solved", "flag_confirmed",
    "duration_min", "steps", "tokens", "first_useful_step", "first_correct_class_step",
    "slop_flags", "rabbit_holes", "false_claims", "progress",
    "isolation_check", "contaminated", "invalid", "notes", "_path",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = []
    for root, _dirs, files in os.walk(a.runs):
        for fn in files:
            if fn == "run.md":
                d = parse_run(os.path.join(root, fn))
                if d and d.get("branch"):
                    rows.append(d)

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    rows.sort(key=lambda x: (str(x.get("batch")), str(x.get("task")), str(x.get("branch"))))
    with open(out / "runs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows)

    invalid = [r for r in rows if r.get("invalid")]
    contaminated = [r for r in rows if r.get("contaminated")]
    core = [r for r in rows if not r.get("invalid") and not r.get("contaminated")]

    def branch_rows(b):
        return [r for r in core if str(r.get("branch")).upper() == b]

    def solved(r):
        return bool(r.get("solved") or r.get("flag_confirmed"))

    def agg(rs):
        s = [r for r in rs if solved(r)]
        return {
            "n": len(rs),
            "solved": len(s),
            "dur": med([r.get("duration_min") for r in s]),
            "steps": med([r.get("steps") for r in s]),
            "fus": med([r.get("first_useful_step") for r in rs]),
            "slop": sum(int(r.get("slop_flags") or 0) for r in rs),
            "rabbit": sum(int(r.get("rabbit_holes") or 0) for r in rs),
            "false": sum(int(r.get("false_claims") or 0) for r in rs),
            "prog2": sum(1 for r in rs if r.get("progress") == 2),
        }

    agA, agB = agg(branch_rows("A")), agg(branch_rows("B"))

    by_task = {}
    for r in core:
        by_task.setdefault(str(r.get("task")), {})[str(r.get("branch")).upper()] = r

    wins = losses = ties = 0
    pair_lines = []
    for t, d in sorted(by_task.items()):
        ra, rb = d.get("A"), d.get("B")
        if not ra or not rb:
            pair_lines.append(f"| {t} | pending | - | - | - |")
            continue
        sa, sb = solved(ra), solved(rb)
        if sa and not sb:
            marker, wins = "A+", wins + 1
        elif sb and not sa:
            marker, losses = "B+", losses + 1
        else:
            marker, ties = "tie", ties + 1
        fa, fb = ra.get("first_useful_step"), rb.get("first_useful_step")
        fm = "="
        if isinstance(fa, (int, float)) and isinstance(fb, (int, float)):
            fm = "A<<" if fa < fb else ("B<<" if fb < fa else "=")
        pair_lines.append(f"| {t} | {marker} | {fmt(fa)} | {fmt(fb)} | {fm} |")

    p = sign_p(wins, losses)

    L = [
        "# Vibe Check — сводка",
        "",
        f"Прогонов: {len(rows)} (core: {len(core)}, invalid: {len(invalid)}, contaminated: {len(contaminated)})",
        "",
        "| Ветка | N | solved | med duration | med steps | med first_useful_step | Σ slop | Σ rabbit | Σ false | progress=2 |",
        "|---|---|---|---|---|---|---|---|---|---|",
        f"| A | {agA['n']} | {agA['solved']} | {fmt(agA['dur'])} | {fmt(agA['steps'])} | {fmt(agA['fus'])} | {agA['slop']} | {agA['rabbit']} | {agA['false']} | {agA['prog2']} |",
        f"| B | {agB['n']} | {agB['solved']} | {fmt(agB['dur'])} | {fmt(agB['steps'])} | {fmt(agB['fus'])} | {agB['slop']} | {agB['rabbit']} | {agB['false']} | {agB['prog2']} |",
        "",
        f"Win-rate (solved): A+ = {wins}, B+ = {losses}, ties = {ties}; знаковый тест p = {fmt(p)} (мягкий индикатор, малые N).",
        "",
        "| Задача | Итог (solved) | first_useful A | first_useful B | сравнение |",
        "|---|---|---|---|---|",
        *pair_lines,
    ]
    text = "\n".join(L) + "\n"
    (out / "summary.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())