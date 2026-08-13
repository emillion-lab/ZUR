#!/usr/bin/env python3
"""Събития в Цюрих през Eventfrog Public API v1.

Написано по официалната спецификация (docs/EVENTFROG-API.md).

Първата работеща версия показваше „Zürich" вместо името на залата.
Три причини, всичките от невнимателно четене на спецификацията:

  · `perPage` е до 1000, не 100 — теглех по стотица и спирах на първите
    хиляда места, а събитието сочеше към зала извън тях
  · `/locations` приема списък `id` — вместо да събирам всички места в
    радиуса и да се надявам, питам точно за залите, които събитията
    ползват
  · `locationAlias` не е името на залата, а алтернативно название
    („Main Stage Area"); почти винаги е празно, затова падаше на града

За таксито значение има краят: хиляда души излизат наведнъж и
половината търсят превоз. `end` идва наготово от интерфейса.

Ключ: repo secret EVENTFROG_KEY.
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

LAT, LNG, RADIUS = 47.3769, 8.5417, 15      # километри около центъра
DAYS_AHEAD = 21
PER_PAGE = 1000                             # таванът по спецификация

# Колко души излизат наведнъж. Продължителността идва от събитието.
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
    """Bearer по спецификация; при отказ пробва остарелия apiKey."""
    qs = urllib.parse.urlencode(params, doseq=True)   # explode=true за списъци
    url = BASE + path + '?' + qs
    for use_bearer in (True, False):
        u = url if use_bearer else url + '&apiKey=' + urllib.parse.quote(KEY)
        headers = {'User-Agent': 'zur-taxi-radar', 'Accept': 'application/json'}
        if use_bearer:
            headers['Authorization'] = 'Bearer ' + KEY
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(u, headers=headers), timeout=40) as r:
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
            return str(v).strip()
    for v in multi.values():
        if v:
            return str(v).strip()
    return ''


def fetch_events(today, until):
    rows, page = [], 1
    while page <= 6:
        d = call('/events', {
            'lat': LAT, 'lng': LNG, 'r': RADIUS,
            'from': today.isoformat(), 'to': until.isoformat(),
            'page': page, 'perPage': PER_PAGE, 'country': 'CH',
        })
        if not d:
            break
        got = d.get('events') or []
        total = d.get('totalNumberOfResources')
        print('   страница %d → %d%s' % (page, len(got),
              (' от %s' % total) if total else ''))
        if not got:
            break
        rows += got
        if len(got) < PER_PAGE or len(rows) >= (total or 0):
            break
        page += 1
        time.sleep(0.6)
    return rows


def fetch_locations(ids):
    """Пита точно за залите, които събитията ползват — без налучкване."""
    locs = {}
    ids = [i for i in ids if i]
    for i in range(0, len(ids), 200):          # на порции, за да не е дълъг адресът
        chunk = ids[i:i + 200]
        d = call('/locations', {'id': chunk, 'perPage': PER_PAGE})
        if not d:
            continue
        got = d.get('locations') or []
        for l in got:
            locs[str(l.get('id'))] = {
                'name': pick(l.get('title')) or (l.get('city') or ''),
                'lat': l.get('lat'), 'lng': l.get('lng'),
                'city': l.get('city') or '',
            }
        print('   зали %d–%d → %d' % (i, i + len(chunk), len(got)))
        time.sleep(0.5)
    return locs


def main():
    if not KEY:
        print('НЯМА КЛЮЧ. repo secret EVENTFROG_KEY липсва.')
        sys.exit(1)

    today = datetime.date.today()
    until = today + datetime.timedelta(days=DAYS_AHEAD)

    print('тегля събитията…')
    raw = fetch_events(today, until)
    print('   общо изтеглени:', len(raw))
    if not raw:
        print('НИЩО НЕ СЕ ИЗТЕГЛИ — не презаписвам стария файл')
        sys.exit(1)

    # кои зали изобщо ни трябват
    wanted = []
    for e in raw:
        for lid in (e.get('locationIds') or []):
            if lid not in wanted:
                wanted.append(str(lid))
    print('тегля', len(wanted), 'зали по идентификатор…')
    locs = fetch_locations(wanted)
    print('   намерени:', len(locs))

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

        venue, lat, lng = '', None, None
        for lid in (e.get('locationIds') or []):
            l = locs.get(str(lid))
            if l and l['name']:
                venue, lat, lng = l['name'], l['lat'], l['lng']
                break
        if not venue:
            # алтернативното име е рядко, но когато го има, е по-точно от нищо
            venue = pick(e.get('locationAlias'))
        try:
            lat, lng = float(lat), float(lng)
        except (TypeError, ValueError):
            lat, lng = LAT, LNG

        end_txt = ''
        if e.get('end'):
            try:
                end_txt = datetime.datetime.fromisoformat(
                    str(e['end']).replace('Z', '+00:00')).strftime('%H:%M')
            except ValueError:
                pass

        out.append({
            'd': day.isoformat(), 't': dt.strftime('%H:%M'), 'end': end_txt,
            'name': title[:90], 'venue': (venue or 'Zürich')[:40],
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
    keep = keep[:300]

    named = sum(1 for e in keep if e['venue'] != 'Zürich')
    print('общо събития:', len(keep), '· с разпозната зала:', named)
    big = [e for e in keep if e['size'] >= 1000]
    print('големи (1000+ души):', len(big))
    for e in big[:8]:
        print('  ', e['d'], e['t'], '→', e['end'] or '?', '·',
              e['venue'], '·', e['name'][:34])

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
