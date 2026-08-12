#!/usr/bin/env python3
"""Дава на ZUR облика на СЕГАШНИЯ BAK — не на стария.

Какво беше сбъркано в предишния опит (patch_skin.py):
  · бутоните бяха кръгли; BAK отдавна ползва заоблени квадрати 48×48
    с радиус 16, подредени в една стъклена колона вдясно
  · списъкът плуваше твърде високо и се застъпваше с колоната
  · КАРЪК режимът е излишен тук и само пречи

Този патч се залепя СЛЕД предишния скин, за да го надвие, вместо да
се редактира старият блок (по-малко местa за грешка).
"""
import sys

HTML = 'index.html'
MARK = '/* ZUR-BAK-RAIL */'

RAIL = MARK + """
/* ══════════════════════════════════════════════════════════════
   Една стъклена колона вдясно — както е в BAK днес.
   Заоблени квадрати, не кръгове; закотвени отдолу, за да не
   изпадат под екрана при по-висока шапка.
   ══════════════════════════════════════════════════════════════ */
#gps-btn, #fs-btn, #next90-btn, #bakshish-btn{
  position:fixed !important; right:12px !important; left:auto !important;
  width:48px !important; height:48px !important;
  min-width:48px !important; max-width:48px !important;
  border-radius:16px !important; padding:0 !important;
  display:flex !important; align-items:center !important; justify-content:center !important;
  font-size:22px !important; line-height:1 !important;
  color:var(--text) !important;
  background:var(--glass) !important;
  border:0 !important;
  box-shadow:
    0 6px 18px rgba(15,27,45,.20),
    0 1px 0 rgba(255,255,255,.75) inset,
    0 0 0 1px var(--glass-edge) !important;
  backdrop-filter:saturate(180%) blur(16px);
  -webkit-backdrop-filter:saturate(180%) blur(16px);
  z-index:2400 !important;
  transition:transform .16s var(--ease), box-shadow .2s var(--ease), opacity .25s var(--ease);
  cursor:pointer;
}
body.theme-night #gps-btn, body.theme-night #fs-btn,
body.theme-night #next90-btn, body.theme-night #bakshish-btn{
  box-shadow:
    0 6px 20px rgba(0,0,0,.55),
    0 1px 0 rgba(255,255,255,.08) inset,
    0 0 0 1px rgba(34,211,238,.45) !important;
}
#gps-btn:active, #fs-btn:active,
#next90-btn:active, #bakshish-btn:active{ transform:scale(.9) !important; }

/* колоната се брои отдолу нагоре, с равен отстъп */
#fs-btn      { bottom:16px  !important; top:auto !important; }
#gps-btn     { bottom:72px  !important; top:auto !important; }
#next90-btn  { bottom:128px !important; top:auto !important; }
#bakshish-btn{ bottom:184px !important; top:auto !important; }

/* активните — само пръстен, без смяна на фона */
#gps-btn.active{
  color:var(--green) !important;
  box-shadow:0 6px 18px rgba(15,27,45,.20), 0 0 0 2px var(--green) !important;
}
#fs-btn.active, #next90-btn.active{
  color:var(--cyan) !important;
  box-shadow:0 6px 18px rgba(15,27,45,.20), 0 0 0 2px var(--cyan) !important;
}

/* по-тесни телефони — колоната се свива, за да не яде картата */
@media (max-width:400px){
  #gps-btn, #fs-btn, #next90-btn, #bakshish-btn{
    width:42px !important; height:42px !important;
    min-width:42px !important; max-width:42px !important;
    font-size:19px !important; border-radius:13px !important;
  }
  #fs-btn      { bottom:14px  !important; }
  #gps-btn     { bottom:64px  !important; }
  #next90-btn  { bottom:114px !important; }
  #bakshish-btn{ bottom:164px !important; }
}

/* ── СПИСЪКЪТ: по-нисък и встрани от колоната ── */
#zone-sidebar{
  left:8px !important;
  right:70px !important;          /* спира преди бутоните */
  bottom:12px !important;
  max-height:30vh !important;
  z-index:1150 !important;
}
body.list-view #zone-sidebar{
  position:static !important; right:auto !important;
  max-height:none !important; border-radius:0 !important;
}

/* ── КАРЪК режимът отпада: не носи нищо тук и само закрива екрана ── */
#karyk-btn, #karyk-banner, #karyk-sidebar{ display:none !important; }

/* ── Бакшиш бутонът остава, но панелът му дублира списъка ── */
#bakshish-panel{ display:none !important; }
#bakshish-btn{ display:none !important; }
"""


def main():
    src = open(HTML, encoding='utf-8').read()
    if MARK in src:
        print('колоната вече е приложена')
        return
    i = src.rfind('</style>')
    if i < 0:
        print('ГРЕШКА: няма </style>')
        sys.exit(1)
    src = src[:i] + RAIL + '\n' + src[i:]
    open(HTML, 'w', encoding='utf-8').write(src)
    print('приложена стъклена колона + махнат КАРЪК')


if __name__ == '__main__':
    main()
