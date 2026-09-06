"""
Pulls the City's School Crosswalks Feature Layer and writes a compact
JSON file.

Source: City of Thunder Bay Open Data Portal, "School Crosswalks Feature
Layer" (https://opendata.thunderbay.ca/datasets/32dccd0a21584e11aeaac16a0b831cd5_0).
Same source and vintage as the School Crossing Guards layer -- the
Hansen application and the City's GIS layers, maintained by
Infrastructure and Operations, last updated September 28, 2023.

Only 81 records, well under the server's per-request limit, so no
pagination needed.
"""
import json
import urllib.request
import urllib.parse

BASE = 'https://services5.arcgis.com/h9xShea49ZANgOtx/arcgis/rest/services/School_Crosswalks_Feature_Layer/FeatureServer/0/query'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'

params = {'where': '1=1', 'outFields': '*', 'outSR': '4326', 'f': 'geojson'}
url = BASE + '?' + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={'User-Agent': UA})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())

features = data['features']
print(f'{len(features)} features fetched')

with open('crosswalks_raw.geojson', 'w', encoding='utf-8') as f:
    json.dump(data, f)

crosswalks = []
for feat in features:
    p = feat['properties']
    # Colour is nearly uniform ('WHITE' for all but a handful of blank
    # or differently-cased entries) -- normalized for consistent display,
    # not treated as a meaningful category to color-code by.
    colour = (p.get('Colour') or '').strip()
    crosswalks.append({
        'type': (p.get('Type') or '').strip() or None,
        'colour': colour.title() if colour else None,
        'points': [[round(lat, 5), round(lon, 5)] for lon, lat in feat['geometry']['coordinates']],
    })

with open('crosswalks.json', 'w', encoding='utf-8') as f:
    json.dump(crosswalks, f, separators=(',', ':'))

print('wrote crosswalks.json:', len(crosswalks), 'crosswalks')
