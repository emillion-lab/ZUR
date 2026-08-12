#!/usr/bin/env python3
"""Разширява времевата скала от 6–24 на 0–24 часа.

Нощните часове (00–06) липсваха напълно, а точно те са важни за такси:
последни влакове, нощни полети, излизане от заведения. MIN_H/MAX_H се
ползват като променливи навсякъде в чертането, затова смяната на един ред
е достатъчна; STEPS расте от 72 на 96, за да остане същата разделителна
способност (4 стъпки на час).

Idempotent: ако е приложено, не прави нищо.
"""
import re
import sys

APP = 'app.js'
HTML = 'index.html'


def patch_app():
    src = open(APP, encoding='utf-8').read()
    if 'MIN_H=0' in src:
        print('app.js: вече е 0–24')
        return False
    old = 'const MIN_H=6, MAX_H=24, STEPS=72;'
    if old not in src:
        print('ГРЕШКА: не намирам реда с MIN_H в app.js')
        sys.exit(1)
    src = src.replace(old, 'const MIN_H=0, MAX_H=24, STEPS=96;')
    open(APP, 'w', encoding='utf-8').write(src)
    print('app.js: скалата е 0–24, STEPS=96')
    return True


def patch_html():
    src = open(HTML, encoding='utf-8').read()
    changed = False

    old_slider = '<input type="range" id="time-slider" min="6" max="24" value="16" step="0.5">'
    new_slider = '<input type="range" id="time-slider" min="0" max="24" value="16" step="0.5">'
    if old_slider in src:
        src = src.replace(old_slider, new_slider)
        changed = True
        print('index.html: плъзгачът тръгва от 0')

    # деленията под плъзгача — на всеки 3 часа, за да се четат на телефон
    old_ticks = ('    <span>6</span><span>8</span><span>10</span><span>12</span><span>14</span>\n'
                 '    <span>16</span><span>18</span><span>20</span><span>22</span><span>24</span>')
    new_ticks = ('    <span>0</span><span>3</span><span>6</span><span>9</span>\n'
                 '    <span>12</span><span>15</span><span>18</span><span>21</span><span>24</span>')
    if old_ticks in src:
        src = src.replace(old_ticks, new_ticks)
        changed = True
        print('index.html: деленията са 0,3,6…24')

    if changed:
        open(HTML, 'w', encoding='utf-8').write(src)
    else:
        print('index.html: вече е поправен')
    return changed


if __name__ == '__main__':
    a = patch_app()
    b = patch_html()
    if not (a or b):
        print('нищо за правене')
