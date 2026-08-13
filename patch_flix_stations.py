#!/usr/bin/env python3
"""Разрешава station_id към име на спирка.

Суровият запис показа истината: `arrival` носи само `station_id`, без
име. Затова всичко падаше на подразбиращата стойност „Sihlquai" и не се
виждаше дали някой автобус идва на летището.

Тук се тегли списъкът със спирки за Цюрих и се прави съответствие
идентификатор → име. Освен това се отпечатват всички различни
идентификатори, които са се появили — ако някой остане неразпознат,
ще личи в лога вместо да се скрие зад догадка.
"""
import sys

PATH = 'scripts/fetch_flixbus.py'
MARK = 'STATION-MAP'


def main():
    src = open(PATH, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    # ── таблицата с имената на спирките ──
    helper = '''
# STATION-MAP — `arrival` дава само station_id; имената идват оттук.
STATIONS = {}


def load_stations(city_name):
    """Тегли спирките на града и връща съответствие id → име."""
    for path in ('/search/autocomplete/stations',
                 '/search/autocomplete/cities'):
        url = (BASE + path + '?q=' + urllib.parse.quote(city_name)
               + '&lang=en&country=')
        d = get(url)
        if not d:
            continue
        rows = d if isinstance(d, list) else (
            d.get('stations') or d.get('cities') or d.get('results') or [])
        got = 0
        for r in rows:
            sid = r.get('id') or r.get('uuid')
            nm = r.get('name') or ''
            if sid and nm:
                STATIONS[str(sid)] = str(nm)
                got += 1
            # някои отговори носят спирките вложени в града
            for s in (r.get('stations') or []):
                sid2 = s.get('id') or s.get('uuid')
                nm2 = s.get('name') or ''
                if sid2 and nm2:
                    STATIONS[str(sid2)] = str(nm2)
                    got += 1
        print('  %s → %d записа' % (path.rsplit('/', 1)[-1], got))
    return STATIONS

'''
    anchor = 'def get(url, tries=3):'
    if anchor not in src:
        print('ГРЕШКА: не намирам get()')
        sys.exit(1)
    # помощникът ползва get(), затова се слага след него
    end_of_get = src.find('def find_city(name):')
    src = src[:end_of_get] + helper + '\n' + src[end_of_get:]

    # ── station_of вече гледа и таблицата ──
    old = """def station_of(it):
    \"\"\"Търси името на спирката навсякъде, където може да е скрито.\"\"\"
    cands = []
    arr = it.get('arrival') or {}
    if isinstance(arr, dict):"""
    new = """SEEN_IDS = {}


def station_of(it):
    \"\"\"Търси името на спирката навсякъде, където може да е скрито.\"\"\"
    cands = []
    arr = it.get('arrival') or {}
    if isinstance(arr, dict):
        sid = str(arr.get('station_id') or '')
        if sid:
            SEEN_IDS[sid] = SEEN_IDS.get(sid, 0) + 1
            nm = STATIONS.get(sid)
            if nm:
                cands.append(nm)"""
    if old not in src:
        print('ГРЕШКА: не намирам station_of()')
        sys.exit(1)
    src = src.replace(old, new)

    # ── зареждане на спирките в началото ──
    src = src.replace(
        "    print('  Цюрих =', dest_id)",
        "    print('  Цюрих =', dest_id)\n"
        "    print('тегля спирките на Цюрих…')\n"
        "    load_stations(DEST)\n"
        "    print('  известни спирки:', len(STATIONS))")

    # ── в края: кои идентификатори са се появили ──
    src = src.replace(
        "    for r in keep[:4]:\n        print('  ', r['t'], r['from'], '→', r['station'])",
        "    print('различни station_id в отговорите:')\n"
        "    for sid, n in sorted(SEEN_IDS.items(), key=lambda x: -x[1]):\n"
        "        print('   %s  %-28s %d' % (sid[:8], STATIONS.get(sid, '(непознат)'), n))\n"
        "    for r in keep[:4]:\n"
        "        print('  ', r['t'], r['from'], '→', r['station'])")

    open(PATH, 'w', encoding='utf-8').write(src)
    print('добавена таблица с имената на спирките')


if __name__ == '__main__':
    main()
