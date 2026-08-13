#!/usr/bin/env python3
"""Мястото на 🎫 в колоната и ограничението до седем събития.

Шест бутона за пристигащи плюс списъка. Билетчето застава най-отгоре,
защото събитията се гледат предварително — човек планира вечерта си,
докато полетите и влаковете се проверяват в движение.
"""
import sys

HTML = 'index.html'
JS = 'transport.js'
CSS_MARK = '/* ZUR-RAIL-V5 */'

CSS = CSS_MARK + """
/* ── Шест бутона за пристигащи, отдолу нагоре ──
   ⛶ 16 · 📍 72 · ⏱ 128 · ✈️ 184 · 🚂 240 · 🚌 296 · 🌍 352 · 🎫 408 · 📋 464 */
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
  #fs-btn, #gps-btn, #next90-btn, #flights-btn,
  #tp-train, #tp-bus, #tp-intl, #tp-events, #list-btn{
    width:42px !important; height:42px !important;
    font-size:19px !important; border-radius:13px !important;
  }
}

/* големите събития се открояват със звезда в златно */
#tp-panel .tp-line{ color:var(--text); }
#tp-panel .tp-row .tp-line:not(:empty){ color:var(--amber); }
"""


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
    print('index.html: колоната е с шест бутона за пристигащи')


def patch_js():
    """Седем събития стигат за една смяна."""
    src = open(JS, encoding='utf-8').read()
    if 'SEVEN-EVENTS' in src:
        print('transport.js: ограничението вече е сложено')
        return

    old = "    body.innerHTML = html.slice ? html : html;"
    # ограничението се прилага там, където се реже списъкът
    old2 = "      if(isPast && open !== 'intl') return;"
    new2 = """      if(isPast && open !== 'intl') return;
      // SEVEN-EVENTS — за събитията седем реда стигат: това е смяна,
      // не програма за седмицата. Останалите само разсейват.
      if(open === 'events' && shown >= 7) return;
      shown++;"""
    if old2 not in src:
        print('ГРЕШКА: не намирам филтъра за миналите')
        sys.exit(1)
    src = src.replace(old2, new2)

    # брояч преди цикъла
    src = src.replace("    var wroteNow = false, wroteLater = false;",
                      "    var wroteNow = false, wroteLater = false, shown = 0;")

    open(JS, 'w', encoding='utf-8').write(src)
    print('transport.js: показваме седем събития')


if __name__ == '__main__':
    patch_html()
    patch_js()
