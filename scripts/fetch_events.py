#!/usr/bin/env python3
"""Събития в Цюрих през Eventfrog Public API v1.

Написано по официалната спецификация (publicapi-v1.json), а не по
догадки. Двата предишни опита — регулярни изрази по HTML и после
JSON-LD — върнаха нула, защото страниците на залите се строят от
JavaScript и сървърът дава празен скелет.

Какво дава спецификацията и защо е важно:
  · GET /public/v1/events с lat/lng/r — радиус в километри около Цюрих
  · полето `end` е истинско, не се налага да се гадае продължителност
  · `title` е обект с езици; вземаме de, после en, после каквото има
  · `locationIds` сочи към отделния списък с места, откъдето идват
    името и координатите на залата
  · страниците започват от 1, не от 0

За таксито значение има краят: хиляда души излизат наведнъж и
половината търсят превоз. Затова `end` се пази както е даден.

Ключ: repo secret EVENTFROG_KEY. Спецификацията предпочита Bearer,
затова се пробва първо той, а `apiKey` в адреса остава за резерва.

Изход: data/events.json
"""
import json
import os
import sys
import time
import datetime
import urllib.parse
import urllib.request

BASE = 'https://api.eventfrog.net/public/v1'
KEY = os.environ.get('EVENTFROG_KEY', '').strip()

# Цюрих и предградията, откъдето се прибират с такси
LAT, LNG, RADIUS = 47.3769, 8.5417, 15      # километри
DAYS_AHEAD = 21

# Големите зали: колко души излизат наведнъж. Продължителността вече
# идва от самото събитие, затова тук стои само размерът.
SIZES = [
    ('letzigrund',    26000),
    ('hallenstadion', 13000),
    ('kongresshaus',   1900),
    ('samsung hall',   1900),
    ('theater 11',     1500),
    ('kaufleuten',     1500),
    ('x-tra',          1500),
    ('volkshaus',      1400),
    ('tonhalle',       1400),
    ('komplex',        1200),
    ('opernhaus',      1100),
    ('schauspielhaus',  750),
    ('plaza',           600),
    ('mascotte',        500),
    ('moods',           300),
]
DEFAULT_SIZE = 250


def size_of(venue, title):
    blob = ((venue or '') + ' ' + (title or '')).lower()
    for key, n in SIZES:
        if key in blob:
            return n
    return DEFAULT_SIZE


