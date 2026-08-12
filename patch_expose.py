#!/usr/bin/env python3
"""Изважда функциите на app.js навън и маха дублирания превключвател.

Защо нищо не се отваряше: целият app.js е в `DOMContentLoaded`, значи
`map`, `showAirportSchedule` и `showZonePopup` живеят вътре в тази
функция. Всеки inline onclick обаче се изпълнява в глобален обхват —
там тези имена ги няма и браузърът мълчаливо се отказва. Затова нито
редовете в списъка, нито бутонът за полети правеха нещо.

Второ: app.js вече си има GSW превключвател (черното кръгче горе
вдясно). Моят lang.js добави втори и двата се биеха. Остава вграденият,
защото превежда целия текст, а не само няколко надписа.
"""
import re
import sys

APP = 'app.js'
HTML = 'index.html'
MARK = '// ZUR-EXPOSE'

EXPOSE = """
// ZUR-EXPOSE — нужно, защото всичко горе е вътре в DOMContentLoaded,
// а inline onclick се изпълнява в глобален обхват.
window.map                 = map;
window.showAirportSchedule = showAirportSchedule;
window.showZonePopup       = showZonePopup;
window.showTransitPopup    = showTransitPopup;
window.render              = render;
window.computeScores       = computeScores;
window.ZONES               = ZONES;
window.getCurrentHour      = function(){ return currentHour; };
"""


def patch_app():
    src = open(APP, encoding='utf-8').read()

    if MARK not in src:
        anchor = '}); // end DOMContentLoaded'
        if anchor not in src:
            print('ГРЕШКА: не намирам края на DOMContentLoaded')
            sys.exit(1)
        src = src.replace(anchor, EXPOSE + '\n' + anchor, 1)
        print('app.js: функциите са изнесени в window')
    else:
        print('app.js: вече е изнесено')

    # времето вече не разчита на моя lang.js, а на вградения uiLang
    src = src.replace(
        "lang=${(window.ZURLang&&window.ZURLang.get()==='gsw')?'de':'en'}",
        "lang=${(typeof uiLang!=='undefined'&&uiLang==='gsw')?'de':'en'}")

    # ZURMapResize беше извън обхвата на map; сега map е в window
    src = src.replace(
        "window.ZURMapResize = function(){ try{ map.invalidateSize(); }catch(e){} };",
        "window.ZURMapResize = function(){ try{ window.map.invalidateSize(); }catch(e){} };")

    # toggleMapView също посяга към window.map
    src = src.replace(
        "  if(!listView && window.map) setTimeout(()=>map.invalidateSize(), 100);",
        "  if(!listView && window.map) setTimeout(function(){ window.map.invalidateSize(); }, 100);")

    open(APP, 'w', encoding='utf-8').write(src)


def patch_html():
    """Маха lang.js — app.js вече си има превключвател."""
    src = open(HTML, encoding='utf-8').read()
    tag = '<script src="lang.js"></script>'
    if tag in src:
        src = src.replace('\n' + tag, '').replace(tag, '')
        open(HTML, 'w', encoding='utf-8').write(src)
        print('index.html: махнат дублиращият lang.js')
    else:
        print('index.html: lang.js вече не се зарежда')


if __name__ == '__main__':
    patch_app()
    patch_html()
