#!/usr/bin/env python3
"""Дава на ZUR визуалния облик на BAK — и денем, и нощем.

Защо предишният опит не сработи: правилата бяха вмъкнати ПРЕДИ
оригиналните `#gps-btn{...}` и `#zone-sidebar{...}`, а при еднаква
специфичност печели последното правило. Затова тук блокът се залепя
най-накрая, точно преди затварящия </style>.

Пренася се:
  · дневната палитра на BAK (по-мек студен фон, по-тъмни акценти)
  · градиентното заглавие в хедъра
  · стъклените кръгли бутони + сияние нощем
  · плаващият стъклен списък със зони над картата
  · лентата, оцветена изрично по тема

Idempotent: маркерът ZUR-BAK-SKIN пази от повторно прилагане.
"""
import sys

HTML = 'index.html'
MARK = '/* ZUR-BAK-SKIN */'

SKIN = MARK + """
/* ══════════════════════════════════════════════════════════════
   Обликът на BAK, пренесен върху ZUR.
   Блокът е нарочно последен — така бие по-ранните правила
   без да се налага !important навсякъде.
   ══════════════════════════════════════════════════════════════ */

/* ── ДЕН: палитрата на BAK, а не суровото бяло ── */
:root{
  --bg:#eef2f8; --surface:#ffffff; --border:#cbd5e6;
  --amber:#d97706; --cyan:#0369a1; --green:#16a34a;
  --red:#dc2626; --orange:#ea580c; --muted:#55657c; --text:#0f1b2d;
  --glass:rgba(255,255,255,.62);
  --glass-edge:rgba(15,27,45,.10);
  --card:0 1px 2px rgba(15,27,45,.08), 0 8px 22px rgba(15,27,45,.07);
  --ring:rgba(3,105,161,.22);
  --title:linear-gradient(100deg,#0369a1,#0891b2 45%,#6366f1);
  --ease:cubic-bezier(.22,1,.36,1);
}
body.theme-night{
  --bg:#080f1c; --surface:#0d1729; --border:#1b2b45;
  --amber:#fbbf24; --cyan:#22d3ee; --green:#34d399;
  --red:#f87171; --orange:#fb923c; --muted:#93a4bd; --text:#e8eef7;
  --glass:rgba(12,22,38,.58);
  --glass-edge:rgba(34,211,238,.20);
  --card:0 2px 8px rgba(0,0,0,.55), 0 0 24px rgba(34,211,238,.09);
  --ring:rgba(34,211,238,.38);
  --title:linear-gradient(100deg,#22d3ee,#38bdf8 45%,#818cf8);
}

/* ── ХЕДЪР: градиентно заглавие вместо плосък цвят ── */
.header{
  background:var(--glass);
  backdrop-filter:saturate(180%) blur(14px);
  -webkit-backdrop-filter:saturate(180%) blur(14px);
  border-bottom:1px solid var(--glass-edge);
}
.header h1{
  font:800 17px/1.15 -apple-system,'Segoe UI',system-ui,sans-serif;
  letter-spacing:.5px;
  background:var(--title); -webkit-background-clip:text; background-clip:text;
  color:transparent; -webkit-text-fill-color:transparent;
}
body.theme-night .header h1{ filter:drop-shadow(0 0 10px rgba(34,211,238,.35)); }
.header p{ font-size:12.5px; letter-spacing:.6px; opacity:.85; }

/* ── КРЪГЛИТЕ БУТОНИ: стъкло, а не плътен цвят ── */
#gps-btn, #fs-btn, #next90-btn, #bakshish-btn{
  width:46px; height:46px; border-radius:50%;
  background:var(--glass);
  border:1.5px solid var(--glass-edge);
  color:var(--text);
  box-shadow:var(--card);
  backdrop-filter:saturate(180%) blur(14px);
  -webkit-backdrop-filter:saturate(180%) blur(14px);
  transition:transform .25s var(--ease), box-shadow .3s var(--ease);
}
#gps-btn:active, #fs-btn:active,
#next90-btn:active, #bakshish-btn:active{ transform:scale(.92); }
body.theme-night #gps-btn, body.theme-night #fs-btn,
body.theme-night #next90-btn, body.theme-night #bakshish-btn{
  background:#12203a; border-color:rgba(34,211,238,.30);
}
#gps-btn.active{ border-color:var(--green); color:var(--green); }
#fs-btn.active, #next90-btn.active{ border-color:var(--cyan); color:var(--cyan); }
body.theme-night #gps-btn.active,
body.theme-night #fs-btn.active,
body.theme-night #next90-btn.active{
  box-shadow:0 2px 8px rgba(0,0,0,.55), 0 0 22px var(--ring);
}
#theme-btn{
  width:30px; height:30px; border-radius:50%;
  background:var(--glass); border:1.5px solid var(--glass-edge);
  color:var(--text); box-shadow:var(--card);
  backdrop-filter:saturate(180%) blur(14px);
  transition:transform .3s var(--ease);
}
#theme-btn:active{ transform:scale(.9) rotate(-25deg); }
body.theme-night #theme-btn{ border-color:var(--cyan); box-shadow:0 0 16px var(--ring); }

/* ── СПИСЪКЪТ СЪС ЗОНИ: плаващо стъкло над картата, както в BAK ── */
#zone-sidebar, #karyk-sidebar{
  position:absolute; left:8px; right:8px; bottom:16px; z-index:1150;
  max-height:33vh; min-height:0;
  overflow-y:auto; overscroll-behavior:contain;
  padding:0 0 6px;
  background:var(--glass);
  border:1px solid var(--glass-edge);
  border-top:1px solid var(--glass-edge);
  border-radius:18px;
  backdrop-filter:saturate(180%) blur(18px);
  -webkit-backdrop-filter:saturate(180%) blur(18px);
  box-shadow:var(--card);
}
#zone-sidebar .sidebar-title, #karyk-sidebar .sidebar-title{
  position:sticky; top:0; z-index:3;
  background:var(--glass);
  backdrop-filter:saturate(180%) blur(18px);
  border-bottom:1px solid var(--glass-edge);
  border-radius:18px 18px 0 0;
  color:var(--muted);
}
.zone-item{ border-bottom:1px solid var(--glass-edge); }
.zone-item:last-child{ border-bottom:none; }
.zone-item:active{ background:rgba(3,105,161,.08); }
body.theme-night .zone-item:active{ background:rgba(34,211,238,.10); }
/* в режим „списък" пак заема целия екран */
body.list-view #zone-sidebar, body.list-view #karyk-sidebar{
  position:static; max-height:none; border-radius:0; bottom:auto;
}

/* ── ЛЕНТАТА: изрично по тема, за да не зависи от реда на правилата ── */
body.theme-day  .ticker-bar{ background:rgba(255,255,255,.72); }
body.theme-day  .tick-item { color:#0f1b2d; }
body.theme-night .ticker-bar{ background:rgba(6,16,28,.72); }
body.theme-night .tick-item { color:#e8eef7; }

/* ── ПАНЕЛИТЕ: същото стъкло ── */
.timeline-panel{
  background:var(--glass);
  backdrop-filter:saturate(180%) blur(14px);
  border-bottom:1px solid var(--glass-edge);
}
#weather-bar{
  background:transparent;
  border-bottom:1px solid var(--glass-edge);
}

/* ── НОЩНА КАРТА: обръщаме само плочките, маркерите остават верни ── */
body.theme-night .leaflet-tile-pane{
  filter:invert(1) hue-rotate(180deg) brightness(.93) contrast(.92) saturate(.75);
}
body.theme-night .leaflet-container{ background:#0a0e14; }

@media (prefers-reduced-motion:reduce){
  #gps-btn, #fs-btn, #next90-btn, #bakshish-btn, #theme-btn{ transition:none; }
}
"""


def main():
    src = open(HTML, encoding='utf-8').read()

    if MARK in src:
        print('обликът вече е приложен')
        return

    # залепя се преди ПОСЛЕДНИЯ </style> — така бие всичко над него
    i = src.rfind('</style>')
    if i < 0:
        print('ГРЕШКА: няма </style> в index.html')
        sys.exit(1)

    src = src[:i] + SKIN + '\n' + src[i:]
    open(HTML, 'w', encoding='utf-8').write(src)
    print('приложен облик на BAK, нов размер:', len(src))


if __name__ == '__main__':
    main()
