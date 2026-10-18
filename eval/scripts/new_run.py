#!/usr/bin/env python3
"""Vibe Check — каркас прогона.

Создаёт runs/<batch>/<task>/<branch>/ (work/, [knowledge-writeback/]) и run.md из шаблона.

Usage:
  python -X utf8 eval/scripts/new_run.py --batch pilot-01 --task web-01 --branch A
  python -X utf8 eval/scripts/new_run.py --batch pilot-01 --task web-01 --branch B --seq 2
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_ROOT = (HERE / ".." / "runs").resolve()
TEMPLATE = (HERE / ".." / "templates" / "run-log.md")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--branch", required=True, choices=["A", "B", "C"])
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--seq", type=int, default=1, help="номер прогона в паре (по умолчанию 1)")
    a = ap.parse_args()

    branch = a.branch.upper()
    date = datetime.date.today().isoformat()
    run_id = f"{date}-{a.task}-{branch}" + ("" if a.seq == 1 else f"-r{a.seq}")

    run_dir = pathlib.Path(a.root) / a.batch / a.task / branch
    if (run_dir / "run.md").exists():
        print(f"already exists: {run_dir / 'run.md'} — не перезаписываю", file=sys.stderr)
        return 1
    (run_dir / "work").mkdir(parents=True, exist_ok=True)
    if branch == "A":
        (run_dir / "knowledge-writeback").mkdir(parents=True, exist_ok=True)

    text = TEMPLATE.read_text(encoding="utf-8")
    for k, v in {
        "example-000-A": run_id,
        "<batch-id>": a.batch,
        "<task-id>": a.task,
        "<run_id>": run_id,
        "branch: A": f"branch: {branch}",
        "started: <ISO8601>": f"started: {datetime.datetime.now().isoformat(timespec='seconds')}",
    }.items():
        text = text.replace(k, v)
    (run_dir / "run.md").write_text(text, encoding="utf-8")

    print(f"created: {run_dir}")
    print("  run.md -> заполнить модель/харнесс/лимиты и вперёд")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())