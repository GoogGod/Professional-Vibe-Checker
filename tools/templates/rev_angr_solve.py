#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rev_angr_solve.py — шаблон: найти «правильный» ввод с помощью angr.
Адаптация: путь к бинарнику, адрес «успеха» (0x4012xx) и «провала».
Запуск: ~/ctfenv/bin/python rev_angr_solve.py [--find 0x4012xx]
"""
import argparse, angr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bin')
    ap.add_argument('--find', required=True, help='адрес успешной ветки')
    a = ap.parse_args()
    proj = angr.Project(a.bin, auto_load_libs=False)
    state = proj.factory.entry_state()
    sm = proj.factory.simulation_manager(state)
    sm.explore(find=int(a.find, 16))
    if sm.found:
        found = sm.found[0]
        print('FOUND!')
        print(found.posix.dumps(0))
    else:
        print('NOT FOUND')

if __name__ == '__main__':
    main()
