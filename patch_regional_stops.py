#!/usr/bin/env python3
"""Регионалните автобуси: правилните спирки и по-разумен филтър.

Таблото остана празно, защото сложих гарите (Zürich HB, Oerlikon), а
таблото на гарата връща влакове — автобусите спират на отделни
автобусни площадки със собствени имена. Затова се връщат истинските
автобусни възли, плюс тези на края на града, откъдето идват хората от
околните общини.

Филтърът също се разхлабва: остава отсяването на едноцифрените градски
линии, но двуцифрените вече минават, защото част от регионалните линии
на ZVV са двуцифрени (напр. 89, 94), а PostAuto носи име вместо номер.

Бележка по същество: в Швейцария между градовете се пътува с влак, не с
автобус. Затова тук ще има по-малко записи, отколкото при влаковете —
това е вярно отражение на действителността, а не липса на данни.
"""
import sys

JS = 'transport.js'
MARK = 'REGIONAL-STOPS-V2'


def main():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    old_stops = """    // Регионалните спират на гаровите площади, не по градските спирки
    bus: [
      ['Zürich HB',              'HB'],
      ['Zürich, Bahnhofquai/HB', 'Bahnhofquai'],
      ['Zürich Oerlikon',        'Oerlikon'],
      ['Zürich, Bellevue',       'Bellevue'],
      ['Zürich Flughafen',       'Flughafen']
    ],"""

    new_stops = """    // REGIONAL-STOPS-V2 — таблото на гарата връща влакове; автобусите
    // имат собствени спирки. Тези тук са автобусните възли, откъдето
    // идват хората от околните общини.
    bus: [
      ['Zürich, Bahnhofquai/HB',   'Bahnhofquai'],
      ['Zürich, Bellevue',         'Bellevue'],
      ['Zürich, Central',          'Central'],
      ['Zürich, Klusplatz',        'Klusplatz'],
      ['Zürich, Bucheggplatz',     'Bucheggplatz'],
      ['Zürich Flughafen, Bahnhof','Flughafen'],
      ['Zürich Oerlikon, Bahnhof', 'Oerlikon']
    ],"""

    if old_stops not in src:
        print('ГРЕШКА: не намирам списъка със спирки за автобусите')
        sys.exit(1)
    src = src.replace(old_stops, new_stops)

    # филтърът: пада само едноцифреното, останалото минава
    old_f = """            var num = String(e.number || '').trim();
            if(/^\\d{1,2}$/.test(num)) return null;"""
    new_f = """            // Едноцифрените са същински градски; двуцифрените вече
            // минават, защото част от регионалните на ZVV са такива.
            var num = String(e.number || '').trim();
            if(/^\\d$/.test(num)) return null;
            // тези три са трамвайни заместващи линии в центъра
            if(num === '31' || num === '46' || num === '72') return null;"""
    if old_f in src:
        src = src.replace(old_f, new_f)

    open(JS, 'w', encoding='utf-8').write(src)
    print('спирките са автобусни възли; филтърът е разхлабен')


if __name__ == '__main__':
    main()
