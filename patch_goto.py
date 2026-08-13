#!/usr/bin/env python3
"""Изборът на ред в таблото завежда картата до мястото.

Досега редът беше само надпис. В BAK докосването затваря панела и
картата отлита до зоната — това е целият смисъл: видях, че в 07:10
пристига автобус от Мюнхен, докосвам и вече знам къде да съм.

Освен това отпада колоната с перона. За влака перонът значи нещо,
за таксито — нищо; чакащият излиза през едно и също фоайе.
"""
import sys

JS = 'transport.js'
MARK = 'GOTO-ZONE'


def main():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    # ── съответствие спирка → точка на картата ──
    coords = """
  // GOTO-ZONE — къде на картата стои всяка спирка. Летището и гарите
  // съвпадат със зоните на приложението; трамвайните възли са добавени,
  // защото хората слизат там, а зона няма.
  var PLACES = {
    'HB':            [47.3779,  8.5403],
    'Sihlquai':      [47.3800,  8.5350],
    'Sihlquai/HB':   [47.3800,  8.5350],
    'Oerlikon':      [47.4116,  8.5442],
    'Stadelhofen':   [47.3663,  8.5484],
    'Flughafen':     [47.4515,  8.5622],
    'Bahnhofquai':   [47.3771,  8.5419],
    'Central':       [47.3769,  8.5431],
    'Bellevue':      [47.3668,  8.5453],
    'Busbahnhof':    [47.3800,  8.5350]
  };

  // Летищните редове нямат спирка — всички водят до терминала
  var AIRPORT = [47.4515, 8.5622];

  function goTo(place){
    var p = place ? PLACES[place] : null;
    if(!p && open === 'flights') p = AIRPORT;
    if(!p) return;
    close();                      // панелът се маха, за да се вижда картата
    setTimeout(function(){
      try{
        if(document.body.classList.contains('list-view')
           && window.toggleMapView) window.toggleMapView();
        if(window.map){
          window.map.invalidateSize();
          window.map.flyTo(p, 15, {duration: 0.9});
        }
      }catch(e){}
    }, 60);
  }
"""
    src = src.replace('  function render(){', coords + '\n  function render(){', 1)

    # ── редовете стават докосваеми ──
    old_row = """      html += '<div class="tp-row' + (isNow ? ' now' : '') + '">'
            + '<span class="tp-t">' + r.t + late + '</span>'
            + '<span class="tp-line">' + esc(r.cat) + esc(r.line) + '</span>'
            + '<span class="tp-to">' + esc(r.from)
            + '<span class="tp-st">' + esc(r.st) + inTxt + '</span></span>'
            + '<span class="tp-plat">' + esc(r.plat) + '</span>'
            + '</div>';"""
    new_row = """      html += '<div class="tp-row go' + (isNow ? ' now' : '') + '"'
            + ' data-go="' + esc(r.st) + '">'
            + '<span class="tp-t">' + r.t + late + '</span>'
            + '<span class="tp-line">' + esc(r.cat) + esc(r.line) + '</span>'
            + '<span class="tp-to">' + esc(r.from)
            + '<span class="tp-st">' + esc(r.st) + inTxt + '</span></span>'
            + '<span class="tp-go">›</span>'
            + '</div>';"""
    if old_row not in src:
        print('ГРЕШКА: не намирам реда в render')
        sys.exit(1)
    src = src.replace(old_row, new_row)

    # летищните редове също
    src = src.replace(
        """  function flightRow(r, cls){
    return '<div class="tp-row ' + cls + '">'""",
        """  function flightRow(r, cls){
    return '<div class="tp-row go ' + cls + '" data-go="Flughafen">'""")
    src = src.replace(
        """         + '<span class="tp-plat">' + r.plat + '</span>'
         + '</div>';""",
        """         + '<span class="tp-plat">' + r.plat + '</span>'
         + '<span class="tp-go">›</span>'
         + '</div>';""")

    # ── един слушател за целия панел ──
    old_close_bind = "    document.getElementById('tp-close').addEventListener('click', close);"
    new_close_bind = """    document.getElementById('tp-close').addEventListener('click', close);
    document.getElementById('tp-body').addEventListener('click', function(e){
      var row = e.target.closest ? e.target.closest('.tp-row.go') : null;
      if(row) goTo(row.getAttribute('data-go'));
    });"""
    src = src.replace(old_close_bind, new_close_bind)

    # ── перонът отпада, стрелката го замества ──
    src = src.replace(
        "'.tp-plat{font-size:13px;color:var(--muted);min-width:32px;text-align:right}',",
        "'.tp-plat{font-size:13px;color:var(--muted);min-width:32px;text-align:right}',\n"
        "      '.tp-row.go{cursor:pointer}',\n"
        "      '.tp-row.go:active{background:rgba(3,105,161,.10)}',\n"
        "      '.tp-go{color:var(--cyan);font-size:20px;min-width:18px;text-align:right;opacity:.7}',")

    open(JS, 'w', encoding='utf-8').write(src)
    print('редовете завеждат картата; перонът е махнат')


if __name__ == '__main__':
    main()
