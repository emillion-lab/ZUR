#!/usr/bin/env python3
"""Показва суровия вид на пристигането, за да се вземе истинската спирка.

Всичките шейсет записа показваха „Sihlquai", но това е стойността по
подразбиране в parse() — истинското име на спирката не се извлича,
защото полето се казва другояче. А FlixBus спира на две места в Цюрих:
Sihlquai и перон R на летището. Второто е важно — там няма таксиметрова
стоянка и слезлите нямат друг вариант.

Вместо да гадая пак, този патч отпечатва първите два записа както идват
от сървъра. От следващия лог се вижда как точно се казват полетата и
поправката става на сигурно.
"""
import sys

PATH = 'scripts/fetch_flixbus.py'
MARK = 'DUMP-SHAPE'


def main():
    src = open(PATH, encoding='utf-8').read()
    if MARK in src:
        print('вече е приложено')
        return

    old = """def parse(d, origin_name):
    \"\"\"Вади часовете на пристигане в Цюрих от отговора на търсенето.\"\"\"
    out = []
    if not d:
        return out"""

    new = """_dumped = [0]


def parse(d, origin_name):
    \"\"\"Вади часовете на пристигане в Цюрих от отговора на търсенето.\"\"\"
    out = []
    if not d:
        return out

    # DUMP-SHAPE — веднъж на пускане показваме как изглежда записът,
    # за да не се гадаят имената на полетата. Маха се, щом се знаят.
    if _dumped[0] < 1:
        try:
            tr0 = (d.get('trips') or [])[0]
            res = tr0.get('results') or {}
            it0 = list(res.values())[0] if isinstance(res, dict) else res[0]
            print('  --- суров запис ---')
            print('  ключове:', sorted(it0.keys()))
            print('  arrival:', json.dumps(it0.get('arrival'), ensure_ascii=False)[:400])
            print('  departure:', json.dumps(it0.get('departure'), ensure_ascii=False)[:250])
            legs = it0.get('legs') or []
            if legs:
                print('  leg[0] ключове:', sorted(legs[0].keys()))
                print('  leg[-1]:', json.dumps(legs[-1], ensure_ascii=False)[:400])
            print('  -------------------')
            _dumped[0] = 1
        except Exception as ex:
            print('  (не мога да покажа записа:', type(ex).__name__, ')')
            _dumped[0] = 1"""

    if old not in src:
        print('ГРЕШКА: не намирам parse()')
        sys.exit(1)

    src = src.replace(old, new)
    open(PATH, 'w', encoding='utf-8').write(src)
    print('добавен еднократен отпечатък на суровия запис')


if __name__ == '__main__':
    main()
