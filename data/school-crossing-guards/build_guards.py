"""
Pulls the City's School Crossing Guard Hut Locations layer and writes a
compact JSON file.

Source: City of Thunder Bay Open Data Portal, "School Crossing Guard Hut
Locations" (https://opendata.thunderbay.ca/maps/26c6df3aa2cd4c29835445e655589006),
maintained by the Infrastructure and Operations Department. The portal's
item description states this was last updated September 28, 2023.

Only 44 records, well under the server's per-request limit, so no
pagination needed. 5 hut numbers appear twice at slightly different
coordinates (two crossing points at the same intersection/guard) --
kept as separate records rather than deduplicated, since each is a real,
distinct point, not a data-entry accident (checked the coordinates
directly: they're close but not identical).
"""
import json
import urllib.request
import urllib.parse

BASE = 'https://services5.arcgis.com/h9xShea49ZANgOtx/arcgis/rest/services/School_Crossing_Guard_Hut_Locations/FeatureServer/0/query'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'

params = {'where': '1=1', 'outFields': '*', 'outSR': '4326', 'f': 'geojson'}
url = BASE + '?' + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={'User-Agent': UA})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())

features = data['features']
print(f'{len(features)} features fetched')

with open('guards_raw.geojson', 'w', encoding='utf-8') as f:
    json.dump(data, f)

guards = []
for feat in features:
    p = feat['properties']
    lon, lat = feat['geometry']['coordinates']
    guards.append({
        'hut': p.get('HUT_NO'),
        'landmark': (p.get('LANDMARKS') or '').strip() or None,
        'intersection': (p.get('Intersect_') or '').strip() or None,
        'lat': round(lat, 5), 'lon': round(lon, 5),
    })
guards.sort(key=lambda g: (g['hut'] is None, g['hut']))

with open('guards.json', 'w', encoding='utf-8') as f:
    json.dump(guards, f, separators=(',', ':'))

print('wrote guards.json:', len(guards), 'crossing guard points')
