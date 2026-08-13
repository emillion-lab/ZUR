#!/usr/bin/env python3
"""Градските автобуси отпадат от ZUR.

Човек, слязъл от автобус 46 на Bahnhofquai, е в центъра и продължава
пеша или с трамвай — не търси такси. Клиенти идват от междуградските:
пристигналият от Милано с куфар в 05:50 има нужда от превоз до хотела.

Затова 🚌 се маха, а 🌍 остава. Колоната се преномерира, за да няма
дупка на мястото му.
"""
import sys

JS = 'transport.js'
HTML = 'index.html'
MARK = 'NO-CITY-BUS'
CSS_MARK = '/* ZUR-RAIL-V3 */'

CSS = CSS_MARK + """
/* ── Колоната без градските автобуси: 4 бутона за пристигащи ──
   ⛶ 16 · 📍 72 · ⏱ 128 · ✈️ 184 · 🚂 240 · 🌍 296 · 📋 352 */
#tp-bus, #tp-tram{ display:none !important; }

#fs-btn      { bottom:16px  !important; top:auto !important; }
#gps-btn     { bottom:72px  !important; top:auto !important; }
#next90-btn  { bottom:128px !important; top:auto !important; }
#flights-btn { bottom:184px !important; top:auto !important; }
#tp-train    { bottom:240px !important; top:auto !important; }
#tp-intl     { bottom:296px !important; top:auto !important; }
#list-btn    { bottom:352px !important; top:auto !important; }

@media (max-height:760px), (max-width:400px){
  #fs-btn      { bottom:12px  !important; }
  #gps-btn     { bottom:60px  !important; }
  #next90-btn  { bottom:108px !important; }
  #flights-btn { bottom:156px !important; }
  #tp-train    { bottom:204px !important; }
  #tp-intl     { bottom:252px !important; }
  #list-btn    { bottom:300px !important; }
}
"""


def patch_js():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('transport.js: вече е приложено')
        return

    old = """    bus:     { icon:'🚌', title:'Bus arrivals',    gsw:'Aachoendi Büs'  },
    intl:    { icon:'🌍', title:'Intl. coaches',   gsw:'Uslandbüs'      }"""
    new = """    // NO-CITY-BUS — градските отпадат: слезлият в центъра не търси такси
    intl:    { icon:'🌍', title:'Intl. coaches',   gsw:'Uslandbüs'      }"""
    if old not in src:
        print('ГРЕШКА: не намирам списъка с видове')
        sys.exit(1)
    src = src.replace(old, new)

    open(JS, 'w', encoding='utf-8').write(src)
    print('transport.js: градските автобуси са махнати')


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
    print('index.html: колоната е с четири бутона за пристигащи')


if __name__ == '__main__':
    patch_js()
    patch_html()
