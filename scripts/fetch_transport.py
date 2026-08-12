#!/usr/bin/env python3
"""Тегли ПРИСТИГАЩИТЕ в Цюрих и ги разделя по вид транспорт.

Защо пристигащи, а не заминаващи: човек, който се качва на трамвая,
вече е решил как ще пътува. Клиент за такси е този, който току-що е
слязъл — на гарата, на летището, на трамвайния възел късно вечер.
Първата версия теглеше заминавания и затова списъкът приличаше на
разписание, а не на поток от хора.

Швейцарският отворен API (transport.opendata.ch) връща всички видове
превоз от един endpoint, с поле `category`, затова едно теглене
покрива влак, трамвай, автобус и международните линии.

Изход: data/transport.json
  { "generated": "...", "train": [...], "tram": [...], "bus": [...], "intl": [...] }
Всеки запис: {t:"HH:MM", cat:"S", line:"3", from:"Wetzikon", plat:"7", delay:2, st:"hb"}
"""
import json
import os
import sys
import time
import datetime
import urllib.parse
import urllib.request

API = 'https://transport.opendata.ch/v1/stationboard'

# Местата, където слезлият пътник става възможен клиент.
# Градските спирки са подбрани като възли, а не като случайни спирки.
STATIONS = [
    # ── гари и летище ──
    ('Zürich HB',                  'hb',          'rail'),
    ('Zürich Oerlikon',            'oerlikon',    'rail'),
    ('Zürich Stadelhofen',         'stadelhofen', 'rail'),
    ('Zürich Flughafen',           'airport',     'rail'),
    # ── трамвайни и автобусни възли ──
    ('Zürich, Bahnhofquai/HB',     'quai',        'city'),
    ('Zürich, Central',            'central',     'city'),
    ('Zürich, Bellevue',           'bellevue',    'city'),
    ('Zürich, Paradeplatz',        'parade',      'city'),
    ('Zürich, Stauffacher',        'stauffacher', 'city'),
    ('Zürich, Bahnhof Enge',       'enge',        'city'),
    # ── международни автобуси ──
    ('Zürich, Carparkplatz Sihlquai', 'sihlquai', 'intl'),
]

TRAIN = {'S', 'SN', 'IC', 'ICE', 'IR', 'RE', 'R', 'EC', 'TGV', 'RJX', 'NJ', 'PE'}
TRAM  = {'T', 'TRAM', 'NFT'}
BUS   = {'B', 'BUS', 'NFB', 'TRO', 'NFO', 'KB'}


def fetch(station, limit=20):
    # type=arrival е същината: таблото на пристигащите, не на заминаващите
    q = urllib.parse.urlencode({'station': station, 'limit': limit,
                                'type': 'arrival'})
    req = urllib.request.Request(API + '?' + q,
                                 headers={'User-Agent': 'zur-taxi-radar'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r).get('stationboard') or []
        except Exception as ex:
            if attempt == 2:
                print('  пропуснато:', station, '—', ex)
                return []
            time.sleep(2 + attempt * 3)
    return []


def origin(entry):
    """Откъде идва. При таблото на пристигащите API-то пълни различни
    полета според превозвача, затова се пробват няколко."""
    for key in ('from', 'to'):
        v = (entry.get(key) or '').strip()
        if v:
            return v
    prev = entry.get('passList') or []
    if prev:
        st = (prev[0].get('station') or {}).get('name') or ''
        return st.strip()
    return ''


def norm(entry, station_key):
    stop = entry.get('stop') or {}
    # при type=arrival времето е в arrival; departure остава празно
    when = stop.get('arrival') or stop.get('departure') or ''
    ts = stop.get('arrivalTimestamp') or stop.get('departureTimestamp') or 0
    if not when:
        return None

    prog = (stop.get('prognosis') or {})
    pw = prog.get('arrival') or prog.get('departure')
    delay = 0
    if pw and pw != when:
        try:
            a = datetime.datetime.fromisoformat(when)
            b = datetime.datetime.fromisoformat(pw)
            delay = int((b - a).total_seconds() // 60)
        except ValueError:
            delay = 0

    return {
        't': when[11:16],
        'ts': ts,
        'line': (entry.get('number') or entry.get('name') or '').strip(),
        'cat': (entry.get('category') or '').strip(),
        'from': origin(entry),
        'plat': (stop.get('platform') or '').strip(),
        'delay': delay,
        'st': station_key,
    }


def bucket(cat):
    c = (cat or '').upper()
    if c in TRAIN:
        return 'train'
    if c in TRAM:
        return 'tram'
    if c in BUS:
        return 'bus'
    return None


def main():
    out = {'train': [], 'tram': [], 'bus': [], 'intl': []}

    for name, key, role in STATIONS:
        print('тегля пристигащи:', name)
        for e in fetch(name):
            n = norm(e, key)
            if not n:
                continue
            b = bucket(n['cat'])
            if not b:
                continue
            if role == 'intl' and b == 'bus':
                out['intl'].append(n)
            else:
                out[b].append(n)
        time.sleep(1.2)

    # една и съща линия се повтаря на всеки няколко минути;
    # държим по три, за да личи ритъмът без да задръсти списъка
    seen = {}
    for k in ('train', 'tram', 'bus', 'intl'):
        keep = []
        for r in sorted(out[k], key=lambda r: r['ts']):
            sig = (r['st'], r['cat'], r['line'], r['from'])
            seen[sig] = seen.get(sig, 0) + 1
            if seen[sig] <= 3:
                keep.append(r)
        out[k] = keep[:40]

    total = sum(len(v) for v in out.values())
    print('общо пристигащи:', total,
          '· влак', len(out['train']),
          '· трамвай', len(out['tram']),
          '· автобус', len(out['bus']),
          '· международни', len(out['intl']))

    if total == 0:
        print('НИЩО НЕ СЕ ИЗТЕГЛИ — не презаписвам стария файл')
        sys.exit(1)

    out['generated'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='minutes')
    out['source'] = 'transport.opendata.ch'
    out['kind'] = 'arrivals'

    os.makedirs('data', exist_ok=True)
    with open('data/transport.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('записан data/transport.json:', os.path.getsize('data/transport.json'), 'байта')


if __name__ == '__main__':
    main()
