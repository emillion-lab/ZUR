#!/usr/bin/env python3
"""Таблото 🌍 да чете истинските международни автобуси.

Досега бутонът питаше швейцарския API, който не знае FlixBus, и оставаше
празен. Сега чете data/flixbus.json — пристигания, събрани от самия
FlixBus чрез обратно търсене (от двайсетина града към Цюрих).

Швейцарският API остава за влаковете и градските автобуси.
"""
import sys

JS = 'transport.js'
MARK = 'INTL-FLIX'


def main():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    # международните вече не минават през швейцарския API
    old_load = "    if(kind !== 'flights') load(kind);"
    new_load = ("    if(kind === 'intl') loadFlix();\n"
                "    else if(kind !== 'flights') load(kind);")
    if old_load not in src:
        print('ГРЕШКА: не намирам извикването на load')
        sys.exit(1)
    src = src.replace(old_load, new_load)

    loader = """
  // INTL-FLIX — международните идват от собствения ни файл, защото
  // швейцарското разписание не ги съдържа. Файлът се пълни четири пъти
  // дневно от scripts/fetch_flixbus.py.
  function loadFlix(){
    var c = cache.intl;
    if(c && Date.now() - c.at < 300000){ render(); return; }
    busy = true; render();
    fetch('data/flixbus.json', {cache:'no-cache'})
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(j){
        busy = false;
        if(!j || !j.arrivals){ cache.intl = {rows:[], at:Date.now(), live:false}; render(); return; }
        var rows = j.arrivals.map(function(r){
          return {
            t: r.t,
            ts: (r.ts || 0) * 1000,
            cat: '',
            line: r.operator || 'FlixBus',
            from: r.from + (r.transfers ? ' · ' + r.transfers + '×' : ''),
            plat: r.station === 'Sihlquai' ? '' : (r.station || ''),
            delay: 0,
            st: r.station || 'Sihlquai'
          };
        });
        cache.intl = { rows: rows, at: new Date(j.generated).getTime(), live: false };
        render();
      })
      .catch(function(){ busy = false; render(); });
  }
"""
    src = src.replace('  function render(){', loader + '\n  function render(){', 1)

    # обяснението при липса вече е друго: файлът просто още не е пълнен
    src = src.replace(
        """      return isGsw()
        ? 'Kei Uslandbüs im Fahrplaa.<br><span style="font-size:12px">'
          + 'FlixBus &amp; Co. gänd ihri Zite nöd a d\\u2019SBB wiiter.<br>'
          + 'Terminal: Carparkplatz Sihlquai</span>'
        : 'International coaches are not in the Swiss timetable.'
          + '<br><span style="font-size:12px">FlixBus and others do not publish '
          + 'to SBB, so nothing can be shown here.<br>'
          + 'Terminal: Carparkplatz Sihlquai, next to the main station</span>';""",
        """      return isGsw()
        ? 'Hüt chunnt kei Uslandbus meh.<br><span style="font-size:12px">'
          + 'Terminal: Carparkplatz Sihlquai</span>'
        : 'No more coaches arriving today.'
          + '<br><span style="font-size:12px">'
          + 'Terminal: Carparkplatz Sihlquai, next to the main station</span>';""")

    # освежаването при връщане в приложението важи и за международните
    src = src.replace(
        "      if(!document.hidden && open && open !== 'flights'){\n"
        "        delete cache[open];\n"
        "        load(open);\n"
        "      }",
        "      if(!document.hidden && open && open !== 'flights'){\n"
        "        delete cache[open];\n"
        "        if(open === 'intl') loadFlix(); else load(open);\n"
        "      }")

    open(JS, 'w', encoding='utf-8').write(src)
    print('таблото 🌍 чете data/flixbus.json')


if __name__ == '__main__':
    main()
