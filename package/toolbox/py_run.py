# -*- coding: utf-8 -*-
"""py_run: локальный запуск Python-кода с поддержкой stdin/args/таймаута.

Параметры — JSON в stdin:
  code (str, опц.) — исходник Python (если нет, читает файл),
  file (str, опц.) — путь к .py-файлу,
  args (list[str], опц.) — аргументы командной строки,
  stdin (str, опц.) — данные на стандартном вводе,
  timeout (float, опц., default 60) — таймаут секунд.
Возвращает {"stdout":..., "stderr":..., "exit":..., "timed_out": bool}.
"""
import json
import subprocess
import sys

TIMEOUT_MARGIN = 5.0


def main():
    raw = sys.stdin.buffer.read().decode("utf-8-sig")
    try:
        p = json.loads(raw) if raw.strip() else {}
    except Exception:
        p = {}
    code = p.get("code")
    file_ = p.get("file")
    args = p.get("args") or []
    stdin_data = p.get("stdin") or ""
    timeout = float(p.get("timeout", 60))
    if not code and not file_:
        error = {"error": "нужен code или file"}
        print(json.dumps(error, ensure_ascii=False))
        return
    script_args = []
    if file_:
        script_args.append(file_)
    else:
        script_args.append("-c")
        script_args.append(code)
    script_args.extend(args)
    try:
        r = subprocess.run(
            [sys.executable] + script_args,
            input=stdin_data.encode("utf-8") if isinstance(stdin_data, str) else stdin_data,
            capture_output=True,
            timeout=timeout + TIMEOUT_MARGIN,
        )
        print(json.dumps({
            "stdout": r.stdout.decode("utf-8", errors="replace"),
            "stderr": r.stderr.decode("utf-8", errors="replace"),
            "exit": r.returncode,
            "timed_out": False,
        }, ensure_ascii=False, indent=2))
    except subprocess.TimeoutExpired:
        print(json.dumps({
            "error": f"таймаут {timeout}с",
            "timed_out": True,
        }, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
