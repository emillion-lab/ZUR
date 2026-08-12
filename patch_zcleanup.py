#!/usr/bin/env python3
"""Изчиства остатъците от махнатите файлове.

lang.js и patch_lang_hook.py отпаднаха (app.js си има вграден GSW
превключвател), но тагът за lang.js остана в index.html и води до 404.
Маха се и излишният затварящ </div> след бутоните, който висеше от
по-стара редакция и разваляше вложеността.
"""
HTML = 'index.html'


def main():
    src = open(HTML, encoding='utf-8').read()
    changed = False

    for tag in ('\n<script src="lang.js"></script>',
                '<script src="lang.js"></script>'):
        if tag in src:
            src = src.replace(tag, '')
            changed = True
            print('махнат тагът за lang.js')
            break

    # излишен затварящ таг след колоната с бутони
    stray = ('<button id="list-btn" title="Zones list" onclick="toggleMapView()">📋</button>\n'
             '\n\n</div>\n')
    if stray in src:
        src = src.replace(stray,
                          '<button id="list-btn" title="Zones list" '
                          'onclick="toggleMapView()">📋</button>\n\n')
        changed = True
        print('махнат излишният </div>')

    if changed:
        open(HTML, 'w', encoding='utf-8').write(src)
    else:
        print('нищо за чистене')


if __name__ == '__main__':
    main()
