#!/usr/bin/env python3
"""Събитията влизат в таблото.

Панелът „следващите 90 минути" стоеше празен, а тъкмо той трябва да
казва какво предстои. Затова събитията получават свой бутон 🎫 и се
подреждат по КРАЯ, не по началото: концертът в 20:00 не носи клиенти,
но същият концерт в 23:45 изсипва хиляда души наведнъж.

Показват се идните пет-седем, с обратно броене до края и с размера на
залата, за да личи кое си струва.

Данните идват от data/events.json (Eventfrog, обновява се нощем).
"""
import sys

JS = 'transport.js'
HTML = 'index.html'
MARK = 'EVENTS-PANEL'
CSS_MARK = '/* ZUR-RAIL-V5 */'

CSS = CSS_MARK + """
/* ── Шест бутона за пристигащи и предстоящи, отдолу нагоре ──
   ⛶ 16 · 📍 72 · ⏱ 128 · ✈️ 184 · 🚂 240 · 🚌 296 · 🌍 352 · 🎫 408 · 📋 464 */
#tp-events{ display:flex !important; }

#fs-btn      { bottom:16px  !important; top:auto !important; }
#gps-btn     { bottom:72px  !important; top:auto !important; }
#next90-btn  { bottom:128px !important; top:auto !important; }
#flights-btn { bottom:184px !important; top:auto !important; }
#tp-train    { bottom:240px !important; top:auto !important; }
#tp-bus      { bottom:296px !important; top:auto !important; }
#tp-intl     { bottom:352px !important; top:auto !important; }
#tp-events   { bottom:408px !important; top:auto !important; }
#list-btn    { bottom:464px !important; top:auto !important; }

@media (max-height:800px), (max-width:400px){
  #fs-btn      { bottom:10px  !important; }
  #gps-btn     { bottom:56px  !important; }
  #next90-btn  { bottom:102px !important; }
  #flights-btn { bottom:148px !important; }
  #tp-train    { bottom:194px !important; }
  #tp-bus      { bottom:240px !important; }
  #tp-intl     { bottom:286px !important; }
  #tp-events   { bottom:332px !important; }
  #list-btn    { bottom:378px !important; }
}

/* размерът на залата — колко души излизат наведнъж */
.tp-size{ font-size:12px; color:var(--muted); min-width:44px; text-align:right }
.tp-row.big .tp-size{ color:var(--orange); font-weight:700 }
"""


def patch_js():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('transport.js: вече е приложено')
        return

    # ── нов вид ──
    old_kinds = """    intl:    { icon:'🌍', title:'Intl. coaches',    gsw:'Uslandbüs'    }"""
    new_kinds = """    intl:    { icon:'🌍', title:'Intl. coaches',    gsw:'Uslandbüs'    },
    // EVENTS-PANEL — подредени по края: тогава тълпата излиза
    events:  { icon:'🎫', title:'Events ending',   gsw:'Events am Ändi' }"""
    if old_kinds not in src:
        print('ГРЕШКА: не намирам списъка с видове')
        sys.exit(1)
    src = src.replace(old_kinds, new_kinds)

    # ── зареждане ──
    old_load = "    if(kind === 'intl') loadFlix();"
    new_load = ("    if(kind === 'events') loadEvents();\n"
                "    else if(kind === 'intl') loadFlix();")
    if old_load in src:
        src = src.replace(old_load, new_load)

    loader = """
  // EVENTS-PANEL — идните събития по КРАЯ. Началото не значи нищо за
  // таксито; краят е моментът, в който залата се изпразва наведнъж.
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
          // краят може да мине през полунощ
          var endTs = new Date(e.d + 'T' + e.end + ':00').getTime();
          var startTs = new Date(e.d + 'T' + e.t + ':00').getTime();
          if(endTs < startTs) endTs += 86400000;
          if(endTs < Date.now() - 900000) return;      // свършило отдавна
          rows.push({
            t: e.end,                                   // показваме края
            ts: endTs,
            cat: '',
            line: e.t,                                  // началото като второстепенно
            from: e.name,
            plat: '',
            delay: 0,
            st: e.venue,
            size: e.size || 0,
            lat: e.lat, lng: e.lng
          });
        });
        rows.sort(function(a, b){ return a.ts - b.ts; });
        cache.events = { rows: rows.slice(0, 40), at: Date.now(), live: false };
        render();
      })
      .catch(function(){ busy = false; render(); });
  }

  function crowd(n){
    if(!n) return '';
    return n >= 1000 ? Math.round(n / 1000) + 'k' : String(n);
  }
"""
    src = src.replace('  function render(){', loader + '\n  function render(){', 1)

    # ── редът за събитие изглежда различно ──
    old_row = """      html += '<div class="tp-row go' + (isNow ? ' now' : '') + '"'
            + ' data-go="' + esc(r.st) + '">'"""
    new_row = """      var big = (r.size || 0) >= 1000 ? ' big' : '';
      html += '<div class="tp-row go' + (isNow ? ' now' : '') + big + '"'
            + ' data-go="' + esc(r.st) + '"'
            + (r.lat ? ' data-lat="' + r.lat + '" data-lng="' + r.lng + '"' : '')
            + '>'"""
    if old_row in src:
        src = src.replace(old_row, new_row)

    # размерът на залата вместо стрелката при събитията
    old_end = """            + '<span class="tp-go">›</span>'
            + '</div>';"""
    new_end = """            + (r.size ? '<span class="tp-size">' + crowd(r.size) + '</span>' : '')
            + '<span class="tp-go">›</span>'
            + '</div>';"""
    if old_end in src:
        src = src.replace(old_end, new_end, 1)

    # ── картата отива на точните координати, ако ги има ──
    old_go = """      var row = e.target.closest ? e.target.closest('.tp-row.go') : null;
      if(row) goTo(row.getAttribute('data-go'));"""
    new_go = """      var row = e.target.closest ? e.target.closest('.tp-row.go') : null;
      if(!row) return;
      var la = row.getAttribute('data-lat'), ln = row.getAttribute('data-lng');
      if(la && ln) goToPoint([parseFloat(la), parseFloat(ln)]);
      else goTo(row.getAttribute('data-go'));"""
    if old_go in src:
        src = src.replace(old_go, new_go)

    # обща функция за отиване на точка
    src = src.replace("  function goTo(place){",
        """  function goToPoint(p){
    if(!p || !p[0]) return;
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

  function goTo(place){""", 1)

    # ── заглавията по вид ──
    src = src.replace("      var map = {train:'trains', tram:'trams', bus:'buses', intl:'intl'};",
                      "      var map = {train:'trains', bus:'buses', intl:'intl', events:'events'};")

    # ── освежаване при връщане ──
    src = src.replace("        if(open === 'intl') loadFlix(); else load(open);",
                      "        if(open === 'events') loadEvents();\n"
                      "        else if(open === 'intl') loadFlix();\n"
                      "        else load(open);")

    open(JS, 'w', encoding='utf-8').write(src)
    print('transport.js: събитията са в таблото, подредени по края')


def patch_html():
    src = open(HTML, encoding='utf-8').read()
    if CSS_MARK in src:
        print('index.html: колоната вече е преномерирана')
        return
    i = src.rfind('</style>')
    if i < 0:
        print('ГРЕШКА: няма </style>')
        sys.exit(1)
    src = src[:i] + CSS + '\n' + src[i:]
    open(HTML, 'w', encoding='utf-8').write(src)
    print('index.html: добавен бутон за събития')


if __name__ == '__main__':
    patch_js()
    patch_html()
