#!/usr/bin/env python3
"""Пристигащи международни автобуси в Цюрих (FlixBus и партньори).

Защо не през швейцарския API: FlixBus не подава разписания към SBB.
Собственият им интерфейс няма табло за спирка, само търсене между
градове — затова се пита наобратно: от двайсетина изходни града КЪМ
Цюрих, и се събират часовете на пристигане.

ВАЖНО за таксито: FlixBus спира на две места в Цюрих —
  · Sihlquai (Ausstellungsstrasse), до централната гара
  · перон R на летището, където няма таксиметрова стоянка
Второто е по-ценно: слезлият там няма друг вариант освен такси.

Досега всички записи излизаха „Sihlquai", защото това беше стойността
по подразбиране, а истинското име на спирката не се извличаше. Затова
скриптът отпечатва веднъж суровия запис — да се видят имената на
полетата, вместо да се гадаят.
"""
import json
import os
import sys
import time
import datetime
import urllib.parse
import urllib.request

BASE = 'https://global.api.flixbus.com'
UA = ('Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120 Mobile Safari/537.36')

ORIGINS = [
    'Milan', 'Munich', 'Stuttgart', 'Frankfurt', 'Paris', 'Lyon',
    'Vienna', 'Prague', 'Berlin', 'Belgrade', 'Zagreb', 'Ljubljana',
    'Budapest', 'Amsterdam', 'Brussels', 'Barcelona', 'Venice',
    'Florence', 'Turin', 'Sarajevo', 'Skopje', 'Sofia',
]

DEST = 'Zurich'

# Разпознаване на спирката по това, което върне интерфейсът.
STOPS = [
    ('flughafen', 'Airport'),
    ('airport',   'Airport'),
    ('kloten',    'Airport'),
    ('sihlquai',  'Sihlquai'),
    ('ausstellung', 'Sihlquai'),
    ('carparkplatz', 'Sihlquai'),
]

_dumped = [0]


def get(url, tries=3):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'en',
        'Origin': 'https://shop.flixbus.com',
        'Referer': 'https://shop.flixbus.com/',
    })
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except Exception as ex:
            if i == tries - 1:
                print('    неуспех:', type(ex).__name__, str(ex)[:120])
                return None
            time.sleep(2 + i * 3)
    return None


def find_city(name):
    url = (BASE + '/search/autocomplete/cities?q=' + urllib.parse.quote(name)
           + '&lang=en&country=')
    d = get(url)
    if not d:
        return None
    rows = d if isinstance(d, list) else (d.get('cities') or d.get('results') or [])
    for r in rows:
        if name.lower() in (r.get('name') or '').lower():
            return r.get('id') or r.get('uuid')
    if rows:
        return rows[0].get('id') or rows[0].get('uuid')
    return None


def search(from_id, to_id, day):
    url = (BASE + '/search/service/v4/search'
           + '?from_city_id=' + urllib.parse.quote(str(from_id))
           + '&to_city_id=' + urllib.parse.quote(str(to_id))
           + '&departure_date=' + day.strftime('%d.%m.%Y')
           + '&products=' + urllib.parse.quote('{"adult":1}')
           + '&currency=EUR&locale=en&search_by=cities'
           + '&include_after_midnight_rides=1')
    return get(url)


def dump_shape(it):
    """Веднъж на пускане показва как изглежда записът."""
    if _dumped[0]:
        return
    _dumped[0] = 1
    try:
        print('  --- суров запис ---')
        print('  ключове:', sorted(it.keys()))
        print('  arrival:', json.dumps(it.get('arrival'), ensure_ascii=False)[:400])
        legs = it.get('legs') or []
        if legs:
            print('  leg[-1] ключове:', sorted(legs[-1].keys()))
            arr = legs[-1].get('arrival') or legs[-1].get('to') or {}
            print('  leg[-1].arrival:', json.dumps(arr, ensure_ascii=False)[:300])
        print('  -------------------')
    except Exception as ex:
        print('  (не мога да покажа записа:', type(ex).__name__, ')')


