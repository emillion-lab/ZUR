# CARTO спря безплатните плочки (28.08.2026) -> OSM, като в BAK. Идемпотентен.
# Нощният филтър (body.theme-night .leaflet-tile-pane) вече е в index.html.
import sys
MARK = 'tile.openstreetmap.org'
s = open('app.js', encoding='utf-8').read()
if MARK in s:
    print('app.js: вече е OSM')
    sys.exit(0)
o = """const map = L.map('map', {center:[47.3900,8.5417], zoom:12, zoomControl:true, attributionControl:false});
L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
  maxZoom:19, subdomains:['a','b','c','d']
}).addTo(map);"""
n = """const map = L.map('map', {center:[47.3900,8.5417], zoom:12, zoomControl:true, attributionControl:true});
// CARTO спря безплатните плочки (28.08.2026) -> OSM като в BAK
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom:19, attribution:'&copy; OpenStreetMap'
}).addTo(map);"""
if s.count(o) != 1:
    sys.exit('app.js: котвата не е намерена (%d)' % s.count(o))
open('app.js', 'w', encoding='utf-8').write(s.replace(o, n))
print('app.js: OSM плочки')
