#!/usr/bin/env python3
"""Тегли разписанията на Цюрих и ги разделя по вид транспорт.

Швейцарският отворен API (transport.opendata.ch) връща всички видове
превоз от един endpoint, с поле `category`. Затова не са нужни отделни
скрейпъри като БДЖ/ЦАС в София — едно теглене покрива влак, трамвай,
автобус и международните линии, а разделянето е по категория.

Изход: data/transport.json
  { "generated": "...", "train": [...], "tram": [...], "bus": [...], "intl": [...] }

Всеки запис: {t: "HH:MM", line: "S3", to: "Aarau", plat: "7", delay: 3}
"""
import json
import os
import sys
import time
import datetime
import urllib.parse
import urllib.request

API = 'https://transport.opendata.ch/v1/stationboard'

# Спирките, които обслужват таксиметровите зони.
# Първият опит ползваше само Bahnhofquai за градския транспорт и оттам
# идваше единствено автобус 46 — затова тук са добавени същинските
# трамвайни и автобусни възли на града.
STATIONS = [
    # ── влакове ──
    ('Zürich HB',                  'hb',          'rail'),
    ('Zürich Oerlikon',            'oerlikon',    'rail'),
    ('Zürich Stadelhofen',         'stadelhofen', 'rail'),
    ('Zürich Flughafen',           'airport',     'rail'),
    # ── трамваи и градски автобуси ──
    ('Zürich, Bahnhofquai/HB',     'quai',        'city'),
    ('Zürich, Central',            'central',     'city'),
    ('Zürich, Bellevue',           'bellevue',    'city'),
    ('Zürich, Paradeplatz',        'parade',      'city'),
    ('Zürich, Stauffacher',        'stauffacher', 'city'),
    ('Zürich, Bahnhof Enge',       'enge',        'city'),
    # ── международни автобуси (FlixBus и др.) ──
    ('Zürich, Carparkplatz Sihlquai', 'sihlquai', 'intl'),
]

# Категориите, както ги връща API-то. Списъкът е нарочно широк —
# швейцарските превозвачи ги пишат ту с главни, ту с малки букви.
TRAIN = {'S', 'SN', 'IC', 'ICE', 'IR', 'RE', 'R', 'EC', 'TGV', 'RJX', 'NJ', 'PE'}
TRAM  = {'T', 'TRAM', 'NFT'}
BUS   = {'B', 'BUS', 'NFB', 'TRO', 'NFO', 'KB'}


def fetch(station, limit=20):
    q = urllib.parse.urlencode({'station': station, 'limit': limit})
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
            time.sleep(2 + attempt * 3)   # API-то е с лимит; чакаме и пробваме пак
    return []


def norm(entry, station_key):
    stop = entry.get('stop') or {}
    dep = stop.get('departure') or ''
    if not dep:
        return None
    prog = (stop.get('prognosis') or {}).get('departure')
    delay = 0
    if prog and prog != dep:
        try:
            a = datetime.datetime.fromisoformat(dep)
            b = datetime.datetime.fromisoformat(prog)
            delay = int((b - a).total_seconds() // 60)
        except ValueError:
            delay = 0
    return {
        't': dep[11:16],
        'ts': stop.get('departureTimestamp') or 0,
        'line': (entry.get('number') or entry.get('name') or '').strip(),
        'cat': (entry.get('category') or '').strip(),
        'to': (entry.get('to') or '').strip(),
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
        print('тегля', name)
        rows = fetch(name)
        for e in rows:
            n = norm(e, key)
            if not n:
                continue
            b = bucket(n['cat'])
            if not b:
                continue
            # Спирката на международните линии е отделен кош, за да не се
            # смесва с градските автобуси.
            if role == 'intl' and b == 'bus':
                out['intl'].append(n)
            else:
                out[b].append(n)
        time.sleep(1.2)                     # възпитано темпо към чуждия API

    # една и съща линия от една спирка към една посока се повтаря
    # на всеки няколко минути; държим по три такива, за да не задръсти
    seen = {}
    for k in ('train', 'tram', 'bus', 'intl'):
        keep = []
        for r in sorted(out[k], key=lambda r: r['ts']):
            sig = (r['st'], r['cat'], r['line'], r['to'])
            seen[sig] = seen.get(sig, 0) + 1
            if seen[sig] <= 3:
                keep.append(r)
        out[k] = keep[:40]

    total = sum(len(v) for v in out.values())
    print('общо записи:', total,
          '· влак', len(out['train']),
          '· трамвай', len(out['tram']),
          '· автобус', len(out['bus']),
          '· международни', len(out['intl']))

    if total == 0:
        print('НИЩО НЕ СЕ ИЗТЕГЛИ — не презаписвам стария файл')
        sys.exit(1)

    out['generated'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='minutes')
    out['source'] = 'transport.opendata.ch'

    os.makedirs('data', exist_ok=True)
    with open('data/transport.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('записан data/transport.json:', os.path.getsize('data/transport.json'), 'байта')


if __name__ == '__main__':
    main()
