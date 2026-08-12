#!/usr/bin/env python3
"""Международните: без трамваи вътре.

Предишният патч махна филтъра по категория с идеята да не се изпусне
международен автобус, вписан непоследователно. Резултатът беше обратен:
спирка Sihlquai е и трамвайна, затова в таблото се изсипаха T50, T51 и
T17 — градски трамваи, представени като международни автобуси.

Сега се пропускат само истински междуградски категории, а трамваите и
градските линии се отсяват изрично.
"""
import sys

JS = 'transport.js'
MARK = 'INTL-NOTRAM'


def main():
    src = open(JS, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    old = """          if(kind === 'train' && !TRAIN_CAT[cat]) return null;
          if(kind === 'bus' && !BUS_CAT[cat]) return null;
          // при международните не отсяваме: превозвачите ги вписват
          // ту като B, ту като нищо, а един пропуснат ред тук боли повече
          // от един излишен"""

    new = """          if(kind === 'train' && !TRAIN_CAT[cat]) return null;
          if(kind === 'bus' && !BUS_CAT[cat]) return null;
          // INTL-NOTRAM — Sihlquai е и трамвайна спирка. Предишната
          // версия пускаше всичко и таблото се напълни с T50/T51/T17,
          // тоест градски трамваи, обявени за международни автобуси.
          if(kind === 'intl'){
            if(TRAM_CAT[cat]) return null;              // трамвай не е междуградски
            if(!BUS_CAT[cat] && cat !== '') return null;
            var ln = String(e.number || '');
            // градските линии са двуцифрени; международните носят име
            // на превозвача или трицифрен номер
            if(/^\\d{1,2}$/.test(ln)) return null;
          }"""

    if old not in src:
        print('ГРЕШКА: не намирам мястото с филтъра')
        sys.exit(1)
    src = src.replace(old, new)

    # таблицата с трамвайните категории вече трябва да съществува
    if 'var TRAM_CAT' not in src:
        src = src.replace(
            "  var BUS_CAT   = {B:1,BUS:1,NFB:1,TRO:1,NFO:1,KB:1};",
            "  var BUS_CAT   = {B:1,BUS:1,NFB:1,TRO:1,NFO:1,KB:1};\n"
            "  var TRAM_CAT  = {T:1,TRAM:1,NFT:1};")

    open(JS, 'w', encoding='utf-8').write(src)
    print('международните вече не показват трамваи')


if __name__ == '__main__':
    main()
