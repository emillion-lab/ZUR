#!/usr/bin/env python3
"""Пристигащи международни автобуси в Цюрих (FlixBus и партньори).

Защо не през швейцарския API: FlixBus не подава разписания към SBB,
затова transport.opendata.ch не ги знае. Собственият им интерфейс пък
няма табло за спирка — има само търсене между два града. Затова се пита
наобратно: от двайсетина големи изходни града КЪМ Цюрих, и се събират
часовете на пристигане.

Двайсет заявки на пускане, четири пъти дневно — поносимо натоварване.

Изход: data/flixbus.json
  {"generated":"...", "arrivals":[{t,ts,from,line,station,dur,operator}]}

Интерфейсът им е неофициален и се променя без предупреждение, затова
всяка стъпка се отпечатва в лога — при счупване се вижда къде точно.
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

# Градовете, от които реално идват хора в Цюрих с автобус.
# Подредени по значимост — ако лимитът удари, горните са свършили работа.
ORIGINS = [
    'Milan', 'Munich', 'Stuttgart', 'Frankfurt', 'Paris', 'Lyon',
    'Vienna', 'Prague', 'Berlin', 'Belgrade', 'Zagreb', 'Ljubljana',
    'Budapest', 'Amsterdam', 'Brussels', 'Barcelona', 'Venice',
    'Florence', 'Turin', 'Sarajevo', 'Skopje', 'Sofia',
]

DEST = 'Zurich'


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
    """Превръща име на град в идентификатор на FlixBus."""
    url = (BASE + '/search/autocomplete/cities?q=' + urllib.parse.quote(name)
           + '&lang=en&country=')
    d = get(url)
    if not d:
        return None
    rows = d if isinstance(d, list) else (d.get('cities') or d.get('results') or [])
    for r in rows:
        nm = (r.get('name') or '').lower()
        if name.lower() in nm:
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
           + '&currency=EUR&locale=en&search_by=cities&include_after_midnight_rides=1')
    return get(url)


def parse(d, origin_name):
    """Вади часовете на пристигане в Цюрих от отговора на търсенето."""
    out = []
    if not d:
        return out
    trips = d.get('trips') or []
    for tr in trips:
        results = tr.get('results') or {}
        items = results.values() if isinstance(results, dict) else results
        for it in items:
            arr = it.get('arrival') or {}
            when = arr.get('date') or ''
            if not when:
                continue
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
                'station': (arr.get('station_name')
                            or arr.get('city_name') or 'Sihlquai'),
                'dur': it.get('duration', {}).get('hours', 0),
                'operator': operator or 'FlixBus',
                'transfers': it.get('transfers', 0),
            })
    return out


def main():
    print('търся идентификатора на Цюрих…')
    dest_id = find_city(DEST)
    print('  Цюрих =', dest_id)
    if not dest_id:
        print('НЕ МОГА ДА НАМЕРЯ ЦЮРИХ — интерфейсът вероятно се е сменил')
        sys.exit(1)

    # ONE-DAY — заявката за утре връща 400 при това съчетание от
    # параметри; днешният ден дава шейсетина курса и стига за смяната.
    today = datetime.date.today()
    days = [today]

    arrivals = []
    for name in ORIGINS:
        cid = find_city(name)
        if not cid:
            print(name, '— няма такъв град')
            continue
        got = 0
        for day in days:
            rows = parse(search(cid, dest_id, day), name)
            arrivals += rows
            got += len(rows)
            time.sleep(0.8)
        print('%-12s %s → %d курса' % (name, cid, got))
        time.sleep(0.5)

    # един и същ курс идва през няколко търсения
    seen, keep = set(), []
    for r in sorted(arrivals, key=lambda x: x['ts']):
        sig = (r['ts'], r['from'])
        if sig in seen:
            continue
        seen.add(sig)
        keep.append(r)

    # само отсега нататък плюс малко назад — миналото не носи клиенти
    now = time.time()
    keep = [r for r in keep if r['ts'] > now - 3600][:60]

    print('общо пристигащи:', len(keep))
    if keep[:3]:
        for r in keep[:3]:
            print('  ', r['t'], r['from'], '→', r['station'], r['operator'])

    if not keep:
        print('НИЩО НЕ СЕ ИЗТЕГЛИ — не презаписвам стария файл')
        sys.exit(1)

    out = {
        'generated': datetime.datetime.now(datetime.timezone.utc)
                     .isoformat(timespec='minutes'),
        'source': 'flixbus',
        'arrivals': keep,
    }
    os.makedirs('data', exist_ok=True)
    with open('data/flixbus.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('записан data/flixbus.json:', os.path.getsize('data/flixbus.json'), 'байта')


if __name__ == '__main__':
    main()
