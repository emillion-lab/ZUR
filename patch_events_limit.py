#!/usr/bin/env python3
"""Седем събития стигат.

Дългият списък не помага: шофьорът гледа екрана между два курса и му
трябва решение, не справочник. Затова при събитията се показват първите
седем по край, а при останалите видове остава по-дългият списък, защото
влаковете идват на всеки няколко минути и подредбата има смисъл.
"""
import sys

JS = 'transport.js'
MARK = 'EVENTS-LIMIT'


def main():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    old = "    c.rows.forEach(function(r){"
    new = """    // EVENTS-LIMIT — седем реда се обхващат с един поглед
    var list = (open === 'events') ? c.rows.slice(0, 7) : c.rows;
    list.forEach(function(r){"""

    if old not in src:
        print('ГРЕШКА: не намирам обхождането на редовете')
        sys.exit(1)

    src = src.replace(old, new, 1)
    open(JS, 'w', encoding='utf-8').write(src)
    print('събитията са ограничени до седем')


if __name__ == '__main__':
    main()
