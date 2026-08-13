#!/usr/bin/env python3
"""Събитията влизат в таблото — подредени по края, не по началото.

Панелът „следващите 90 минути" стоеше празен, а `data/events.json` вече
се пълни всяка нощ от Eventfrog. Затова събитията си получават бутон
като останалите видове.

Подредбата е по КРАЯ на събитието, не по началото. Началото не носи
клиенти — хората идват разпръснато и повечето с градски транспорт.
Краят е моментът, когато хиляда души излизат наведнъж и половината
търсят превоз. Затова редът показва „свършва в 23:45", а часът на
започване стои по-дребно отдолу.

Показват се следващите 7, плюс тези, които свършват в момента.
"""
import sys

JS = 'transport.js'
MARK = 'EVENTS-KIND'


def main():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    # ── новият вид ──
    old_kinds = """    intl:    { icon:'🌍', title:'Intl. coaches',    gsw:'Uslandbüs'    }"""
    new_kinds = """    intl:    { icon:'🌍', title:'Intl. coaches',    gsw:'Uslandbüs'    },
    // EVENTS-KIND — подредени по края: тогава излиза тълпата
    events:  { icon:'🎫', title:'Events ending',    gsw:'Events am Ände' }"""
    if old_kinds not in src:
        print('ГРЕШКА: не намирам списъка с видове')
        sys.exit(1)
    src = src.replace(old_kinds, new_kinds)

    # ── зареждане ──
    old_load = "    if(kind === 'intl') loadFlix();"
    new_load = """    if(kind === 'events') loadEvents();
    else if(kind === 'intl') loadFlix();"""
    if old_load not in src:
        print('ГРЕШКА: не намирам разклонението при отваряне')
        sys.exit(1)
    src = src.replace(old_load, new_load)

    loader = """
  // EVENTS-KIND — от data/events.json, пълнен всяка нощ от Eventfrog.
  // Подреждаме по края: началото не носи клиенти, краят носи.
  function loadEvents(){
    var c = cache.events;
    if(c && Date.now() - c.at < 600000){ render(); return; }
    busy = true; render();
    fetch('data/events.json', {cache:'no-cache'})
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(j){
        busy = false;
        var rows = [];
        (j && j.events || []).forEach(function(e){
          if(!e.end) return;                       // без край не върши работа
          var endTs = Date.parse(e.d + 'T' + e.end + ':00');
          var begTs = Date.parse(e.d + 'T' + e.t + ':00');
          // събитие след полунощ свършва на следващия ден
          if(endTs < begTs) endTs += 86400000;
          rows.push({
            t: e.end,                              // часът, който ни интересува
            ts: endTs,
            cat: '',
            line: e.size >= 1000 ? '★' : '',       // големите се открояват
            from: e.name,
            plat: '',
            delay: 0,
            st: e.venue || 'Zürich',
            lat: e.lat, lng: e.lng,
            began: e.t,
            size: e.size || 0
          });
        });
        rows.sort(function(a, b){ return a.ts - b.ts; });
        cache.events = { rows: rows, at: Date.now(), live: false };
        render();
      })
      .catch(function(){ busy = false; render(); });
  }
"""
    src = src.replace('  function render(){', loader + '\n  function render(){', 1)

    # ── редът: край едро, начало и зала дребно ──
    old_row = """      html += '<div class="tp-row go' + (isNow ? ' now' : '') + '"'
            + ' data-go="' + esc(r.st) + '">'
            + '<span class="tp-t">' + r.t + late + '</span>'
            + '<span class="tp-line">' + esc(r.cat) + esc(r.line) + '</span>'
            + '<span class="tp-to">' + esc(r.from)
            + '<span class="tp-st">' + esc(r.st) + inTxt + '</span></span>'
            + '<span class="tp-go">›</span>'
            + '</div>';"""
    new_row = """      var sub = open === 'events'
        ? esc(r.st) + ' · ' + (isGsw() ? 'aa ' : 'from ') + r.began + inTxt
        : esc(r.st) + inTxt;
      html += '<div class="tp-row go' + (isNow ? ' now' : '') + '"'
            + ' data-go="' + esc(r.st) + '"'
            + (r.lat ? ' data-lat="' + r.lat + '" data-lng="' + r.lng + '"' : '')
            + '>'
            + '<span class="tp-t">' + r.t + late + '</span>'
            + '<span class="tp-line">' + esc(r.cat) + esc(r.line) + '</span>'
            + '<span class="tp-to">' + esc(r.from)
            + '<span class="tp-st">' + sub + '</span></span>'
            + '<span class="tp-go">›</span>'
            + '</div>';"""
    if old_row not in src:
        print('ГРЕШКА: не намирам реда в render')
        sys.exit(1)
    src = src.replace(old_row, new_row)

    # ── залата няма запис в PLACES; ползваме координатите от събитието ──
    old_click = """      var row = e.target.closest ? e.target.closest('.tp-row.go') : null;
      if(row) goTo(row.getAttribute('data-go'));"""
    new_click = """      var row = e.target.closest ? e.target.closest('.tp-row.go') : null;
      if(!row) return;
      var la = row.getAttribute('data-lat'), ln = row.getAttribute('data-lng');
      if(la && ln) goToPoint([parseFloat(la), parseFloat(ln)]);
      else goTo(row.getAttribute('data-go'));"""
    if old_click in src:
        src = src.replace(old_click, new_click)

    # goTo работи по име; за залите ни трябва по точка
    src = src.replace("  function goTo(place){",
        """  function goToPoint(p){
    if(!p || isNaN(p[0])) return;
    close();
    setTimeout(function(){
      try{
        if(document.body.classList.contains('list-view')
           && window.toggleMapView) window.toggleMapView();
        if(window.map){
          window.map.invalidateSize();
          window.map.flyTo(p, 15, {duration: 0.9});
        }
      }catch(e){}
    }, 60);
  }

  function goTo(place){""")

    # ── показваме седем, не трийсет: това е смяна, не програма ──
    src = src.replace("    body.innerHTML = html + '<div class=\"tp-note\">transport.opendata.ch</div>';",
        """    body.innerHTML = html + '<div class="tp-note">'
      + (open === 'events' ? 'eventfrog.ch' : 'transport.opendata.ch')
      + '</div>';""")

    open(JS, 'w', encoding='utf-8').write(src)
    print('събитията са в таблото, подредени по края')


if __name__ == '__main__':
    main()
