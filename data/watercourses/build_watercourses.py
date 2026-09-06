"""
Pulls the City's Watercourse Feature Layer (streams, rivers, creeks,
lake/pond centrelines, and modeled "virtual flow" drainage paths) and
writes a compact JSON file.

Source: City of Thunder Bay Open Data Portal, "Watercourse Feature
Layer" (https://opendata.thunderbay.ca/datasets/8efe6484b4c740d2874a7ef88c3e4b19_0).
Traced from 2012/2019 aerial photography; last updated 2019. Unlike a
schedule or a sign inventory, a river's course doesn't meaningfully go
"stale" on a similar timescale, so this isn't flagged as a data-quality
concern the way the bus GTFS file or street signs were.

Paginated (2,757 records against a 2,000-per-request server limit),
requesting WGS84 (outSR=4326) directly so no manual reprojection is
needed.
"""
import json
import urllib.request
import urllib.parse

BASE = 'https://services5.arcgis.com/h9xShea49ZANgOtx/arcgis/rest/services/Watercourse_Feature_Layer/FeatureServer/0/query'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'
PAGE_SIZE = 2000

# The source stores names in ALL CAPS; Python's naive .title() would
# mangle "McIntyre"/"McVicar" into "Mcintyre"/"Mcvicar", so the 18
# distinct names here are corrected by hand rather than algorithmically
# -- verified against the source's own distinct-value list, not guessed.
NAME_FIX = {
    'NEEBING RIVER': 'Neebing River',
    'MCINTYRE RIVER': 'McIntyre River',
    'MOSQUITO CREEK': 'Mosquito Creek',
    'MCVICAR CREEK': 'McVicar Creek',
    'CURRENT RIVER': 'Current River',
    'UNKNOWN': None,
    'KAMINISTIQUIA RIVER': 'Kaministiquia River',
    'PENNOCK CREEK': 'Pennock Creek',
    'BOULEVARD LAKE': 'Boulevard Lake',
    'WHISKEYJACK CREEK': 'Whiskeyjack Creek',
    'SHORELINE': None,
    'NORTH BRANCH RIVER': 'North Branch River',
    'NEEBING-MCINTYRE FLOODWAY': 'Neebing-McIntyre Floodway',
    'SAWDUST LAKE': 'Sawdust Lake',
    'MCKELLAR RIVER': 'McKellar River',
    'MISSION RIVER': 'Mission River',
    'HORSESHOE LAKE': 'Horseshoe Lake',
}


def fetch_page(offset):
    params = {
        'where': '1=1', 'outFields': '*', 'outSR': '4326', 'f': 'geojson',
        'resultOffset': offset, 'resultRecordCount': PAGE_SIZE,
    }
    url = BASE + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


features = []
offset = 0
while True:
    page = fetch_page(offset)
    batch = page.get('features', [])
    features += batch
    print(f'fetched {len(batch)} at offset {offset} (total {len(features)})')
    if len(batch) < PAGE_SIZE:
        break
    offset += PAGE_SIZE

with open('watercourses_raw.geojson', 'w', encoding='utf-8') as f:
    json.dump({'type': 'FeatureCollection', 'features': features}, f)

watercourses = []
for feat in features:
    p = feat['properties']
    geom = feat['geometry']
    # A handful of MultiLineStrings alongside mostly-LineStrings -- split
    # into their component parts rather than special-casing downstream.
    parts = geom['coordinates'] if geom['type'] == 'MultiLineString' else [geom['coordinates']]
    raw_name = (p.get('Name') or '').strip()
    name = NAME_FIX.get(raw_name, raw_name.title() if raw_name else None)
    for part in parts:
        watercourses.append({
            'name': name,
            'type': (p.get('TYPE') or '').strip() or 'Unknown',
            'points': [[round(lat, 5), round(lon, 5)] for lon, lat in part],
        })

from collections import Counter
print('by type:', Counter(w['type'] for w in watercourses))

with open('watercourses.json', 'w', encoding='utf-8') as f:
    json.dump(watercourses, f, separators=(',', ':'))

print('wrote watercourses.json:', len(watercourses), 'segments')
