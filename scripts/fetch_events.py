#!/usr/bin/env python3
"""Събития в Цюрих през Eventfrog.

Два опита преди този се провалиха и от тях излезе поука: страниците на
залите се строят от JavaScript, затова нито регулярни изрази по HTML,
нито JSON-LD хващат нещо — сървърът връща празен скелет.

Eventfrog е най-големият швейцарски календар (над 20 000 събития) и има
документиран отворен интерфейс за трети страни. Ключът се взима
безплатно и се слага като repo secret EVENTFROG_KEY.

За таксито значение има краят на събитието: хиляда души излизат наведнъж
и половината търсят превоз. Затова се пази начало плюс очаквана
продължителност според мястото.

Изход: data/events.json
"""
import json
import os
import sys
import time
import datetime
import urllib.parse
import urllib.request

API = 'https://api.eventfrog.net/api/v1/events.json'
KEY = os.environ.get('EVENTFROG_KEY', '').strip()

# Цюрих и близките предградия, откъдето хората се прибират с такси
BBOX = {'latMin': 47.30, 'latMax': 47.46, 'lngMin': 8.42, 'lngMax': 8.63}

# Големите зали: колко души излизат наведнъж и колко трае събитието.
# Разпознават се по името на мястото, което Eventfrog връща.
KNOWN = [
    ('hallenstadion',  13000, 165),
    ('letzigrund',     26000, 150),
    ('opernhaus',       1100, 180),
    ('schauspielhaus',   750, 150),
    ('kaufleuten',      1500, 300),
    ('x-tra',           1500, 300),
    ('volkshaus',       1400, 180),
    ('tonhalle',        1400, 150),
    ('kongresshaus',    1900, 165),
    ('theater 11',      1500, 165),
    ('samsung hall',    1900, 180),
    ('komplex 457',     1200, 300),
    ('mascotte',         500, 300),
    ('plaza',            600, 300),
    ('moods',            300, 180),
]
DEFAULT_SIZE, DEFAULT_DUR = 300, 150


def profile(venue, name):
    blob = ((venue or '') + ' ' + (name or '')).lower()
    for key, size, dur in KNOWN:
        if key in blob:
            return size, dur
    return DEFAULT_SIZE, DEFAULT_DUR


def get(url, tries=3):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'zur-taxi-radar',
        'Accept': 'application/json',
    })
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as ex:
            body = ''
            if hasattr(ex, 'read'):
                try:
                    body = ex.read()[:200].decode('utf-8', 'replace')
                except Exception:
                    pass
            if i == tries - 1:
                print('    неуспех:', type(ex).__name__, str(ex)[:100], body)
                return None
            time.sleep(2 + i * 3)
    return None


def main():
    if not KEY:
        print('НЯМА КЛЮЧ. Вземи безплатен от eventfrog.ch и го сложи като')
        print('repo secret EVENTFROG_KEY (Settings → Secrets → Actions).')
        print('Документация: https://docs.api.eventfrog.net/')
        sys.exit(1)

    today = datetime.date.today()
    until = today + datetime.timedelta(days=21)

    out, page = [], 0
    while page < 8:
        q = {
            'apiKey': KEY,
            'perPage': 100,
            'page': page,
            'fromDate': today.isoformat(),
            'toDate': until.isoformat(),
        }
        q.update(BBOX)
        print('страница', page)
        d = get(API + '?' + urllib.parse.urlencode(q))
        if not d:
            break
        rows = d.get('datasets') or d.get('events') or d.get('data') or []
        if not rows:
            print('   → празна')
            break
        print('   →', len(rows), 'записа')

        for e in rows:
            start = (e.get('start') or e.get('startDate')
                     or e.get('dateFrom') or '')
            if not start:
                continue
            try:
                dt = datetime.datetime.fromisoformat(
                    str(start).replace('Z', '+00:00'))
            except ValueError:
                continue
            day = dt.date()
            if not (today <= day <= until):
                continue

            name = str(e.get('name') or e.get('title') or '').strip()
            if len(name) < 2:
                continue

            loc = e.get('location') or {}
            if not isinstance(loc, dict):
                loc = {}
            venue = str(loc.get('name') or e.get('locationName') or '').strip()

            lat = loc.get('lat') or loc.get('latitude') or e.get('lat')
            lng = loc.get('lng') or loc.get('longitude') or e.get('lng')
            try:
                lat, lng = float(lat), float(lng)
            except (TypeError, ValueError):
                lat, lng = 47.3769, 8.5417       # център, ако липсват

            size, dur = profile(venue, name)
            end = (dt + datetime.timedelta(minutes=dur)).strftime('%H:%M')

            out.append({
                'd': day.isoformat(),
                't': dt.strftime('%H:%M'),
                'end': end,
                'name': name[:90],
                'venue': (venue or 'Zürich')[:40],
                'lat': round(lat, 5), 'lng': round(lng, 5),
                'size': size,
                'url': str(e.get('url') or '')[:200],
            })

        if len(rows) < 100:
            break
        page += 1
        time.sleep(1.0)

    seen, keep = set(), []
    for e in sorted(out, key=lambda x: (x['d'], x['t'])):
        sig = (e['d'], e['t'], e['venue'], e['name'][:30])
        if sig in seen:
            continue
        seen.add(sig)
        keep.append(e)

    # най-полезни са големите: те правят опашката пред залата
    keep.sort(key=lambda x: (x['d'], x['t']))
    keep = keep[:200]

    print('общо събития:', len(keep))
    big = [e for e in keep if e['size'] >= 1000]
    print('от тях големи (1000+):', len(big))
    for e in big[:8]:
        print('  ', e['d'], e['t'], '→', e['end'], '·', e['venue'], '·', e['name'][:38])

    if not keep:
        print('НИЩО НЕ СЕ ИЗТЕГЛИ — не презаписвам стария файл')
        sys.exit(1)

    os.makedirs('data', exist_ok=True)
    with open('data/events.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated': datetime.datetime.now(datetime.timezone.utc)
                         .isoformat(timespec='minutes'),
            'source': 'eventfrog',
            'events': keep,
        }, f, ensure_ascii=False, separators=(',', ':'))
    print('записан data/events.json:', os.path.getsize('data/events.json'), 'байта')


if __name__ == '__main__':
    main()
