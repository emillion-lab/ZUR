#!/usr/bin/env python3
"""Поправя срината карта и българското описание на времето.

1. КАРТАТА. Предишният патч ѝ даде `flex:1`, но `body` в ZUR не е
   flex контейнер (в BAK е — оттам дойде грешката). Резултатът: картата
   се сви до нищо, а с нея спряха и всички изскачащи прозорци, които се
   отварят върху нея — затова „нито един бутон не работеше".
   Тук body става истинска колона и картата вече законно взима остатъка.

2. ВРЕМЕТО. Заявката към OpenWeather носеше `lang=bg`, наследено от
   София. Оттам „ясно небе" върху английски интерфейс. Езикът вече
   следва избора EN/GSW (за швейцарски немски OWM дава немски).
"""
import re
import sys

HTML = 'index.html'
APP = 'app.js'
MARK = '/* ZUR-MAPFIX */'

CSS = MARK + """
/* ── body става колона, за да може картата да заеме остатъка ── */
html{ height:100%; }
body{
  display:flex !important;
  flex-direction:column !important;
  min-height:100dvh !important;
  height:100dvh !important;
  overflow:hidden !important;
}
.header, #weather-bar, .timeline-panel, .ticker-bar{ flex:0 0 auto !important; }
#map{
  flex:1 1 auto !important;
  height:auto !important;
  min-height:180px !important;
  width:100% !important;
}
body.map-fullscreen #map{ flex:1 1 auto !important; height:auto !important; }
body.list-view #map{ display:none !important; }
body.list-view #zone-sidebar{ flex:1 1 auto !important; overflow-y:auto !important; }
"""


def patch_html():
    src = open(HTML, encoding='utf-8').read()
    if MARK in src:
        print('index.html: вече е поправен')
        return
    i = src.rfind('</style>')
    if i < 0:
        print('ГРЕШКА: няма </style>')
        sys.exit(1)
    src = src[:i] + CSS + '\n' + src[i:]
    open(HTML, 'w', encoding='utf-8').write(src)
    print('index.html: body е колона, картата заема остатъка')


def patch_app():
    src = open(APP, encoding='utf-8').read()
    if 'ZURLang' in src and 'lang=bg' not in src:
        print('app.js: езикът на времето вече е оправен')
        return

    old = 'units=metric&lang=bg&appid='
    if old not in src:
        print('app.js: не намирам lang=bg — пропускам')
        return
    # интерфейсът е EN/GSW; за швейцарски немски OWM връща немски
    new = ("units=metric&lang=${(window.ZURLang&&window.ZURLang.get()==='gsw')?'de':'en'}"
           "&appid=")
    src = src.replace(old, new)

    # картата трябва да си премери наново, щом вече е гъвкава
    if 'ZURMapResize' not in src:
        src += ("\n// картата вече е гъвкава по височина — премерва се при въртене\n"
                "window.ZURMapResize = function(){ try{ map.invalidateSize(); }catch(e){} };\n"
                "window.addEventListener('resize', function(){ setTimeout(window.ZURMapResize, 120); });\n"
                "window.addEventListener('orientationchange', function(){ setTimeout(window.ZURMapResize, 300); });\n"
                "setTimeout(window.ZURMapResize, 400);\n")

    open(APP, 'w', encoding='utf-8').write(src)
    print('app.js: времето следва езика, картата се премерва наново')


if __name__ == '__main__':
    patch_html()
    patch_app()
