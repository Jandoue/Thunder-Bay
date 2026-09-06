"""
Pulls the City's Designated Road Right-of-Way Feature Layer and writes a
compact JSON file.

Source: City of Thunder Bay Open Data Portal, "Designated Road Right of
Way Feature Layer" (https://opendata.thunderbay.ca/datasets/ebf7231ba2124034b4ba5e1c28b8a9db_0).
Designated road right-of-way (corridor reservation) widths from the 2019
Transportation Master Plan / 2019 Official Plan, alongside the prior
2002 Official Plan's designation for comparison. Last updated March 11,
2019 -- over 6 years stale as of writing, disclosed in the layer
description rather than presented as current.

The schema's ROAD_CLASS field is entirely empty in this data (checked
directly: all 1,291 records have it null) and is dropped rather than
shown as a field that's always blank.

Only 1,291 records, well under the server's per-request limit, so no
pagination needed.
"""
import json
import re
import urllib.request
import urllib.parse

BASE = 'https://services5.arcgis.com/h9xShea49ZANgOtx/arcgis/rest/services/Designated_Road_ROW_Feature_Layer/FeatureServer/0/query'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'

WIDTH_RE = re.compile(r'^(\d+)\s*m$', re.IGNORECASE)


def normalize_row(value, default):
    v = (value or '').strip()
    if not v:
        return default
    m = WIDTH_RE.match(v)
    if m:
        return f'{m.group(1)} m'
    if v.upper() == 'PROVINCIAL HIGHWAY':
        return 'Provincial Highway'
    if v.upper() == 'LOCAL ROAD':
        return 'Local Road'
    if v.upper() == 'TBD':
        return 'TBD'
    return v.title()


params = {'where': '1=1', 'outFields': '*', 'outSR': '4326', 'f': 'geojson'}
url = BASE + '?' + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={'User-Agent': UA})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())

features = data['features']
print(f'{len(features)} features fetched')

with open('road_row_raw.geojson', 'w', encoding='utf-8') as f:
    json.dump(data, f)

segments = []
for feat in features:
    p = feat['properties']
    segments.append({
        'row_2018': normalize_row(p.get('OP2018_ROW'), 'Not designated'),
        'row_2002': normalize_row(p.get('OP2002_ROW'), 'Not designated'),
        'points': [[round(lat, 5), round(lon, 5)] for lon, lat in feat['geometry']['coordinates']],
    })

from collections import Counter
print('by 2018 ROW:', Counter(s['row_2018'] for s in segments))

with open('road_row.json', 'w', encoding='utf-8') as f:
    json.dump(segments, f, separators=(',', ':'))

print('wrote road_row.json:', len(segments), 'segments')
