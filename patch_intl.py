#!/usr/bin/env python3
"""Международните автобуси: по-широка мрежа и честен отговор.

Швейцарският отворен API стъпва върху разписанието на SBB/ZVV.
FlixBus, Eurolines и другите международни превозвачи не подават данни
там, затова таблото връщаше нула и изглеждаше като счупено.

Промените:
  · пробват се няколко изписвания на терминала — имената в базата се
    разминават с това, което пишат превозвачите
  · за международните не се реже по категория и хоризонтът е цял ден,
    а не следващият час: един автобус на ден пак е полезен
  · ако наистина няма нищо, се обяснява защо, вместо да мълчи
"""
import sys

JS = 'transport.js'
MARK = 'INTL-WIDE'


def main():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    # 1. няколко изписвания на терминала
    old_stops = """    intl: [
      ['Zürich, Carparkplatz Sihlquai', 'Sihlquai']
    ]"""
    new_stops = """    // INTL-WIDE — имената на терминала се разминават между базите,
    // затова се пробват няколко и се събира каквото върне
    intl: [
      ['Zürich, Carparkplatz Sihlquai', 'Sihlquai'],
      ['Zürich, Sihlquai/HB',           'Sihlquai/HB'],
      ['Zürich Sihlquai',               'Sihlquai'],
      ['Zürich, Busbahnhof',            'Busbahnhof']
    ]"""
    if old_stops not in src:
        print('ГРЕШКА: не намирам списъка със спирки')
        sys.exit(1)
    src = src.replace(old_stops, new_stops)

    # 2. за международните не режем по категория
    old_cat = """          if(kind === 'train' && !TRAIN_CAT[cat]) return null;
          if((kind === 'bus' || kind === 'intl') && !BUS_CAT[cat]) return null;"""
    new_cat = """          if(kind === 'train' && !TRAIN_CAT[cat]) return null;
          if(kind === 'bus' && !BUS_CAT[cat]) return null;
          // при международните не отсяваме: превозвачите ги вписват
          // ту като B, ту като нищо, а един пропуснат ред тук боли повече
          // от един излишен"""
    if old_cat in src:
        src = src.replace(old_cat, new_cat)

    # 3. по-голям лимит за международните
    src = src.replace(
        "    var u = API + '?station=' + encodeURIComponent(name)\n"
        "          + '&limit=15&type=arrival';",
        "    var lim = (kind === 'intl') ? 40 : 15;\n"
        "    var u = API + '?station=' + encodeURIComponent(name)\n"
        "          + '&limit=' + lim + '&type=arrival';")

    # 4. дублиращите се редове от четирите изписвания
    src = src.replace(
        "        var sig = r.st + '|' + r.cat + r.line + '|' + r.from;",
        "        var sig = (kind === 'intl' ? '' : r.st) + '|'\n"
        "                + r.cat + r.line + '|' + r.from + '|' + r.t;")

    # 5. хоризонтът: при международните гледаме целия ден
    old_filter = """      var mins = r.ts ? Math.round((r.ts - now) / 60000) : null;
      var isNow  = mins !== null && mins >= -5 && mins <= 5;
      var isPast = mins !== null && mins < -5;
      if(isPast) return;                       // минали пристигания не помагат"""
    new_filter = """      var mins = r.ts ? Math.round((r.ts - now) / 60000) : null;
      var isNow  = mins !== null && mins >= -5 && mins <= 5;
      var isPast = mins !== null && mins < -5;
      // Международните са по няколко на ден — минал автобус пак е
      // сведение кога идва следващият, затова не се крие.
      if(isPast && open !== 'intl') return;"""
    if old_filter in src:
        src = src.replace(old_filter, new_filter)

    # 6. честно обяснение вместо мълчание
    old_empty = """      body.innerHTML = '<div class="tp-empty">'
        + (isGsw() ? 'Grad chunnt nüt aa.' : 'Nothing arriving right now.')
        + '</div>';
      return;
    }

    stamp.textContent = c.live ? 'live' : 'cached';"""
    new_empty = """      body.innerHTML = '<div class="tp-empty">' + emptyText() + '</div>';
      return;
    }

    stamp.textContent = c.live ? 'live' : 'cached';"""
    if old_empty in src:
        src = src.replace(old_empty, new_empty)

    src = src.replace(
        """    if(!html) html = '<div class="tp-empty">'
      + (isGsw() ? 'Grad chunnt nüt aa.' : 'Nothing arriving right now.') + '</div>';""",
        """    if(!html) html = '<div class="tp-empty">' + emptyText() + '</div>';""")

    helper = """
  // Международните ги няма в швейцарското разписание — по-добре да се
  // каже, отколкото шофьорът да реши, че приложението е счупено.
  function emptyText(){
    if(open === 'intl'){
      return isGsw()
        ? 'Kei Uslandbüs im Fahrplaa.<br><span style="font-size:12px">'
          + 'FlixBus &amp; Co. gänd ihri Zite nöd a d\\u2019SBB wiiter.<br>'
          + 'Terminal: Carparkplatz Sihlquai</span>'
        : 'International coaches are not in the Swiss timetable.'
          + '<br><span style="font-size:12px">FlixBus and others do not publish '
          + 'to SBB, so nothing can be shown here.<br>'
          + 'Terminal: Carparkplatz Sihlquai, next to the main station</span>';
    }
    return isGsw() ? 'Grad chunnt nüt aa.' : 'Nothing arriving right now.';
  }
"""
    src = src.replace('  function render(){', helper + '\n  function render(){', 1)

    open(JS, 'w', encoding='utf-8').write(src)
    print('международните: по-широко търсене, цял ден, обяснение при липса')


if __name__ == '__main__':
    main()