def station_of(it):
    """Търси името на спирката навсякъде, където може да е скрито."""
    cands = []
    arr = it.get('arrival') or {}
    if isinstance(arr, dict):
        for k in ('station_name', 'stationName', 'name', 'city_name', 'cityName'):
            v = arr.get(k)
            if v:
                cands.append(str(v))
        st = arr.get('station')
        if isinstance(st, dict):
            cands.append(str(st.get('name') or ''))
        elif st:
            cands.append(str(st))
    for leg in reversed(it.get('legs') or []):
        for key in ('arrival', 'to', 'destination'):
            v = leg.get(key)
            if isinstance(v, dict):
                cands.append(str(v.get('name') or v.get('station_name') or ''))
            elif isinstance(v, str):
                cands.append(v)

    blob = ' '.join(c for c in cands if c).lower()
    for key, label in STOPS:
        if key in blob:
            return label
    for c in cands:
        if c and len(c) > 2:
            return c[:30]
    return 'Sihlquai'


def parse(d, origin_name):
    out = []
    if not d:
        return out
    for tr in (d.get('trips') or []):
        results = tr.get('results') or {}
        items = results.values() if isinstance(results, dict) else results
        for it in items:
            arr = it.get('arrival') or {}
            when = arr.get('date') or ''
            if not when:
                continue
            dump_shape(it)
            legs = it.get('legs') or []
            operator = ''
            if legs:
                operator = (legs[-1].get('operator_name')
                            or legs[-1].get('operator') or '')
            out.append({
                't': when[11:16],
                'ts': int(datetime.datetime.fromisoformat(
                          when.replace('Z', '+00:00')).timestamp()),
                'from': origin_name,
                'line': (it.get('uid') or '')[:8],
                'station': station_of(it),
                'dur': (it.get('duration') or {}).get('hours', 0),
                'operator': operator or 'FlixBus',
                'transfers': it.get('transfers', 0),
            })
    return out


def main():
    print('търся идентификатора на Цюрих…')
    dest_id = find_city(DEST)
    print('  Цюрих =', dest_id)
    if not dest_id:
        print('НЕ МОГА ДА НАМЕРЯ ЦЮРИХ')
        sys.exit(1)

    today = datetime.date.today()
    arrivals = []
    for name in ORIGINS:
        cid = find_city(name)
        if not cid:
            print(name, '— няма такъв град')
            continue
        rows = parse(search(cid, dest_id, today), name)
        arrivals += rows
        print('%-12s → %d курса' % (name, len(rows)))
        time.sleep(1.0)

    seen, keep = set(), []
    for r in sorted(arrivals, key=lambda x: x['ts']):
        sig = (r['ts'], r['from'], r['station'])
        if sig in seen:
            continue
        seen.add(sig)
        keep.append(r)

    now = time.time()
    keep = [r for r in keep if r['ts'] > now - 3600][:70]

    # колко идват на коя спирка — това е същината на проверката
    counts = {}
    for r in keep:
        counts[r['station']] = counts.get(r['station'], 0) + 1
    print('общо пристигащи:', len(keep))
    for st, n in sorted(counts.items(), key=lambda x: -x[1]):
        print('   %-22s %d' % (st, n))
    for r in keep[:4]:
        print('  ', r['t'], r['from'], '→', r['station'])

    if not keep:
        print('НИЩО НЕ СЕ ИЗТЕГЛИ — не презаписвам стария файл')
        sys.exit(1)

    os.makedirs('data', exist_ok=True)
    with open('data/flixbus.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated': datetime.datetime.now(datetime.timezone.utc)
                         .isoformat(timespec='minutes'),
            'source': 'flixbus',
            'arrivals': keep,
        }, f, ensure_ascii=False, separators=(',', ':'))
    print('записан data/flixbus.json:', os.path.getsize('data/flixbus.json'), 'байта')


if __name__ == '__main__':
    main()
