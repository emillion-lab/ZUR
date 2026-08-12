#!/usr/bin/env python3
"""Колоната избледнява, докато таблото е отворено.

Панелът заема целия екран и покрива бутоните — оставаше само малкото ×
горе вдясно. В BAK при отворен панел бутоните минават най-отгоре и
изсветляват: избраният личи, останалите са едва видими, но всеки от тях
затваря панела с едно докосване.

Затова, докато има отворено табло:
  · колоната се вдига над панела
  · избраният бутон остава четлив, но полупрозрачен
  · останалите избледняват силно и служат за затваряне
"""
import sys

HTML = 'index.html'
JS = 'transport.js'
MARK = '/* ZUR-RAIL-FADE */'

CSS = MARK + """
/* ── докато таблото е отворено, колоната стои над него ── */
body.tp-open #fs-btn, body.tp-open #gps-btn, body.tp-open #next90-btn,
body.tp-open #flights-btn, body.tp-open #tp-train,
body.tp-open #tp-bus, body.tp-open #tp-intl, body.tp-open #list-btn{
  z-index:3400 !important;
}

/* избраният: вижда се, но пропуска панела под себе си */
body.tp-open .tp-btn.on{
  opacity:.72 !important;
  color:var(--cyan) !important;
  box-shadow:0 6px 18px rgba(15,27,45,.18), 0 0 0 2px var(--cyan) !important;
}

/* останалите: едва загатнати, но пак се докосват и затварят */
body.tp-open .tp-btn:not(.on),
body.tp-open #fs-btn, body.tp-open #gps-btn,
body.tp-open #next90-btn, body.tp-open #list-btn{
  opacity:.26 !important;
}
body.tp-open .tp-btn:not(.on):active,
body.tp-open #fs-btn:active, body.tp-open #gps-btn:active,
body.tp-open #next90-btn:active, body.tp-open #list-btn:active{
  opacity:.6 !important;
}

/* панелът пуска малко от картата да се види, за да е ясно къде сме */
body.tp-open #tp-panel{
  background:color-mix(in srgb, var(--bg) 92%, transparent) !important;
}
@supports not (background: color-mix(in srgb, red 50%, blue)){
  body.tp-open #tp-panel{ background:var(--bg) !important; }
}
"""


def patch_html():
    src = open(HTML, encoding='utf-8').read()
    if MARK in src:
        print('index.html: избледняването вече е добавено')
        return
    i = src.rfind('</style>')
    if i < 0:
        print('ГРЕШКА: няма </style>')
        sys.exit(1)
    src = src[:i] + CSS + '\n' + src[i:]
    open(HTML, 'w', encoding='utf-8').write(src)
    print('index.html: колоната избледнява при отворено табло')


def patch_js():
    src = open(JS, encoding='utf-8').read()
    if 'tp-open' in src:
        print('transport.js: класът вече се поставя')
        return

    # при затваряне
    old_close = ("    var p = document.getElementById('tp-panel');\n"
                 "    if(p) p.classList.remove('on');")
    new_close = ("    var p = document.getElementById('tp-panel');\n"
                 "    if(p) p.classList.remove('on');\n"
                 "    document.body.classList.remove('tp-open');")
    if old_close not in src:
        print('ГРЕШКА: не намирам close()')
        sys.exit(1)
    src = src.replace(old_close, new_close)

    # при отваряне
    old_open = "    document.getElementById('tp-panel').classList.add('on');"
    new_open = ("    document.getElementById('tp-panel').classList.add('on');\n"
                "    document.body.classList.add('tp-open');")
    src = src.replace(old_open, new_open)

    # всеки друг бутон от колоната също затваря панела
    anchor = "  window.ZURTransportRedraw = render;"
    extra = """
  // Докато таблото е отворено, останалите бутони служат за затваряне —
  // панелът покрива екрана и иначе трябва да се цели в малкото ×.
  function bindClosers(){
    ['fs-btn','gps-btn','next90-btn','list-btn'].forEach(function(id){
      var b = document.getElementById(id);
      if(!b || b.dataset.tpCloser) return;
      b.dataset.tpCloser = '1';
      b.addEventListener('click', function(e){
        if(open){
          e.preventDefault();
          e.stopImmediatePropagation();
          close();
        }
      }, true);   // capture: изпреварва собственото действие на бутона
    });
  }
"""
    src = src.replace(anchor, extra + '\n' + anchor)
    src = src.replace('    mkButtons();\n    setTimeout(mkButtons, 1500);',
                      '    mkButtons();\n    bindClosers();\n'
                      '    setTimeout(function(){ mkButtons(); bindClosers(); }, 1500);')

    open(JS, 'w', encoding='utf-8').write(src)
    print('transport.js: другите бутони затварят таблото')


if __name__ == '__main__':
    patch_html()
    patch_js()
