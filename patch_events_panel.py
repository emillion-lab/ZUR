#!/usr/bin/env python3
"""Бутонът ⏱ да показва предстоящите събития вместо празен панел.

„Следващите 90 минути" стоеше празно, защото разчиташе на полети в
тесен прозорец. По-полезно е друго: кои събития свършват скоро.
Хиляда души излизат от залата наведнъж и точно тогава има клиенти —
това е сведението, заради което изобщо теглим Eventfrog.

Показват се идните 5–7, подредени по края, а не по началото: за
таксито значение има кога излизат, не кога влизат.
"""
import sys

JS = 'transport.js'
MARK = 'EVENTS-PANEL'


def main():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    # ── нов вид в таблото ──
    old_kinds = "    flights: { icon:'✈️', title:'Flight arrivals', gsw:'Aachoendi Flüüg' },"
    new_kinds = ("    // EVENTS-PANEL — кога тълпа излиза на улицата\n"
                 "    events:  { icon:'⏱', title:'Ending soon',     gsw:'Hört gly uf'    },\n"
                 "    flights: { icon:'✈️', title:'Flight arrivals', gsw:'Aachoendi Flüüg' },")
    if old_kinds not in src:
        print('ГРЕШКА: не намирам списъка с видове')
        sys.exit(1)
    src = src.replace(old_kinds, new_kinds)

    # ── бутонът ⏱ вече съществува в страницата; закачаме се за него ──
    old_id = "      var id = k === 'flights' ? 'flights-btn' : 'tp-' + k;"
    new_id = ("      var id = k === 'flights' ? 'flights-btn'\n"
              "             : k === 'events'  ? 'next90-btn'\n"
              "             : 'tp-' + k;")
    src = src.replace(old_id, new_id)

    old_id2 = "    var id = kind === 'flights' ? 'flights-btn' : 'tp-' + kind;"
    new_id2 = ("    var id = kind === 'flights' ? 'flights-btn'\n"
               "           : kind === 'events'  ? 'next90-btn'\n"
               "           : 'tp-' + kind;")
    src = src.replace(old_id2, new_id2)

    # ── зареждане ──
    old_load = """    if(kind === 'intl') loadFlix();
    else if(kind !== 'flights') load(kind);"""
    new_load = """    if(kind === 'events') loadEvents();
    else if(kind === 'intl') loadFlix();
    else if(kind !== 'flights') load(kind);"""
    if old_load in src:
        src = src.replace(old_load, new_load)

    loader = """
  // EVENTS-PANEL — събитията идват от data/events.json (Eventfrog).
  // Подреждаме по КРАЯ: таксито го интересува кога излизат хората.
  function loadEvents(){
    var c = cache.events;
    if(c && Date.now() - c.at < 600000){ render(); return; }
    busy = true; render();
    fetch('data/events.json', {cache:'no-cache'})
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(j){
        busy = false;
        var rows = [];
        (j && j.events ? j.events : []).forEach(function(e){
          if(!e.end) return;
          var endTs = new Date(e.d + 'T' + e.end + ':00').getTime();
          // събитие, което свършва след полунощ, се води за следващия ден
          var startTs = new Date(e.d + 'T' + e.t + ':00').getTime();
          if(endTs < startTs) endTs += 86400000;
          rows.push({
            t: e.end,                       // показваме края, не началото
            ts: endTs,
            cat: '',
            line: e.size >= 1000 ? '👥' + Math.round(e.size / 1000) + 'k'
                 : e.size >= 500 ? '👥' + e.size : '',
            from: e.name,
            plat: '',
            delay: 0,
            st: e.venue,
            lat: e.lat, lng: e.lng
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

    # ── събитията се завеждат по свои координати, не по спирка ──
    old_goto = """  function goTo(place){
    var p = place ? PLACES[place] : null;
    if(!p && open === 'flights') p = AIRPORT;"""
    new_goto = """  function goTo(place, lat, lng){
    var p = null;
    if(lat && lng) p = [lat, lng];            // събитията носят свои точки
    if(!p) p = place ? PLACES[place] : null;
    if(!p && open === 'flights') p = AIRPORT;"""
    if old_goto in src:
        src = src.replace(old_goto, new_goto)

    old_bind = """      var row = e.target.closest ? e.target.closest('.tp-row.go') : null;
      if(row) goTo(row.getAttribute('data-go'));"""
    new_bind = """      var row = e.target.closest ? e.target.closest('.tp-row.go') : null;
      if(row) goTo(row.getAttribute('data-go'),
                   parseFloat(row.getAttribute('data-lat')),
                   parseFloat(row.getAttribute('data-lng')));"""
    if old_bind in src:
        src = src.replace(old_bind, new_bind)

    old_row = """      html += '<div class="tp-row go' + (isNow ? ' now' : '') + '"'
            + ' data-go="' + esc(r.st) + '">'"""
    new_row = """      html += '<div class="tp-row go' + (isNow ? ' now' : '') + '"'
            + ' data-go="' + esc(r.st) + '"'
            + (r.lat ? ' data-lat="' + r.lat + '" data-lng="' + r.lng + '"' : '')
            + '>'"""
    if old_row in src:
        src = src.replace(old_row, new_row)

    # ── при събитията „сега" значи „излизат в следващия половин час" ──
    old_now = "      var isNow  = mins !== null && mins >= -5 && mins <= 5;"
    new_now = ("      var isNow  = (open === 'events')\n"
               "                 ? (mins !== null && mins >= -10 && mins <= 30)\n"
               "                 : (mins !== null && mins >= -5 && mins <= 5);")
    if old_now in src:
        src = src.replace(old_now, new_now)

    # ── показваме първите седем, не трийсет ──
    old_slice = "    body.innerHTML = html + '<div class=\"tp-note\">transport.opendata.ch</div>';"
    new_slice = ("    body.innerHTML = html + '<div class=\"tp-note\">'\n"
                 "      + (open === 'events' ? 'eventfrog.ch' : 'transport.opendata.ch')\n"
                 "      + '</div>';")
    if old_slice in src:
        src = src.replace(old_slice, new_slice)

    open(JS, 'w', encoding='utf-8').write(src)
    print('бутонът ⏱ показва предстоящите събития')


if __name__ == '__main__':
    main()
