"""
Pulls the City's Wards Feature Layer (the 7 municipal electoral wards)
and writes a compact JSON file.

Source: City of Thunder Bay Open Data Portal, "Wards Feature Layer"
(https://opendata.thunderbay.ca/datasets/c691fd45b6ba46be9e69c24d77bf610d_0).
Based on original township boundaries and electoral boundaries approved
by the Office of the City Clerk. Last updated June 17, 2025.

Only 7 records with modest ring complexity (a few hundred points each),
well under the server's per-request limit and small enough that no
simplification is needed.
"""
import json
import urllib.request
import urllib.parse

BASE = 'https://services5.arcgis.com/h9xShea49ZANgOtx/arcgis/rest/services/Wards_Feature_Layer/FeatureServer/0/query'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'

# The source stores names in ALL CAPS; Python's naive .title() would
# mangle "McIntyre"/"McKellar" into "Mcintyre"/"Mckellar" -- corrected by
# hand for all 7 wards rather than guessed at algorithmically.
NAME_FIX = {
    'WESTFORT': 'Westfort', 'MCINTYRE': 'McIntyre', 'NEEBING': 'Neebing',
    'RED RIVER': 'Red River', 'NORTHWOOD': 'Northwood', 'MCKELLAR': 'McKellar',
    'CURRENT RIVER': 'Current River',
}

params = {'where': '1=1', 'outFields': '*', 'outSR': '4326', 'f': 'geojson'}
url = BASE + '?' + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={'User-Agent': UA})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())

features = data['features']
print(f'{len(features)} features fetched')

with open('wards_raw.geojson', 'w', encoding='utf-8') as f:
    json.dump(data, f)

wards = []
for feat in features:
    p = feat['properties']
    geom = feat['geometry']
    # A polygon can have multiple rings (holes, or disjoint parts); a
    # MultiPolygon would have multiple polygons each with their own rings.
    polygons = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    rings = [[[round(lat, 5), round(lon, 5)] for lon, lat in ring] for poly in polygons for ring in poly]
    raw_name = (p.get('WARD_NAME') or '').strip()
    wards.append({
        'name': NAME_FIX.get(raw_name, raw_name.title()),
        'ward_no': (p.get('WARD_NO') or '').strip(),
        'area_km2': round(p['Shape__Area'] / 1_000_000, 1) if p.get('Shape__Area') else None,
        'rings': rings,
    })
wards.sort(key=lambda w: w['ward_no'])

with open('wards.json', 'w', encoding='utf-8') as f:
    json.dump(wards, f, separators=(',', ':'))

print('wrote wards.json:', len(wards), 'wards')
for w in wards:
    print(' ', w['ward_no'], w['name'], w['area_km2'], 'km2')
