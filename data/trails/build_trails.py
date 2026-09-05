import json, math

d = json.load(open('trails_raw.json', encoding='utf-8'))
els = d['elements']

def haversine_km(a, b):
    R = 6371.0
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(h))

def line_length_km(points):
    return sum(haversine_km(points[i], points[i+1]) for i in range(len(points)-1))

HIGHWAY_TYPE = {
    'path': 'Path', 'footway': 'Footpath', 'track': 'Track', 'cycleway': 'Cycling path',
}

trails = []

# Named ways (not part of the TCT relation captured separately below)
tct_way_ids = set()
rel = next((e for e in els if e['type'] == 'relation'), None)
if rel:
    for m in rel.get('members', []):
        tct_way_ids.add(m.get('ref'))

for e in els:
    if e['type'] != 'way':
        continue
    tags = e.get('tags', {})
    name = tags.get('name')
    if not name:
        continue
    geom = e.get('geometry')
    if not geom or len(geom) < 2:
        continue
    pts = [[g['lat'], g['lon']] for g in geom]
    length = line_length_km(pts)
    trails.append({
        'name': name,
        'type': HIGHWAY_TYPE.get(tags.get('highway'), tags.get('highway', 'Trail')),
        'surface': tags.get('surface', ''),
        'length_km': round(length, 2),
        'points': [[round(p[0], 5), round(p[1], 5)] for p in pts],
        'part_of_tct': e['id'] in tct_way_ids,
        'osm_id': e['id'],
    })

print('named way trails:', len(trails))

# Trans Canada Trail relation -- merge all member way geometries into one
# multi-segment feature (241 members).
tct_segments = []
tct_length = 0.0
if rel:
    for m in rel.get('members', []):
        geom = m.get('geometry')
        if not geom or len(geom) < 2:
            continue
        pts = [[round(g['lat'], 5), round(g['lon'], 5)] for g in geom]
        tct_segments.append(pts)
        tct_length += line_length_km([[p[0], p[1]] for p in pts])
    print('Trans Canada Trail: ', len(tct_segments), 'segments,', round(tct_length, 1), 'km total')

out = {
    'trails': trails,
    'tct': {'name': 'Trans Canada Trail (Thunder Bay)', 'segments': tct_segments, 'length_km': round(tct_length, 1)},
}

def js(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)

with open('../trails_js.txt', 'w', encoding='utf-8') as f:
    f.write('const TRAILS_DATA = ' + js(out) + ';')

json.dump(out, open('trails_final.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

import os
print('trails_js.txt', os.path.getsize('../trails_js.txt'), 'bytes')

from collections import Counter
print(Counter(t['type'] for t in trails))
print()
print('longest named trails:')
for t in sorted(trails, key=lambda x: -x['length_km'])[:12]:
    print(f"  {t['length_km']:>6.2f} km  {t['name']} ({t['type']})")
