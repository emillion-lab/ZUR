#!/usr/bin/env python3
"""Два отделни бутона: междуградски и международни автобуси.

Досега имаше само международните (FlixBus). Междуградските — швейцарските
регионални линии, които довеждат хора от околните градчета до Цюрих —
липсваха, а именно те носят пътник с багаж до гарата.

Как се различават от градските:
  · градските линии в Цюрих са с едно- или двуцифрен номер (31, 46, 72)
  · регионалните и междуградските са трицифрени (912, 750) или са
    PostAuto, чиито курсове идват от съседните общини
Затова тук минава само трицифреният номер и всичко, което не е градско.

Иконите:
  🚌 междуградски (в страната)   🚍→🌍 международни (от чужбина)
"""
import sys

JS = 'transport.js'
HTML = 'index.html'
MARK = 'REGIONAL-BUS'
CSS_MARK = '/* ZUR-RAIL-V4 */'

CSS = CSS_MARK + """
/* ── Пет бутона за пристигащи, отдолу нагоре ──
   ⛶ 16 · 📍 72 · ⏱ 128 · ✈️ 184 · 🚂 240 · 🚌 296 · 🌍 352 · 📋 408 */
#tp-tram{ display:none !important; }
#tp-bus { display:flex !important; }

#fs-btn      { bottom:16px  !important; top:auto !important; }
#gps-btn     { bottom:72px  !important; top:auto !important; }
#next90-btn  { bottom:128px !important; top:auto !important; }
#flights-btn { bottom:184px !important; top:auto !important; }
#tp-train    { bottom:240px !important; top:auto !important; }
#tp-bus      { bottom:296px !important; top:auto !important; }
#tp-intl     { bottom:352px !important; top:auto !important; }
#list-btn    { bottom:408px !important; top:auto !important; }

@media (max-height:760px), (max-width:400px){
  #fs-btn      { bottom:12px  !important; }
  #gps-btn     { bottom:60px  !important; }
  #next90-btn  { bottom:108px !important; }
  #flights-btn { bottom:156px !important; }
  #tp-train    { bottom:204px !important; }
  #tp-bus      { bottom:252px !important; }
  #tp-intl     { bottom:300px !important; }
  #list-btn    { bottom:348px !important; }
}
"""


def patch_js():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('transport.js: вече е приложено')
        return

    # ── двата вида си идват на място ──
    old_kinds = """    // NO-CITY-BUS — градските отпадат: слезлият в центъра не търси такси
    intl:    { icon:'🌍', title:'Intl. coaches',   gsw:'Uslandbüs'      }"""
    new_kinds = """    // REGIONAL-BUS — градските отпадат (слезлият в центъра не търси такси),
    // но междуградските остават: те докарват хора с багаж от околните градчета
    bus:     { icon:'🚌', title:'Regional coaches', gsw:'Regionalbüs'  },
    intl:    { icon:'🌍', title:'Intl. coaches',    gsw:'Uslandbüs'    }"""
    if old_kinds not in src:
        print('ГРЕШКА: не намирам списъка с видове')
        sys.exit(1)
    src = src.replace(old_kinds, new_kinds)

    # ── спирките, където слизат регионалните ──
    old_stops = """    bus: [
      ['Zürich, Bahnhofquai/HB', 'Bahnhofquai'],
      ['Zürich, Central',        'Central'],
      ['Zürich, Bellevue',       'Bellevue']
    ],"""
    new_stops = """    // Регионалните спират на гаровите площади, не по градските спирки
    bus: [
      ['Zürich HB',              'HB'],
      ['Zürich, Bahnhofquai/HB', 'Bahnhofquai'],
      ['Zürich Oerlikon',        'Oerlikon'],
      ['Zürich, Bellevue',       'Bellevue'],
      ['Zürich Flughafen',       'Flughafen']
    ],"""
    if old_stops in src:
        src = src.replace(old_stops, new_stops)

    # ── филтърът: градските отпадат по номер ──
    old_filter = "          if(kind === 'bus' && !BUS_CAT[cat]) return null;"
    new_filter = """          if(kind === 'bus'){
            if(!BUS_CAT[cat]) return null;
            // REGIONAL-BUS — градските линии в Цюрих са едно- или
            // двуцифрени (31, 46, 72); регионалните са трицифрени или
            // носят име на превозвач. Само вторите докарват клиенти.
            var num = String(e.number || '').trim();
            if(/^\\d{1,2}$/.test(num)) return null;
          }"""
    if old_filter in src:
        src = src.replace(old_filter, new_filter)

    open(JS, 'w', encoding='utf-8').write(src)
    print('transport.js: междуградските се връщат, градските остават отсети')


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
    print('index.html: колоната е с пет бутона за пристигащи')


if __name__ == '__main__':
    patch_js()
    patch_html()
