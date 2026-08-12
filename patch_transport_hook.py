#!/usr/bin/env python3
"""Закача transport.js към страницата.

Панелът и четирите бутона (влак/трамвай/автобус/международни) се строят
от самия скрипт, затова тук е нужен само един ред в index.html.
"""
import sys

HTML = 'index.html'
TAG = '<script src="transport.js"></script>'


def main():
    src = open(HTML, encoding='utf-8').read()
    if TAG in src:
        print('transport.js вече е закачен')
        return

    # след app.js, за да е сигурно, че основното приложение е вдигнато
    anchor = '<script src="app.js?v='
    i = src.find(anchor)
    if i < 0:
        print('ГРЕШКА: не намирам app.js тага')
        sys.exit(1)
    j = src.find('</script>', i) + len('</script>')

    src = src[:j] + '\n' + TAG + src[j:]
    open(HTML, 'w', encoding='utf-8').write(src)
    print('закачен transport.js')


if __name__ == '__main__':
    main()
