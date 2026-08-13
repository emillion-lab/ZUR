#!/usr/bin/env python3
"""Маха дублираната loadEvents.

Функцията се оказа дефинирана два пъти: веднъж от по-ранна сесия, втори
път от моя patch_events_panel.py, който провери за грешен маркер и не
позна, че работата вече е свършена. В JavaScript втората дефиниция
пренаписва първата, затова таблото ползваше моята — а тя не знае за
полетата `began` и `size`, които останалата част от кода очаква.

Тук се маха моята и остава първата, по-пълната.

Кръстен с `z`, за да върви последен по азбучен ред — след всички
патчове, които биха могли да добавят нещо.
"""
import re
import sys

JS = 'transport.js'


def main():
    src = open(JS, encoding='utf-8').read()

    hits = [m.start() for m in re.finditer(r'\n  function loadEvents\(\)\{', src)]
    if len(hits) < 2:
        print('няма дублирана loadEvents (%d срещане)' % len(hits))
        return

    # намираме края на втората дефиниция по броене на скобите
    start = hits[-1] + 1
    i = src.index('{', start)
    depth, j = 0, i
    while j < len(src):
        if src[j] == '{':
            depth += 1
        elif src[j] == '}':
            depth -= 1
            if depth == 0:
                break
        j += 1
    end = j + 1
    while end < len(src) and src[end] in '\n ':
        end += 1

    removed = src[start:end]
    if 'loadEvents' not in removed:
        print('ГРЕШКА: изрязвам грешно място, отказвам се')
        sys.exit(1)

    src = src[:start] + src[end:]

    # ако и помощната crowd() се е удвоила, махаме излишната
    ch = [m.start() for m in re.finditer(r'\n  function crowd\(n\)\{', src)]
    if len(ch) > 1:
        s2 = ch[-1] + 1
        i2 = src.index('{', s2)
        d2, k = 0, i2
        while k < len(src):
            if src[k] == '{':
                d2 += 1
            elif src[k] == '}':
                d2 -= 1
                if d2 == 0:
                    break
            k += 1
        e2 = k + 1
        while e2 < len(src) and src[e2] in '\n ':
            e2 += 1
        src = src[:s2] + src[e2:]
        print('махната и дублираната crowd()')

    open(JS, 'w', encoding='utf-8').write(src)
    print('махната дублираната loadEvents; остава по-пълната')


if __name__ == '__main__':
    main()