def call(path, params):
    """Bearer по спецификация; при отказ пробва стария apiKey в адреса."""
    url = BASE + path + '?' + urllib.parse.urlencode(params, doseq=True)
    for use_bearer in (True, False):
        u = url if use_bearer else url + '&apiKey=' + urllib.parse.quote(KEY)
        headers = {'User-Agent': 'zur-taxi-radar', 'Accept': 'application/json'}
        if use_bearer:
            headers['Authorization'] = 'Bearer ' + KEY
        req = urllib.request.Request(u, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as ex:
            body = ''
            if hasattr(ex, 'read'):
                try:
                    body = ex.read()[:180].decode('utf-8', 'replace')
                except Exception:
                    pass
            if not use_bearer:
                print('    неуспех:', type(ex).__name__, str(ex)[:90], body)
                return None
            # Bearer не мина — мълчаливо пробваме резервния начин
    return None


def pick(multi):
    """title и подобните са обекти с езици."""
    if isinstance(multi, str):
        return multi
    if not isinstance(multi, dict):
        return ''
    for lang in ('de', 'en', 'fr', 'it'):
        v = multi.get(lang)
        if v:
            return str(v)
    for v in multi.values():
        if v:
            return str(v)
    return ''


def load_locations():
    """Имената и координатите на залите, наведнъж за целия радиус."""
    locs, page = {}, 1
    while page <= 10:
        d = call('/locations', {'lat': LAT, 'lng': LNG, 'r': RADIUS,
                                'page': page, 'perPage': 100})
        if not d:
            break
        rows = d.get('locations') or d.get('datasets') or []
        if not rows:
            break
        for l in rows:
            locs[str(l.get('id'))] = {
                'name': pick(l.get('title')) or l.get('city') or '',
                'lat': l.get('lat'), 'lng': l.get('lng'),
            }
        print('   места, страница %d → %d' % (page, len(rows)))
        if len(rows) < 100:
            break
        page += 1
        time.sleep(0.6)
    return locs


def main():
    if not KEY:
        print('НЯМА КЛЮЧ. Вземи безплатен от eventfrog.ch и го сложи като')
        print('repo secret EVENTFROG_KEY (Settings → Secrets → Actions).')
        sys.exit(1)

    today = datetime.date.today()
    until = today + datetime.timedelta(days=DAYS_AHEAD)

    print('тегля местата около Цюрих…')
    locs = load_locations()
    print('   общо места:', len(locs))

    print('тегля събитията…')
    raw, page = [], 1
    while page <= 12:
        d = call('/events', {
            'lat': LAT, 'lng': LNG, 'r': RADIUS,
            'from': today.isoformat(),
            'to': until.isoformat(),
            'page': page, 'perPage': 100,
            'country': 'CH',
        })
        if not d:
            break
        rows = d.get('events') or d.get('datasets') or []
        total = d.get('totalNumberOfResources')
        print('   страница %d → %d записа%s'
              % (page, len(rows), (' от %s' % total) if total else ''))
        if not rows:
            break
        raw += rows
        if len(rows) < 100:
            break
        page += 1
        time.sleep(0.8)

    out = []
    for e in raw:
        if e.get('cancelled') or e.get('visible') is False:
            continue
        begin = e.get('begin') or ''
        if not begin:
            continue
        try:
            dt = datetime.datetime.fromisoformat(str(begin).replace('Z', '+00:00'))
        except ValueError:
            continue
        day = dt.date()
        if not (today <= day <= until):
            continue

        title = pick(e.get('title'))
        if len(title) < 2:
            continue

        # мястото: първо по locationIds, после по locationAlias
        venue, lat, lng = '', None, None
        for lid in (e.get('locationIds') or []):
            l = locs.get(str(lid))
            if l:
                venue = l['name']
                lat, lng = l['lat'], l['lng']
                break
        if not venue:
            venue = pick(e.get('locationAlias'))
        try:
            lat, lng = float(lat), float(lng)
        except (TypeError, ValueError):
            lat, lng = LAT, LNG

        end_txt = ''
        endv = e.get('end')
        if endv:
            try:
                end_txt = datetime.datetime.fromisoformat(
                    str(endv).replace('Z', '+00:00')).strftime('%H:%M')
            except ValueError:
                end_txt = ''

        out.append({
            'd': day.isoformat(),
            't': dt.strftime('%H:%M'),
            'end': end_txt,
            'name': title[:90],
            'venue': (venue or 'Zürich')[:40],
            'lat': round(lat, 5), 'lng': round(lng, 5),
            'size': size_of(venue, title),
            'url': str(e.get('url') or '')[:200],
        })

    seen, keep = set(), []
    for e in sorted(out, key=lambda x: (x['d'], x['t'])):
        sig = (e['d'], e['t'], e['venue'], e['name'][:30])
        if sig in seen:
            continue
        seen.add(sig)
        keep.append(e)
    keep = keep[:250]

    print('общо събития:', len(keep))
    big = [e for e in keep if e['size'] >= 1000]
    print('големи (1000+ души):', len(big))
    for e in big[:8]:
        print('  ', e['d'], e['t'], '→', e['end'] or '?', '·',
              e['venue'], '·', e['name'][:36])

    if not keep:
        print('НИЩО НЕ СЕ ИЗТЕГЛИ — не презаписвам стария файл')
        sys.exit(1)

    os.makedirs('data', exist_ok=True)
    with open('data/events.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated': datetime.datetime.now(datetime.timezone.utc)
                         .isoformat(timespec='minutes'),
            'source': 'eventfrog-public-v1',
            'events': keep,
        }, f, ensure_ascii=False, separators=(',', ':'))
    print('записан data/events.json:', os.path.getsize('data/events.json'), 'байта')


if __name__ == '__main__':
    main()
