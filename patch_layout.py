#!/usr/bin/env python3
"""Подрежда дясната колона и оправя изрязаната карта и плътния хедър.

Три неща, които се виждат на екрана:

1. Бутоните се застъпваха. Позициите бяха разпръснати на три места
   (patch_rail, patch_list_toggle, transport.js) и всяко местеше по
   своя сметка. Тук се задават наведнъж, отдолу нагоре, с общ ритъм.

2. Картата беше с `height: calc(100vh - 340px)` — число, което важи
   само при определена височина на шапката. Щом заглавието се пренесе
   на два реда, отдолу оставаше празна лента. Сега картата просто
   заема каквото остане.

3. Хедърът беше плътен. В BAK през него се вижда пейзажът.
"""
import sys

HTML = 'index.html'
MARK = '/* ZUR-LAYOUT-FIX */'

CSS = MARK + """
/* ── КАРТАТА заема остатъка, вместо да се смята на ръка ── */
#map{
  flex:1 1 auto !important;
  height:auto !important;
  min-height:200px !important;
}
body.map-fullscreen #map{ height:100dvh !important; flex:none !important; }
body.list-view #map{ display:none !important; }

/* ── ХЕДЪРЪТ: пейзажът се вижда през него, както в BAK ── */
.header{
  background:linear-gradient(180deg,
    rgba(255,255,255,.42), rgba(255,255,255,.16)) !important;
  backdrop-filter:saturate(170%) blur(12px);
  -webkit-backdrop-filter:saturate(170%) blur(12px);
  border-bottom:1px solid var(--glass-edge) !important;
}
body.theme-night .header{
  background:linear-gradient(180deg,
    rgba(10,16,30,.55), rgba(10,16,30,.22)) !important;
}
/* лентата с времето минава зад шапката, за да няма шев */
#weather-bar{
  margin-top:-1px;
  background:transparent !important;
  border-bottom:1px solid var(--glass-edge) !important;
}
.timeline-panel{
  background:linear-gradient(180deg,
    rgba(255,255,255,.55), rgba(255,255,255,.30)) !important;
  backdrop-filter:saturate(170%) blur(12px);
}
body.theme-night .timeline-panel{
  background:linear-gradient(180deg,
    rgba(10,16,30,.62), rgba(10,16,30,.34)) !important;
}

/* ══ ДЯСНАТА КОЛОНА: една подредба, отдолу нагоре ══
   ⛶ 16 · 📍 72 · ⏱ 128 · ✈️ 184 · 🚂 240 · 🚊 296 · 🚌 352 · 🌍 408 · 📋 464
   Всички са 48px с 8px просвет. Задават се тук, за да не се бият
   правилата от трите места, където се раждат бутоните. */
#fs-btn      { bottom:16px  !important; top:auto !important; }
#gps-btn     { bottom:72px  !important; top:auto !important; }
#next90-btn  { bottom:128px !important; top:auto !important; }
#flights-btn { bottom:184px !important; top:auto !important; }
#tp-train    { bottom:240px !important; top:auto !important; }
#tp-tram     { bottom:296px !important; top:auto !important; }
#tp-bus      { bottom:352px !important; top:auto !important; }
#tp-intl     { bottom:408px !important; top:auto !important; }
#list-btn    { bottom:464px !important; top:auto !important; }

/* самолетът ползва същия калъп като останалите */
#flights-btn{
  position:fixed !important; right:12px !important;
  width:48px !important; height:48px !important;
  border-radius:16px !important; padding:0 !important; border:0 !important;
  display:flex !important; align-items:center !important; justify-content:center !important;
  font-size:22px !important; line-height:1 !important;
  color:var(--text) !important; background:var(--glass) !important;
  box-shadow:
    0 6px 18px rgba(15,27,45,.20),
    0 1px 0 rgba(255,255,255,.75) inset,
    0 0 0 1px var(--glass-edge) !important;
  backdrop-filter:saturate(180%) blur(16px);
  -webkit-backdrop-filter:saturate(180%) blur(16px);
  z-index:2400 !important; cursor:pointer;
  transition:transform .16s ease;
}
#flights-btn:active{ transform:scale(.9) !important; }
body.theme-night #flights-btn{
  box-shadow:
    0 6px 20px rgba(0,0,0,.55),
    0 1px 0 rgba(255,255,255,.08) inset,
    0 0 0 1px rgba(34,211,238,.45) !important;
}
body.list-view #flights-btn{ display:none !important; }

/* по-ниски телефони: 42px и по-стегнат ритъм, за да се съберат деветте */
@media (max-height:760px), (max-width:400px){
  #fs-btn, #gps-btn, #next90-btn, #flights-btn,
  #tp-train, #tp-tram, #tp-bus, #tp-intl, #list-btn{
    width:42px !important; height:42px !important;
    font-size:19px !important; border-radius:13px !important;
  }
  #fs-btn      { bottom:12px  !important; }
  #gps-btn     { bottom:60px  !important; }
  #next90-btn  { bottom:108px !important; }
  #flights-btn { bottom:156px !important; }
  #tp-train    { bottom:204px !important; }
  #tp-tram     { bottom:252px !important; }
  #tp-bus      { bottom:300px !important; }
  #tp-intl     { bottom:348px !important; }
  #list-btn    { bottom:396px !important; }
}
"""

BTN = ('<button id="flights-btn" title="Flight arrivals" '
       'onclick="if(window.showAirportSchedule)showAirportSchedule()">'
       '\u2708\ufe0f</button>\n')


def main():
    src = open(HTML, encoding='utf-8').read()
    if MARK in src:
        print('подредбата вече е приложена')
        return

    i = src.rfind('</style>')
    if i < 0:
        print('ГРЕШКА: няма </style>')
        sys.exit(1)
    src = src[:i] + CSS + '\n' + src[i:]

    if 'id="flights-btn"' not in src:
        anchor = '<button id="fs-btn"  title="Fullscreen map">⛶</button>'
        if anchor in src:
            src = src.replace(anchor, anchor + '\n' + BTN)
        else:
            j = src.rfind('</body>')
            src = src[:j] + BTN + src[j:]
        print('добавен бутон за полети')

    open(HTML, 'w', encoding='utf-8').write(src)
    print('подредена колона, картата запълва екрана, хедърът е прозрачен')


if __name__ == '__main__':
    main()
