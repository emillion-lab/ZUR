#!/usr/bin/env python3
"""Списъкът да не стои върху картата — както е в BAK.

В BAK картата е чиста; списъкът се вика с бутон 📋 от дясната колона и
заема целия екран. Тук списъкът плуваше постоянно и ядеше половината
карта. Логиката `list-view` вече съществува в app.js (toggleMapView),
затова е достатъчно да се смени кога се показва.

Прави се:
  · #zone-sidebar се скрива, докато body няма клас list-view
  · в дясната колона се добавя бутон 📋, който вика toggleMapView()
  · старият бутон вътре в заглавието на списъка остава да върши работа
    в режим „списък" (за връщане към картата)
"""
import sys

HTML = 'index.html'
MARK = '/* ZUR-LIST-TOGGLE */'

CSS = MARK + """
/* ── Картата е чиста: списъкът идва само при поискване ── */
#zone-sidebar{ display:none !important; }
body.list-view #zone-sidebar{
  display:block !important;
  position:static !important;
  left:auto !important; right:auto !important; bottom:auto !important;
  max-height:none !important;
  border-radius:0 !important;
  border:0 !important; border-top:1px solid var(--glass-edge) !important;
  box-shadow:none !important;
}
body.list-view #map{ display:none !important; }

/* бутонът за списъка застава най-отдолу в колоната; останалите се качват */
#list-btn{
  position:fixed !important; right:12px !important; bottom:16px !important;
  width:48px !important; height:48px !important;
  border-radius:16px !important; padding:0 !important; border:0 !important;
  display:flex !important; align-items:center !important; justify-content:center !important;
  font-size:22px !important; line-height:1 !important;
  color:var(--text) !important;
  background:var(--glass) !important;
  box-shadow:
    0 6px 18px rgba(15,27,45,.20),
    0 1px 0 rgba(255,255,255,.75) inset,
    0 0 0 1px var(--glass-edge) !important;
  backdrop-filter:saturate(180%) blur(16px);
  -webkit-backdrop-filter:saturate(180%) blur(16px);
  z-index:2400 !important; cursor:pointer;
  transition:transform .16s var(--ease);
}
#list-btn:active{ transform:scale(.9) !important; }
body.theme-night #list-btn{
  box-shadow:
    0 6px 20px rgba(0,0,0,.55),
    0 1px 0 rgba(255,255,255,.08) inset,
    0 0 0 1px rgba(34,211,238,.45) !important;
}
body.list-view #list-btn{ color:var(--cyan) !important; }

#fs-btn     { bottom:72px  !important; }
#gps-btn    { bottom:128px !important; }
#next90-btn { bottom:184px !important; }

@media (max-width:400px){
  #list-btn{
    width:42px !important; height:42px !important;
    font-size:19px !important; border-radius:13px !important;
    bottom:14px !important;
  }
  #fs-btn     { bottom:64px  !important; }
  #gps-btn    { bottom:114px !important; }
  #next90-btn { bottom:164px !important; }
}
"""

BTN = ('<button id="list-btn" title="Zones list" '
       'onclick="toggleMapView()">\U0001F4CB</button>\n')


def main():
    src = open(HTML, encoding='utf-8').read()
    if MARK in src:
        print('превключвателят вече е добавен')
        return

    i = src.rfind('</style>')
    if i < 0:
        print('ГРЕШКА: няма </style>')
        sys.exit(1)
    src = src[:i] + CSS + '\n' + src[i:]

    # бутонът застава до другите от колоната
    anchor = '<button id="fs-btn"  title="Fullscreen map">⛶</button>'
    if anchor in src:
        src = src.replace(anchor, anchor + '\n' + BTN)
    else:
        j = src.rfind('</body>')
        src = src[:j] + BTN + src[j:]

    open(HTML, 'w', encoding='utf-8').write(src)
    print('списъкът вече се вика с бутон, картата остава чиста')


if __name__ == '__main__':
    main()
