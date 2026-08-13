#!/usr/bin/env python3
"""Междуградските да носят икона на автобус, не глобус.

Глобусът беше избран, докато 🚌 стоеше зает от градските линии. Те вече
ги няма, а глобус не говори „автобус" на никого — човек го търси по
превозното средство. Затова 🚍 (насрещен автобус) заема мястото:
различава се от градското 🚌 в старите снимки и се чете еднозначно.
"""
import sys

JS = 'transport.js'
MARK = 'INTL-BUS-ICON'


def main():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('иконата вече е сменена')
        return

    old = "    intl:    { icon:'🌍', title:'Intl. coaches',   gsw:'Uslandbüs'      }"
    new = ("    // INTL-BUS-ICON — глобусът не говори „автобус"; 🚌 се освободи,\n"
           "    // след като градските линии отпаднаха\n"
           "    intl:    { icon:'🚍', title:'Coach arrivals',  gsw:'Aachoendi Cars' }")

    if old not in src:
        # друг патч може да е пипал реда; хващаме го по-широко
        import re
        pat = re.compile(r"    intl:\s*\{[^}]*\}")
        if not pat.search(src):
            print('ГРЕШКА: не намирам реда за международните')
            sys.exit(1)
        src = pat.sub(new.split('\n')[-1], src, count=1)
        print('иконата е сменена (широко съвпадение)')
    else:
        src = src.replace(old, new)
        print('иконата е 🚍, надписът е Coach arrivals')

    open(JS, 'w', encoding='utf-8').write(src)


if __name__ == '__main__':
    main()
