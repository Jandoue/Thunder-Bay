"""
Pulls the City's Rail Network Feature Layer (CN/CP mainlines, yards,
spurs, sidings, and crossovers within city limits) and writes a compact
JSON file.

Source: City of Thunder Bay Open Data Portal, "Rail Network Feature
Layer" (https://opendata.thunderbay.ca/datasets/93ca79cb85524e92b746e4da1cc4f407_0).
Unlike the bus/street-signs data, the portal's own item description
states this was last updated June 17, 2025 -- recent, not stale.

Single request (1,510 records, under the 2,000-per-request server
limit), requesting WGS84 (outSR=4326) directly so no manual reprojection
is needed.
"""
import json
import urllib.request
import urllib.parse

BASE = 'https://services5.arcgis.com/h9xShea49ZANgOtx/arcgis/rest/services/Rail_Network_Feature_Layer/FeatureServer/0/query'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'

params = {
    'where': '1=1',
    'outFields': '*',
    'outSR': '4326',
    'f': 'geojson',
}
url = BASE + '?' + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={'User-Agent': UA})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())

features = data['features']
print(f'{len(features)} features fetched')

with open('rail_raw.geojson', 'w', encoding='utf-8') as f:
    json.dump(data, f)

tracks = []
for feat in features:
    p = feat['properties']
    geom = feat['geometry']
    # One MultiLineString exists in this feed alongside 1,509
    # LineStrings -- split it into its component parts rather than
    # special-casing a different shape downstream.
    parts = geom['coordinates'] if geom['type'] == 'MultiLineString' else [geom['coordinates']]
    for part in parts:
        tracks.append({
            'name': (p.get('TRACKNAME') or '').strip() or None,
            'class': (p.get('TRACKCLASS') or '').strip() or 'Unknown',
            'owner': (p.get('OWNER') or '').strip() or 'Unknown',
            'operator': (p.get('OPERATOR') or '').strip() or 'Unknown',
            'points': [[round(lat, 5), round(lon, 5)] for lon, lat in part],
        })

from collections import Counter
print('by class:', Counter(t['class'] for t in tracks))
print('by owner:', Counter(t['owner'] for t in tracks))

with open('rail.json', 'w', encoding='utf-8') as f:
    json.dump(tracks, f, separators=(',', ':'))

print('wrote rail.json:', len(tracks), 'track segments')
