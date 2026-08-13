#!/usr/bin/env python3
"""Събития в Цюрих — кога тълпа излиза на улицата.

За таксито значение има краят на събитието: три хиляди души излизат от
Hallenstadion в 22:40 и половината търсят превоз. Затова се пази часът
на започване плюс очаквана продължителност според залата.

Първият опит четеше HTML с регулярни изрази и хвана нула — страниците се
градят от JavaScript и разметката се мени. Затова тук се чете JSON-LD:
schema.org/Event, вграден в <script type="application/ld+json">. Този
стандарт го слагат почти всички, за да излизат в Google, и се променя
далеч по-рядко от разметката.

Изход: data/events.json
  {"generated":..., "events":[{d,t,end,name,venue,lat,lng,size,url}]}
"""
import json
import os
import re
import sys
import time
import datetime
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')

# Залата определя колко хора излизат наведнъж и колко трае събитието.
# Разпознава се по името на мястото в самото събитие.
VENUES = [
    ('hallenstadion', 'Hallenstadion',  47.4108, 8.5510, 13000, 165),
    ('letzigrund',    'Letzigrund',     47.3828, 8.5036, 26000, 150),
    ('opernhaus',     'Opernhaus',      47.3650, 8.5460,  1100, 180),
    ('schauspielhaus','Schauspielhaus', 47.3700, 8.5487,   750, 150),
    ('kaufleuten',    'Kaufleuten',     47.3719, 8.5364,  1500, 300),
    ('x-tra',         'X-TRA',          47.3822, 8.5300,  1500, 300),
    ('volkshaus',     'Volkshaus',      47.3757, 8.5297,  1400, 180),
    ('tonhalle',      'Tonhalle',       47.3660, 8.5406,  1400, 150),
    ('kongresshaus',  'Kongresshaus',   47.3657, 8.5364,  1900, 165),
    ('theater 11',    'Theater 11',     47.4102, 8.5527,  1500, 165),
    ('samsung hall',  'Samsung Hall',   47.4028, 8.6073,  1900, 180),
    ('swiss life',    'Swiss Life Hall',47.4108, 8.5510, 13000, 165),
]
DEFAULT = ('Zürich', 47.3769, 8.5417, 500, 150)

SOURCES = [
    'https://www.hallenstadion.ch/en/events',
    'https://www.hallenstadion.ch/de/veranstaltungen',
    'https://www.opernhaus.ch/en/schedule/',
    'https://www.schauspielhaus.ch/en/schedule',
    'https://www.kaufleuten.ch/events/',
    'https://www.x-tra.ch/programm',
    'https://www.tonhalle-orchester.ch/en/concerts/',
    'https://www.zuerich.com/en/visit/events',
]


def fetch(url, tries=2):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'de-CH,de;q=0.9,en;q=0.8',
    })
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                try:
                    return raw.decode('utf-8')
                except UnicodeDecodeError:
                    return raw.decode('iso-8859-1', 'replace')
        except Exception as ex:
            if i == tries - 1:
                print('    неуспех:', type(ex).__name__, str(ex)[:100])
                return ''
            time.sleep(3)
    return ''


def jsonld_blocks(html):
    """Вади всички <script type="application/ld+json"> от страницата."""
    out = []
    for m in re.finditer(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, re.S | re.I):
        txt = m.group(1).strip()
        # някои сайтове слагат по няколко обекта или коментари вътре
        txt = re.sub(r'^\s*//.*$', '', txt, flags=re.M)
        try:
            out.append(json.loads(txt))
        except json.JSONDecodeError:
            continue
    return out


def walk_events(node, found):
    """Обхожда JSON-LD и събира всичко от тип Event."""
    if isinstance(node, list):
        for n in node:
            walk_events(n, found)
        return
    if not isinstance(node, dict):
        return

    t = node.get('@type') or node.get('type') or ''
    types = t if isinstance(t, list) else [t]
    if any('event' in str(x).lower() for x in types):
        found.append(node)

    for key in ('@graph', 'itemListElement', 'item', 'subEvent', 'events'):
        if key in node:
            walk_events(node[key], found)


