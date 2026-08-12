#!/usr/bin/env python3
"""Допълва демо разписанието с късните вечерни кацания на ZRH.

Кешът покриваше 04:00–21:10 UTC (06:00–23:10 местно), затова часовете
след 23:00 стояха празни на времевата скала. Летище Цюрих има нощна
забрана за полети между 23:30 и 06:00, така че истински нощни кацания
почти няма — но интервалът 21:10–23:20 UTC съществува и липсваше.

Добавят се само реални редовни линии, кацащи в този прозорец.
Idempotent: ако LX317 вече е вътре, нищо не се прави.
"""
import json
import sys

PATH = 'flight-cache.json'
DAY = '2026-07-09'          # датата, с която е записан целият демо кеш

LATE = [
    ('LX317',  'Barcelona',   '21:35'),
    ('LX1073', 'Palma',       '21:50'),
    ('LX345',  'Nice',        '22:05'),
    ('LX1215', 'Amsterdam',   '22:20'),
    ('LX617',  'Lisbon',      '22:35'),
    ('LX1345', 'Vienna',      '22:50'),
    ('LX257',  'Athens',      '23:05'),
    ('LX1927', 'Porto',       '23:20'),
]


def main():
    with open(PATH, encoding='utf-8') as f:
        d = json.load(f)

    rows = d.get('data') or []
    have = {r.get('flight', {}).get('iata') for r in rows}

    if 'LX317' in have:
        print('късните полети вече са добавени')
        return

    for iata, origin, hhmm in LATE:
        rows.append({
            'flight': {'iata': iata},
            'departure': {'airport': origin},
            'arrival': {'scheduled': DAY + 'T' + hhmm + ':00+00:00'},
        })

    rows.sort(key=lambda r: r['arrival']['scheduled'])
    d['data'] = rows

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)

    hours = sorted({r['arrival']['scheduled'][11:13] for r in rows})
    print('полети:', len(rows), '· покрити часа (UTC):', ' '.join(hours))


if __name__ == '__main__':
    main()
