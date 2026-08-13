#!/usr/bin/env python3
"""Порциите при теглене на залите бяха твърде големи.

200 идентификатора по 19 цифри правят адрес от над 4000 знака и сървърът
отговаря с 414. Порция от 40 дава около 900 знака — спокойно под всяка
разумна граница. Дванайсет заявки вместо три, но всичките минават.
"""
import sys

PATH = 'scripts/fetch_events.py'
MARK = 'CHUNK-40'


def main():
    src = open(PATH, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    old = """    for i in range(0, len(ids), 200):          # на порции, за да не е дълъг адресът
        chunk = ids[i:i + 200]"""
    new = """    # CHUNK-40 — по 200 идентификатора адресът минаваше 4000 знака и
    # сървърът връщаше 414. Четиридесет дават около 900 знака.
    for i in range(0, len(ids), 40):
        chunk = ids[i:i + 40]"""

    if old not in src:
        print('ГРЕШКА: не намирам цикъла с порциите')
        sys.exit(1)

    src = src.replace(old, new)
    src = src.replace("        time.sleep(0.5)\n    return locs",
                      "        time.sleep(0.35)\n    return locs")
    open(PATH, 'w', encoding='utf-8').write(src)
    print('порциите са по 40 идентификатора')


if __name__ == '__main__':
    main()
