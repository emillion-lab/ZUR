#!/usr/bin/env python3
"""Допълва демо разписанието с късните вечерни кацания на ZRH.

Кешът покриваше 04:00–21:10 UTC (06:00–23:10 местно), затова часовете
след 23:00 стояха празни на времевата скала. Летище Цюрих има нощна
забрана за полети между 23:30 и 06:00, така че истински нощни кацания
почти няма — но интервалът 21:10–23:20 UTC съществува и липсваше.

Проверката за вече свършена работа е по ЧАС, не по номер на полет:
първата версия гледаше за LX317, който обаче вече беше в кеша като
дневен полет, и патчът тихо не правеше нищо.
"""
import json

PATH = 'flight-cache.json'
DAY = '2026-07-09'          # датата, с която е записан целият демо кеш

LATE = [
    ('LX2317', 'Barcelona',   '21:35'),
    ('LX2073', 'Palma',       '21:50'),
    ('LX2345', 'Nice',        '22:05'),
    ('LX2215', 'Amsterdam',   '22:20'),
    ('LX2617', 'Lisbon',      '22:35'),
    ('LX2145', 'Vienna',      '22:50'),
    ('LX2257', 'Athens',      '23:05'),
    ('LX2927', 'Porto',       '23:20'),
]


def main():
    with open(PATH, encoding='utf-8') as f:
        d = json.load(f)

    rows = d.get('data') or []
    hours = {r['arrival']['scheduled'][11:13] for r in rows}

    # има ли изобщо нещо след 21:30? това е истинският признак
    if '22' in hours or '23' in hours:
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

    hrs = sorted({r['arrival']['scheduled'][11:13] for r in rows})
    print('полети:', len(rows), '· покрити часа (UTC):', ' '.join(hrs))


if __name__ == '__main__':
    main()
