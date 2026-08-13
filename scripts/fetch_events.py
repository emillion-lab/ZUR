#!/usr/bin/env python3
"""Събития в Цюрих — кога и къде хората излизат наведнъж.

За такси значение има не самото събитие, а краят му: три хиляди души
излизат от Hallenstadion в един и същи момент и търсят превоз. Затова
се вадят начален час и зала, а краят се пресмята по вид събитие.

Източници, по ред на надеждност:
  · zuerich.com — официалният афиш на града
  · eventfrog.ch — местният календар, добър за клубове и по-малки зали
Двата слагат schema.org разметка в страниците си, затова се чете тя,
а не подредбата на HTML-а, която се сменя при всеки редизайн.

Изход: data/events.json
  {"generated":"...", "events":[{date,start,end,name,venue,zone,boost}]}
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

SOURCES = [
    ('zuerich',   'https://www.zuerich.com/en/visit/events'),
    ('eventfrog', 'https://eventfrog.ch/en/s/zurich.html'),
]

# Залите, които познаваме, и в коя зона попадат.
# Ключът е това, което търсим в името на мястото — с малки букви.
VENUES = {
    'hallenstadion':   ('hallenstadion', 3.6),
    'letzigrund':      ('letzigrund',    3.4),
    'stadion letzi':   ('letzigrund',    3.4),
    'opernhaus':       ('opera',         2.8),
    'opera house':     ('opera',         2.8),
    'schauspielhaus':  ('opera',         2.4),
    'tonhalle':        ('opera',         2.4),
    'kaufleuten':      ('zw_clubs',      2.6),
    'x-tra':           ('zw_clubs',      2.6),
    'komplex 457':     ('zw_clubs',      2.6),
    'plaza':           ('zw_clubs',      2.4),
    'mascotte':        ('langstrasse',   2.2),
    'exil':            ('zurich_west',   2.2),
    'dynamo':          ('zurich_west',   2.0),
    'volkshaus':       ('langstrasse',   2.2),
    'kongresshaus':    ('opera',         2.6),
    'samsung hall':    ('hallenstadion', 2.8),
    'the hall':        ('opfikon_gl',    2.6),
    'zürich west':     ('zurich_west',   2.2),
    'prime tower':     ('zurich_west',   2.0),
    'hauptbahnhof':    ('hb',            2.0),
    'landesmuseum':    ('hb',            1.8),
    'kunsthaus':       ('opera',         1.8),
    'uni zürich':      ('uni',           1.8),
    'eth':             ('uni',           1.8),
}

# Колко трае събитието, ако сайтът не казва края
DURATION = [
    (('concert', 'konzert', 'live', 'tour', 'festival'), 3.0),
    (('opera', 'oper', 'ballet', 'ballett'), 3.5),
    (('theatre', 'theater', 'schauspiel'), 2.5),
    (('match', 'spiel', 'game', 'fc ', 'hockey'), 2.5),
    (('club', 'party', 'dj', 'night'), 5.0),
    (('exhibition', 'ausstellung', 'museum'), 0.0),   # няма пик на излизане
]


def fetch(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en,de;q=0.8',
    })
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                return raw.decode('utf-8', 'replace')
        except Exception as ex:
            if i == 2:
                print('    неуспех:', type(ex).__name__, str(ex)[:120])
                return ''
            time.sleep(3 + i * 4)
    return ''


def jsonld(html):
    """Вади всички schema.org блокове от страницата."""
    out = []
    for m in re.finditer(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, re.S | re.I):
        txt = m.group(1).strip()
        try:
            d = json.loads(txt)
        except ValueError:
            continue
        if isinstance(d, list):
            out += d
        elif isinstance(d, dict):
            if '@graph' in d and isinstance(d['@graph'], list):
                out += d['@graph']
            else:
                out.append(d)
    return out


def is_event(node):
    t = node.get('@type') or ''
    if isinstance(t, list):
        t = ' '.join(t)
    return 'Event' in str(t)


def venue_of(node):
    loc = node.get('location') or {}
    if isinstance(loc, list):
        loc = loc[0] if loc else {}
    if isinstance(loc, str):
        return loc
    return (loc.get('name') or '')


def match_zone(venue, name):
    hay = (venue + ' ' + name).lower()
    for key, (zone, boost) in VENUES.items():
        if key in hay:
            return zone, boost
    return None, 0


def duration_for(name):
    low = name.lower()
    for words, hours in DURATION:
        if any(w in low for w in words):
            return hours
    return 2.5


def parse_events(nodes, src):
    out = []
    for n in nodes:
        if not is_event(n):
            continue
        name = (n.get('name') or '').strip()
        start = n.get('startDate') or ''
        if not name or not start or 'T' not in start:
            continue

        venue = venue_of(n)
        zone, boost = match_zone(venue, name)
        if not zone:
            continue                     # зала, която не познаваме

        dur = duration_for(name)
        if dur == 0:
            continue                     # изложба — няма пик на излизане

        try:
            sdt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
        except ValueError:
            continue

        end = n.get('endDate') or ''
        if end and 'T' in end:
            try:
                edt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                end_h = edt.hour + edt.minute / 60
            except ValueError:
                end_h = sdt.hour + sdt.minute / 60 + dur
        else:
            end_h = sdt.hour + sdt.minute / 60 + dur

        if end_h >= 24:
            end_h -= 24

        out.append({
            'date': sdt.date().isoformat(),
            'start': '%02d:%02d' % (sdt.hour, sdt.minute),
            'endHour': round(end_h, 2),
            'name': name[:70],
            'venue': venue[:50],
            'zone': zone,
            'boost': boost,
            'src': src,
        })
    return out


def main():
    events = []
    for src, url in SOURCES:
        print('тегля', src, url)
        html = fetch(url)
        if not html:
            continue
        nodes = jsonld(html)
        print('   schema.org блокове:', len(nodes))
        got = parse_events(nodes, src)
        print('   разпознати събития в познати зали:', len(got))
        events += got
        time.sleep(2)

    # едно събитие може да е и на двата сайта
    seen, keep = set(), []
    for e in sorted(events, key=lambda x: (x['date'], x['endHour'])):
        sig = (e['date'], e['zone'], e['name'][:25].lower())
        if sig in seen:
            continue
        seen.add(sig)
        keep.append(e)

    # само отсега нататък, до седмица напред
    today = datetime.date.today().isoformat()
    week = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
    keep = [e for e in keep if today <= e['date'] <= week][:60]

    print('общо събития:', len(keep))
    for e in keep[:6]:
        print('  ', e['date'], e['start'], '→', e['endHour'],
              e['zone'], '·', e['name'][:40])

    out = {
        'generated': datetime.datetime.now(datetime.timezone.utc)
                     .isoformat(timespec='minutes'),
        'events': keep,
    }
    os.makedirs('data', exist_ok=True)
    with open('data/events.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('записан data/events.json:', os.path.getsize('data/events.json'), 'байта')

    if not keep:
        print('ВНИМАНИЕ: нула събития — разметката вероятно се е сменила')


if __name__ == '__main__':
    main()
