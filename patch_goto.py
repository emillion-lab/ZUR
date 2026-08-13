#!/usr/bin/env python3
"""Изборът на ред в таблото завежда картата до мястото.

Редът беше само надпис. В BAK докосването затваря панела и картата
отлита до зоната — това е смисълът: видях, че в 07:10 пристига автобус
от Мюнхен, докосвам и вече знам къде да съм.

Отпада и колоната с перона: за влака значи нещо, за таксито — нищо.

Бележка за идемпотентността: маркерът е `function goTo(`, а не
коментарът GOTO-ZONE. По-късен патч (patch_places.py) пренаписва блока
с координатите заедно с коментара, а функцията остава — така проверката
не се самозаблуждава и скриптът не се проваля при второ пускане.
"""
import sys

JS = 'transport.js'


def main():
    src = open(JS, encoding='utf-8').read()

    if 'function goTo(' in src:
        print('вече е приложено')
        return

    coords = """
  // Къде на картата стои всяка спирка. Летището и гарите съвпадат със
  // зоните на приложението; трамвайните възли са добавени, защото хора
  // слизат там, а зона няма. Стойностите се сверяват в patch_places.py.
  var PLACES = {
    'HB':            [47.378036,  8.540377],
    'Sihlquai':      [47.381159,  8.537139],
    'Sihlquai/HB':   [47.381159,  8.537139],
    'Busbahnhof':    [47.381159,  8.537139],
    'Oerlikon':      [47.411487,  8.544181],
    'Stadelhofen':   [47.366588,  8.548439],
    'Flughafen':     [47.450375,  8.562402],
    'Bahnhofquai':   [47.377546,  8.541740],
    'Central':       [47.376526,  8.544372],
    'Bellevue':      [47.367118,  8.545099],
    'Paradeplatz':   [47.369732,  8.538909],
    'Stauffacher':   [47.373592,  8.529596],
    'Enge':          [47.364240,  8.531458]
  };

  var AIRPORT = [47.450375, 8.562402];

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
    if '  function render(){' not in src:
        print('ГРЕШКА: не намирам render()')
        sys.exit(1)
    src = src.replace('  function render(){', coords + '\n  function render(){', 1)

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
    if old_row in src:
        src = src.replace(old_row, new_row)
    else:
        print('   бележка: редът вече е с друг вид, пропускам')

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

    old_bind = "    document.getElementById('tp-close').addEventListener('click', close);"
    new_bind = """    document.getElementById('tp-close').addEventListener('click', close);
    document.getElementById('tp-body').addEventListener('click', function(e){
      var row = e.target.closest ? e.target.closest('.tp-row.go') : null;
      if(row) goTo(row.getAttribute('data-go'));
    });"""
    if old_bind in src and 'tp-row.go' not in src.split('tp-close')[1][:400]:
        src = src.replace(old_bind, new_bind, 1)

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
