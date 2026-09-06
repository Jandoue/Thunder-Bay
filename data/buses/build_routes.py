"""
Builds a static reference layer of Thunder Bay Transit route paths, drawn
under the live buses layer so a route's general path is visible even
when no bus currently happens to be on it (e.g. overnight).

Source: the same City open data portal item referenced in
fetch_buses.py's docstring -- the static GTFS feed whose internal file
dates are November 2019 (checked directly), nearly 7 years stale as of
writing. Route *numbers* in it still match the live GTFS-Realtime feed
(checked directly -- every route_id seen in a live pull exists in this
file's routes.txt), so route paths are shown, but this is explicitly a
best-available reference, not a guarantee that every street-level
alignment is still current -- disclosed in the layer's own description
rather than silently trusted. See the root README for the full story.

This is an occasional/manual rebuild (route paths don't change often),
not something run on a schedule like fetch_buses.py.
"""
import csv
import io
import json
import urllib.request
import zipfile
from collections import defaultdict

GTFS_ZIP_URL = 'https://www.arcgis.com/sharing/rest/content/items/ff2f52641c8947cb86f76470a2193752/data'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'

req = urllib.request.Request(GTFS_ZIP_URL, headers={'User-Agent': UA})
with urllib.request.urlopen(req, timeout=30) as resp:
    raw = resp.read()

# Kept for pipeline transparency, same convention as every other layer's
# *_raw file -- not consumed directly by anything.
with open('gtfs_raw.zip', 'wb') as f:
    f.write(raw)

zf = zipfile.ZipFile(io.BytesIO(raw))


def read_csv(name):
    with zf.open(name) as f:
        text = io.TextIOWrapper(f, encoding='utf-8-sig')
        return list(csv.DictReader(text))


trips = read_csv('trips.txt')
shapes = read_csv('shapes.txt')

# One route_id (and a representative headsign) per shape_id -- checked
# directly against this feed that no shape_id maps to more than one
# route_id, so first-trip-wins is safe rather than arbitrary.
shape_route = {}
shape_headsign = {}
for row in trips:
    sid = row['shape_id']
    if sid and sid not in shape_route:
        shape_route[sid] = row['route_id']
        shape_headsign[sid] = row['trip_headsign'] or None

points_by_shape = defaultdict(list)
for row in shapes:
    sid = row['shape_id']
    points_by_shape[sid].append((
        int(row['shape_pt_sequence']),
        round(float(row['shape_pt_lat']), 5),
        round(float(row['shape_pt_lon']), 5),
    ))

routes = defaultdict(list)
skipped = 0
for sid, pts in points_by_shape.items():
    route = shape_route.get(sid)
    if not route:
        # No trip in the feed references this shape (e.g. a retired
        # pattern left behind in shapes.txt) -- nothing to label it with.
        skipped += 1
        continue
    pts.sort(key=lambda p: p[0])
    routes[route].append({
        'headsign': shape_headsign.get(sid),
        'points': [[lat, lon] for _, lat, lon in pts],
    })

print(f'{len(routes)} routes, {sum(len(v) for v in routes.values())} shapes, {skipped} shape(s) with no matching trip')

out = {
    'source_date': '2019-11-08',
    'routes': [{'route': r, 'shapes': s} for r, s in sorted(routes.items())],
}

with open('routes.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, separators=(',', ':'))

print('wrote routes.json:', len(out['routes']), 'routes')