def venue_of(ev):
    """Познава залата по мястото; ако не успее — общ център."""
    loc = ev.get('location') or {}
    if isinstance(loc, list):
        loc = loc[0] if loc else {}
    name = ''
    if isinstance(loc, dict):
        name = str(loc.get('name') or '')
    blob = (name + ' ' + str(ev.get('name') or '')).lower()

    for key, disp, lat, lng, size, dur in VENUES:
        if key in blob:
            return disp, lat, lng, size, dur

    # координати от самото събитие, ако ги дава
    if isinstance(loc, dict):
        geo = loc.get('geo') or {}
        if isinstance(geo, dict):
            try:
                return (name or DEFAULT[0], float(geo['latitude']),
                        float(geo['longitude']), DEFAULT[3], DEFAULT[4])
            except (KeyError, TypeError, ValueError):
                pass
    return (name or DEFAULT[0],) + DEFAULT[1:]


def parse_start(ev):
    s = ev.get('startDate') or ev.get('startdate') or ''
    if not s:
        return None, None
    s = str(s).strip()
    try:
        dt = datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
    except ValueError:
        m = re.match(r'(\d{4})-(\d{2})-(\d{2})[T ]?(\d{2})?:?(\d{2})?', s)
        if not m:
            return None, None
        y, mo, d, h, mi = m.groups()
        dt = datetime.datetime(int(y), int(mo), int(d),
                               int(h or 20), int(mi or 0))
    return dt.date(), dt.strftime('%H:%M')


def main():
    raw = []
    for url in SOURCES:
        short = url.split('/')[2]
        print('тегля', short)
        html = fetch(url)
        if not html:
            print('   → празно')
            continue
        blocks = jsonld_blocks(html)
        found = []
        for b in blocks:
            walk_events(b, found)
        print('   → %d JSON-LD блока, %d събития' % (len(blocks), len(found)))
        raw += found
        time.sleep(1.2)

    today = datetime.date.today()
    limit = today + datetime.timedelta(days=21)

    out = []
    for ev in raw:
        day, t = parse_start(ev)
        if not day or not t:
            continue
        if not (today <= day <= limit):
            continue
        name = str(ev.get('name') or '').strip()
        if len(name) < 2:
            continue
        vname, lat, lng, size, dur = venue_of(ev)
        try:
            h, mi = [int(x) for x in t.split(':')]
            end = (datetime.datetime.combine(day, datetime.time(h, mi))
                   + datetime.timedelta(minutes=dur)).strftime('%H:%M')
        except ValueError:
            end = ''
        url = ev.get('url') or ''
        if isinstance(url, list):
            url = url[0] if url else ''
        out.append({
            'd': day.isoformat(), 't': t, 'end': end,
            'name': name[:90], 'venue': vname[:40],
            'lat': round(lat, 5), 'lng': round(lng, 5),
            'size': size, 'url': str(url)[:200],
        })

    seen, keep = set(), []
    for e in sorted(out, key=lambda x: (x['d'], x['t'])):
        sig = (e['d'], e['t'], e['venue'], e['name'][:30])
        if sig in seen:
            continue
        seen.add(sig)
        keep.append(e)
    keep = keep[:150]

    print('общо събития:', len(keep))
    for e in keep[:8]:
        print('  ', e['d'], e['t'], '→', e['end'], '·', e['venue'], '·', e['name'][:38])

    if not keep:
        print('НИЩО НЕ СЕ ИЗТЕГЛИ — не презаписвам стария файл')
        sys.exit(1)

    os.makedirs('data', exist_ok=True)
    with open('data/events.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated': datetime.datetime.now(datetime.timezone.utc)
                         .isoformat(timespec='minutes'),
            'events': keep,
        }, f, ensure_ascii=False, separators=(',', ':'))
    print('записан data/events.json:', os.path.getsize('data/events.json'), 'байта')


if __name__ == '__main__':
    main()
