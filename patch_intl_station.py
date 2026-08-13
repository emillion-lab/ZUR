#!/usr/bin/env python3
"""Международните: спирката вместо излишното „Zurich".

В списъка пишеше „→ Zurich" на всеки ред, което не носи сведение —
всички пристигат в Цюрих, затова са в това табло. Полезното е къде
точно слизат: Sihlquai. Скрейпърът вече го записва в `station`.

Освен това редовете стават докосваеми като останалите: докосването
затваря панела и завежда картата до автогарата, както е в BAK.
"""
import sys

PY = 'scripts/fetch_flixbus.py'
JS = 'transport.js'
MARK = 'STATION-NOT-CITY'


def patch_scraper():
    """Спирката да не пада на името на града."""
    src = open(PY, encoding='utf-8').read()
    if MARK in src:
        print('скрейпърът вече е поправен')
        return

    old = """                'station': (arr.get('station_name')
                            or arr.get('city_name') or 'Sihlquai'),"""
    new = """                # STATION-NOT-CITY — city_name дава „Zurich", което е
                # безполезно: всички редове тук пристигат в Цюрих.
                # Автогарата е Sihlquai, освен ако някой ден не добавят друга.
                'station': (arr.get('station_name') or 'Sihlquai'),"""

    if old in src:
        src = src.replace(old, new)
        open(PY, 'w', encoding='utf-8').write(src)
        print('скрейпърът: спирката вместо града')
    else:
        # друга сесия е пренаписвала този участък; отбелязваме без провал
        if 'city_name' in src:
            src = src.replace("or arr.get('city_name') or 'Sihlquai'",
                              "or 'Sihlquai'  # STATION-NOT-CITY")
            open(PY, 'w', encoding='utf-8').write(src)
            print('скрейпърът: махнат city_name')
        else:
            print('скрейпърът: няма какво да се маха')


def patch_panel():
    """Показваме спирката и правим реда докосваем."""
    src = open(JS, encoding='utf-8').read()
    if 'INTL-ROW' in src:
        print('панелът вече е поправен')
        return

    old = """        var rows = j.arrivals.map(function(r){
          return {
            t: r.t,
            ts: (r.ts || 0) * 1000,
            cat: '',
            line: r.operator || 'FlixBus',
            from: r.from + (r.transfers ? ' · ' + r.transfers + '×' : ''),
            plat: r.station === 'Sihlquai' ? '' : (r.station || ''),
            delay: 0,
            st: r.station || 'Sihlquai'
          };
        });"""

    new = """        // INTL-ROW — „→ Zurich" не носеше нищо; важното е коя автогара.
        // `st` служи и за завеждане на картата: PLACES знае Sihlquai.
        var rows = j.arrivals.map(function(r){
          var stop = r.station && r.station !== 'Zurich'
                   ? r.station : 'Sihlquai';
          return {
            t: r.t,
            ts: (r.ts || 0) * 1000,
            cat: '',
            line: r.operator || 'FlixBus',
            from: r.from + (r.transfers ? ' · ' + r.transfers + '×' : ''),
            plat: '',
            delay: 0,
            st: stop
          };
        });"""

    if old not in src:
        print('ГРЕШКА: не намирам подготовката на редовете')
        sys.exit(1)

    src = src.replace(old, new)
    open(JS, 'w', encoding='utf-8').write(src)
    print('панелът: показва автогарата, редът завежда картата')


if __name__ == '__main__':
    patch_scraper()
    patch_panel()
