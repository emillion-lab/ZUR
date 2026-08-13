#!/usr/bin/env python3
"""Събития в Цюрих — кога тълпа излиза на улицата.

За таксито значение има не самото събитие, а краят му: три хиляди души
излизат от Hallenstadion в 22:40 и половината търсят превоз. Затова се
пази часът на започване, очакваната продължителност и мястото.

Източници — залите, които събират хора наведнъж:
  · Hallenstadion      (~13 000) концерти, спорт
  · Letzigrund         (~26 000) футбол, лека атлетика, големи концерти
  · Opernhaus          (~1 100)  опера и балет
  · Schauspielhaus     (~750)    театър
  · Kaufleuten / X-TRA (~1 500)  клубни вечери

Всеки източник е отделна функция. Ако един се счупи, останалите работят
и това личи в лога.

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
import html as htmllib

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')

VENUES = {
    'hallenstadion': {
        'name': 'Hallenstadion', 'lat': 47.4108, 'lng': 8.5510,
        'size': 13000, 'dur': 165,
    },
    'letzigrund': {
        'name': 'Letzigrund', 'lat': 47.3828, 'lng': 8.5036,
        'size': 26000, 'dur': 150,
    },
    'opernhaus': {
        'name': 'Opernhaus', 'lat': 47.3650, 'lng': 8.5460,
        'size': 1100, 'dur': 180,
    },
    'schauspielhaus': {
        'name': 'Schauspielhaus', 'lat': 47.3700, 'lng': 8.5487,
        'size': 750, 'dur': 150,
    },
    'kaufleuten': {
        'name': 'Kaufleuten', 'lat': 47.3719, 'lng': 8.5364,
        'size': 1500, 'dur': 300,
    },
}


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
                for enc in ('utf-8', 'iso-8859-1', 'cp1252'):
                    try:
                        return raw.decode(enc)
                    except UnicodeDecodeError:
                        continue
                return raw.decode('utf-8', 'replace')
        except Exception as ex:
            if i == tries - 1:
                print('    неуспех:', type(ex).__name__, str(ex)[:110])
                return ''
            time.sleep(3)
    return ''


def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = htmllib.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()


def end_time(day, hhmm, minutes):
    try:
        h, m = [int(x) for x in hhmm.split(':')]
    except ValueError:
        return ''
    start = datetime.datetime.combine(day, datetime.time(h, m))
    return (start + datetime.timedelta(minutes=minutes)).strftime('%H:%M')


def add(out, key, day, t, name, url=''):
    v = VENUES[key]
    if not t or not name:
        return
    out.append({
        'd': day.isoformat(),
        't': t,
        'end': end_time(day, t, v['dur']),
        'name': name[:90],
        'venue': v['name'],
        'lat': v['lat'], 'lng': v['lng'],
        'size': v['size'],
        'url': url,
    })


# ── Hallenstadion ──────────────────────────────────────────────
def scrape_hallenstadion(out):
    h = fetch('https://www.hallenstadion.ch/en/events')
    if not h:
        return 0
    n = 0
    # блокове с дата и заглавие; структурата се мени, затова се търси
    # съчетание от дата и час, а не точен клас
    for m in re.finditer(
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})(.{0,400}?)(\d{1,2}[:.]\d{2})',
            h, re.S):
        d, mo, y, mid, t = m.groups()
        try:
            day = datetime.date(int(y), int(mo), int(d))
        except ValueError:
            continue
        if day < datetime.date.today():
            continue
        title = clean(mid)[:90]
        if len(title) < 3:
            continue
        add(out, 'hallenstadion', day, t.replace('.', ':'), title)
        n += 1
        if n >= 25:
            break
    return n


# ── Letzigrund ─────────────────────────────────────────────────
def scrape_letzigrund(out):
    h = fetch('https://www.stadion-letzigrund.ch/veranstaltungen')
    if not h:
        return 0
    n = 0
    for m in re.finditer(
            r'(\d{1,2})\.\s*(\w+)\s*(\d{4})(.{0,300}?)(\d{1,2}[:.]\d{2})',
            h, re.S):
        d, mon, y, mid, t = m.groups()
        mo = month_num(mon)
        if not mo:
            continue
        try:
            day = datetime.date(int(y), mo, int(d))
        except ValueError:
            continue
        if day < datetime.date.today():
            continue
        title = clean(mid)[:90]
        if len(title) < 3:
            continue
        add(out, 'letzigrund', day, t.replace('.', ':'), title)
        n += 1
        if n >= 15:
            break
    return n


# ── Opernhaus ──────────────────────────────────────────────────
def scrape_opernhaus(out):
    h = fetch('https://www.opernhaus.ch/en/schedule/')
    if not h:
        return 0
    n = 0
    for m in re.finditer(
            r'(\d{4})-(\d{2})-(\d{2})(.{0,300}?)(\d{1,2}[:.]\d{2})',
            h, re.S):
        y, mo, d, mid, t = m.groups()
        try:
            day = datetime.date(int(y), int(mo), int(d))
        except ValueError:
            continue
        if day < datetime.date.today():
            continue
        title = clean(mid)[:90]
        if len(title) < 3:
            continue
        add(out, 'opernhaus', day, t.replace('.', ':'), title)
        n += 1
        if n >= 25:
            break
    return n


MONTHS = {
    'januar':1, 'january':1, 'jan':1, 'februar':2, 'february':2, 'feb':2,
    'märz':3, 'maerz':3, 'march':3, 'mär':3, 'mar':3,
    'april':4, 'apr':4, 'mai':5, 'may':5, 'juni':6, 'june':6, 'jun':6,
    'juli':7, 'july':7, 'jul':7, 'august':8, 'aug':8,
    'september':9, 'sept':9, 'sep':9, 'oktober':10, 'october':10, 'okt':10,
    'november':11, 'nov':11, 'dezember':12, 'december':12, 'dez':12, 'dec':12,
}


def month_num(s):
    return MONTHS.get((s or '').strip().lower())


def main():
    out = []
    jobs = [
        ('Hallenstadion',  scrape_hallenstadion),
        ('Letzigrund',     scrape_letzigrund),
        ('Opernhaus',      scrape_opernhaus),
    ]
    for name, fn in jobs:
        print('тегля', name)
        try:
            got = fn(out)
        except Exception as ex:
            print('    счупен парсер:', type(ex).__name__, str(ex)[:110])
            got = 0
        print('   →', got, 'събития')
        time.sleep(1.5)

    # едно събитие се появява по няколко пъти при широкия израз
    seen, keep = set(), []
    for e in sorted(out, key=lambda x: (x['d'], x['t'])):
        sig = (e['d'], e['t'], e['venue'])
        if sig in seen:
            continue
        seen.add(sig)
        keep.append(e)

    # само отсега напред, две седмици стигат
    today = datetime.date.today().isoformat()
    limit = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
    keep = [e for e in keep if today <= e['d'] <= limit][:120]

    print('общо събития:', len(keep))
    for e in keep[:6]:
        print('  ', e['d'], e['t'], '→', e['end'], e['venue'], '·', e['name'][:40])

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
