import json, math

def perp_dist(pt, a, b):
    (x, y), (ax, ay), (bx, by) = pt, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(x - ax, y - ay)
    t = ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)
    px, py = ax + t * dx, ay + t * dy
    return math.hypot(x - px, y - py)

def rdp(points, eps):
    if len(points) < 3:
        return points
    dmax, idx = 0, 0
    for i in range(1, len(points) - 1):
        d = perp_dist(points[i], points[0], points[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        left = rdp(points[:idx + 1], eps)
        right = rdp(points[idx:], eps)
        return left[:-1] + right
    return [points[0], points[-1]]

# ---- Fire stations (tiny, no simplification needed) ----
stations = json.load(open('fire_stations.geojson'))['features']
station_out = []
for f in stations:
    p = f['properties']
    lon, lat = f['geometry']['coordinates']
    station_out.append({'name': p['NAME'].title(), 'addr': p['Address'].title(), 'lat': round(lat, 5), 'lon': round(lon, 5)})
station_out.sort(key=lambda s: s['name'])
print('stations:', len(station_out))

# ---- Fire zones (simplify polygons) ----
zones = json.load(open('fire_zones.geojson'))['features']
zone_out = []
total_before = total_after = 0
for f in zones:
    p = f['properties']
    geom = f['geometry']
    rings = geom['coordinates'] if geom['type'] == 'Polygon' else geom['coordinates'][0]
    simplified_rings = []
    for ring in rings:
        total_before += len(ring)
        s = rdp(ring, 0.00025)
        total_after += len(s)
        simplified_rings.append([[round(x, 5), round(y, 5)] for x, y in s])
    zone_out.append({
        'area': p['FIRE_AREA'] or '?',
        'station': (p['FIRE_STATION'] or 'Unassigned').title(),
        'rings': simplified_rings,
    })
print(f'zone points: {total_before} -> {total_after}')

# ---- Hydrants (merge pages, full attributes -- matches the field set the
#      City's own ArcGIS viewer requests: BEAT, CREATEDDATE, FDMID, GLOBALID,
#      LASTUPDATE, LOC_ID, NODE_ID, ROT_ANGLE, X_COORD, Y_COORD, OBJECTID) ----
import datetime
def fmt_epoch_ms(ms):
    if not ms:
        return ''
    return datetime.datetime.utcfromtimestamp(ms / 1000).strftime('%Y-%m-%d')

hyd_features = []
for fn in ['hydrants_full_p1.geojson', 'hydrants_full_p2.geojson', 'hydrants_full_p3.geojson']:
    hyd_features += json.load(open(fn))['features']
hyd_out = []
for f in hyd_features:
    lon, lat = f['geometry']['coordinates']
    p = f['properties']
    hyd_out.append({
        'lat': round(lat, 5), 'lon': round(lon, 5),
        'id': p.get('OBJECTID'), 'loc': p.get('LOC_ID') or '', 'fdmid': p.get('FDMID') or '',
        'beat': p.get('BEAT') or '', 'rot': p.get('ROT_ANGLE'), 'node': p.get('NODE_ID') or '',
        'gid': p.get('GLOBALID') or '',
        'x': round(p['X_COORD'], 2) if p.get('X_COORD') is not None else '',
        'y': round(p['Y_COORD'], 2) if p.get('Y_COORD') is not None else '',
        'created': fmt_epoch_ms(p.get('CREATEDDATE')), 'updated': fmt_epoch_ms(p.get('LASTUPDATE')),
    })
print('hydrants:', len(hyd_out))

json.dump({'stations': station_out, 'zones': zone_out, 'hydrants': hyd_out},
          open('layers_bundle.json', 'w'))

# print JS-ready snippets
def js(obj):
    return json.dumps(obj, separators=(',', ':'))

with open('stations_js.txt', 'w') as f:
    f.write('const FIRE_STATIONS = ' + js(station_out) + ';')
with open('zones_js.txt', 'w') as f:
    f.write('const FIRE_ZONES = ' + js(zone_out) + ';')
with open('hydrants_js.txt', 'w') as f:
    f.write('const HYDRANTS = ' + js(hyd_out) + ';')

import os
for fn in ['stations_js.txt', 'zones_js.txt', 'hydrants_js.txt']:
    print(fn, os.path.getsize(fn), 'bytes')
