#!/usr/bin/env python3
"""Закача lang.js и свързва таблото с превключвателя на езика.

Две неща:
  · зарежда lang.js след transport.js, за да завари бутоните
  · дава на transport.js кука ZURTransportRedraw, та смяната на езика
    да преначертае отвореното табло, без да се презарежда страницата
"""
import sys

HTML = 'index.html'
JS = 'transport.js'
TAG = '<script src="lang.js"></script>'
HOOK = '  window.ZURTransportRedraw = render;'


def patch_html():
    src = open(HTML, encoding='utf-8').read()
    if TAG in src:
        print('lang.js вече е закачен')
        return
    anchor = '<script src="transport.js"></script>'
    if anchor in src:
        src = src.replace(anchor, anchor + '\n' + TAG)
    else:
        j = src.rfind('</body>')
        src = src[:j] + TAG + '\n' + src[j:]
    open(HTML, 'w', encoding='utf-8').write(src)
    print('закачен lang.js')


def patch_js():
    src = open(JS, encoding='utf-8').read()
    if 'ZURTransportRedraw' in src:
        print('куката вече е вътре')
        return
    anchor = '  function init(){\n'
    if anchor not in src:
        print('ГРЕШКА: не намирам init() в transport.js')
        sys.exit(1)
    src = src.replace(anchor, HOOK + '\n\n' + anchor, 1)

    # надписите в таблото минават през речника, ако го има
    src = src.replace(
        "      body.innerHTML = '<div class=\"tp-empty\">Loading…</div>';",
        "      body.innerHTML = '<div class=\"tp-empty\">'\n"
        "        + (window.ZURLang ? window.ZURLang.t('loading') : 'Loading…')\n"
        "        + '</div>';")
    src = src.replace(
        "      body.innerHTML = '<div class=\"tp-empty\">Nothing scheduled right now.</div>';",
        "      body.innerHTML = '<div class=\"tp-empty\">'\n"
        "        + (window.ZURLang ? window.ZURLang.t('nothing') : 'Nothing arriving right now.')\n"
        "        + '</div>';")
    src = src.replace(
        "'<span class=\"tp-st\">from ' + st + '</span>'",
        "'<span class=\"tp-st\">'\n"
        "             + (window.ZURLang ? window.ZURLang.t('from') : 'from')\n"
        "             + ' ' + st + '</span>'")

    # записите вече носят `from` (откъде идва), не `to`
    src = src.replace("+ '<span class=\"tp-to\">' + esc(r.to)",
                      "+ '<span class=\"tp-to\">' + esc(r.from || r.to)")

    # заглавията на четирите вида идват от речника
    src = src.replace(
        "    head.textContent = KINDS[open].icon + ' ' + KINDS[open].title.toUpperCase();",
        "    var lbl = KINDS[open].title;\n"
        "    if(window.ZURLang){\n"
        "      var map = {train:'trains', tram:'trams', bus:'buses', intl:'intl'};\n"
        "      lbl = window.ZURLang.t(map[open]);\n"
        "    }\n"
        "    head.textContent = KINDS[open].icon + ' ' + lbl.toUpperCase();")

    open(JS, 'w', encoding='utf-8').write(src)
    print('transport.js вече говори и на двата езика')


if __name__ == '__main__':
    patch_html()
    patch_js()
