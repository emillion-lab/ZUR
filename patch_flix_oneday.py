#!/usr/bin/env python3
"""Международните автобуси: само днешният ден.

В лога на първото пускане всеки град даваше по едно „Bad Request".
Причината е втората заявка — за утре. FlixBus я отказва при това
съчетание от параметри, а днешният ден и без това дава шейсетина курса,
което покрива смяната. Утрешните ще дойдат с утрешното пускане.

Махат се 22 излишни заявки и логът се изчиства.
"""
import sys

PATH = 'scripts/fetch_flixbus.py'
MARK = 'ONE-DAY'


def main():
    src = open(PATH, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    old = """    today = datetime.date.today()
    days = [today, today + datetime.timedelta(days=1)]"""
    new = """    # ONE-DAY — заявката за утре връща 400 при това съчетание от
    # параметри; днешният ден дава шейсетина курса и стига за смяната.
    today = datetime.date.today()
    days = [today]"""

    if old not in src:
        print('ГРЕШКА: не намирам списъка с дни')
        sys.exit(1)

    src = src.replace(old, new)
    open(PATH, 'w', encoding='utf-8').write(src)
    print('само днешният ден — 22 заявки по-малко')


if __name__ == '__main__':
    main()
