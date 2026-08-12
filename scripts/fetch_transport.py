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

# Спирките, които обслужват таксиметровите зони. Взимаме заминаванията:
# човек, който току-що е слязъл, идва от някъде — но за такси е по-важно
# кога тръгва последното превозно средство, защото след него хората
# остават на улицата.
STATIONS = [
    ('Zürich HB',             'hb'),
    ('Zürich Oerlikon',       'oerlikon'),
    ('Zürich Stadelhofen',    'stadelhofen'),
    ('Zürich Flughafen',      'airport'),
    ('Zürich, Bahnhofquai/HB', 'quai'),     # трамваи и автобуси пред гарата
    ('Zürich, Sihlquai',      'sihlquai'),  # международните автобуси
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

    for name, key in STATIONS:
        print('тегля', name)
        rows = fetch(name)
        for e in rows:
            n = norm(e, key)
            if not n:
                continue
            b = bucket(n['cat'])
            if not b:
                continue
            # Sihlquai е спирката на международните линии — отделен кош,
            # за да не се смесват с градските автобуси.
            if key == 'sihlquai' and b == 'bus':
                out['intl'].append(n)
            else:
                out[b].append(n)
        time.sleep(1.2)                     # възпитано темпо към чуждия API

    for k in out:
        out[k].sort(key=lambda r: r['ts'])
        out[k] = out[k][:40]

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
