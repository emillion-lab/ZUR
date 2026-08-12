#!/usr/bin/env python3
"""Свързва таблото с полетите и подрежда колоната наново.

Три неща:
  · flightDetails живее вътре в DOMContentLoaded на app.js — таблото
    не можеше да го достигне. Изнася се в window при всяко зареждане.
  · Трамваят отпада: пътникът, който слиза от трамвая, обикновено
    продължава пеша. Такси взимат тези с багаж — влак, автобус, летище.
  · Колоната се преномерира без трамвая, за да няма дупка.
"""
import sys

APP = 'app.js'
HTML = 'index.html'
MARK = '// ZUR-FLIGHTS-OUT'

CSS_MARK = '/* ZUR-RAIL-V2 */'
CSS = CSS_MARK + """
/* ── Колоната без трамвая: 5 бутона, отдолу нагоре ──
   ⛶ 16 · 📍 72 · ⏱ 128 · ✈️ 184 · 🚂 240 · 🚌 296 · 🌍 352 · 📋 408 */
#tp-tram{ display:none !important; }

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


def patch_app():
    src = open(APP, encoding='utf-8').read()
    if MARK in src:
        print('app.js: полетите вече са изнесени')
        return

    # след всяко зареждане на кеша таблото трябва да види новите данни
    anchor = "      console.log('[SOF] flightDetails populated:', flightDetails.length, 'flights');"
    if anchor not in src:
        print('ГРЕШКА: не намирам мястото след зареждане на полетите')
        sys.exit(1)

    src = src.replace(anchor, anchor + '\n'
        + '      // ZUR-FLIGHTS-OUT — таблото чете оттук\n'
        + '      window.flightDetails = flightDetails;\n'
        + '      if(window.ZURTransportRedraw) window.ZURTransportRedraw();')

    # и при резервния режим, за да не остане празно
    fb = 'function applyFallbackAirport(){\n  airportStatus=\'fallback\';'
    if fb in src:
        src = src.replace(fb, fb + '\n  window.flightDetails = flightDetails;')

    open(APP, 'w', encoding='utf-8').write(src)
    print('app.js: flightDetails е в window')


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
    print('index.html: колоната е без трамвай')


if __name__ == '__main__':
    patch_app()
    patch_html()
