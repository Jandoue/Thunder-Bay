import csv, json, math

rows = list(csv.reader(open('heritage.csv', encoding='utf-8-sig')))
data = [r for r in rows[1:] if any(c.strip() for c in r)]

geocoded_list = json.load(open('heritage_geocoded.json', encoding='utf-8'))  # 108 successes, in original row order

# Exact indices (0-based, matching `data`) that failed in the geocoding pass --
# read directly off that run's own printed log, not re-derived by matching
# names (many rows share identical names, e.g. 13 different "Queen Anne
# Revival style house" entries at 13 different addresses, so name-matching
# would silently collapse them onto one coordinate).
FAILED_INDICES = {13, 26, 29, 33, 35, 36, 38, 39, 40, 42, 52, 54, 61, 62, 63,
                   64, 65, 66, 67, 68, 73, 77, 84, 98, 113, 115, 122, 133}

assert len(data) - len(FAILED_INDICES) == len(geocoded_list), \
    (len(data), len(FAILED_INDICES), len(geocoded_list))

geocoded_by_index = {}
j = 0
for i in range(len(data)):
    if i not in FAILED_INDICES:
        geocoded_by_index[i] = geocoded_list[j]
        j += 1
assert j == len(geocoded_list)

# Sanity spot-check: index 0 must be "CN Station" in both.
assert data[0][0] == 'CN Station' == geocoded_list[0]['name']
# index 1 must be Pagoda in both (first row after a success).
assert data[1][0] == 'Pagoda' == geocoded_list[1]['name']

POINT_FIXES = {
    'Black Bay Bridge': (48.4656777, -89.2055147),
    'Waverley Park Lookout': (48.4364573, -89.2238680),
    "Thunder Bay Jail and Thunder Bay Governor's Residence": (48.4521831, -89.1988780),
    'Ross Residence (Sandstone Manor)': (48.3784388, -89.2524802),
    'Thunder Bay Main Lighthouse': (48.4341192, -89.2169096),
    'Centennial Botanical Conservatory ': (48.4763937, -89.1881712),
    'Connaught Square': (48.4370, -89.2270),
}
APPROX_NOTE = {
    'Black Bay Bridge': 'Pinned to Arundel St. (bridge itself not in map data)',
    'Waverley Park Lookout': 'Pinned to Waverley St. (feature itself not in map data)',
    "Thunder Bay Jail and Thunder Bay Governor's Residence": 'Pinned to MacDougall St.',
    'Ross Residence (Sandstone Manor)': 'Pinned to Catherine St.',
    'Thunder Bay Main Lighthouse': 'Pinned to Marina Park (nearest mapped landmark to the breakwater)',
    'Centennial Botanical Conservatory ': 'Pinned to Centennial Park (building itself not in map data)',
    'Connaught Square': 'Pinned to approximate Waverley Park district center',
}
WAVERLEY_ANCHOR = (48.4370, -89.2270)
DISTRICT_STREETS = {"st. patrick's square", 'herbert street'}

# Indices where the geocoder matched a generic ROAD segment (osm class=highway)
# rather than an actual address point -- confirmed via a precision audit
# (checked addresstype/osm_type on every result) and cross-checked against
# OpenStreetMap's raw address data via Overpass: these streets have ZERO
# addr:housenumber points mapped in OSM at all, so no geocoder can do better
# without a different data source. Multiple different house numbers on the
# same street often landed on the exact same coordinate as a result (e.g. 6 of
# the 12 Red River Road entries below all got one identical point) -- jittered
# apart here so they're at least visually distinguishable, and every one is
# flagged in its popup rather than presented as an exact address match.
ROAD_FALLBACK = json.load(open('precision_audit.json', encoding='utf-8'))
ROAD_FALLBACK_INDICES = {int(k) for k, v in ROAD_FALLBACK.items()
                          if v['osm_type'] == 'way' and v['addresstype'] == 'road'}

out = []
unresolved = []
district_i = 0
road_jitter_i = 0
for i, r in enumerate(data):
    name, addr_num, street, cira, status, year_added, bylaw, ownership = r
    street_clean = street.strip()
    lat = lon = None
    approx_note = None
    if i in geocoded_by_index and i in ROAD_FALLBACK_INDICES:
        base_lat, base_lon = geocoded_by_index[i]['lat'], geocoded_by_index[i]['lon']
        angle = road_jitter_i * 2.1
        radius = 0.00025 + (road_jitter_i % 4) * 0.0001
        lat = base_lat + radius * math.cos(angle)
        lon = base_lon + radius * math.sin(angle) / math.cos(math.radians(48.4))
        approx_note = f'Pinned to {street_clean} -- exact civic address not in OpenStreetMap data for this street'
        road_jitter_i += 1
    elif i in geocoded_by_index:
        lat, lon = geocoded_by_index[i]['lat'], geocoded_by_index[i]['lon']
    elif name in POINT_FIXES and i in FAILED_INDICES:
        lat, lon = POINT_FIXES[name]
        approx_note = APPROX_NOTE[name]
    elif street_clean.lower() in DISTRICT_STREETS:
        angle = district_i * 2.4
        radius = 0.00035 + (district_i % 5) * 0.00012
        lat = WAVERLEY_ANCHOR[0] + radius * math.cos(angle)
        lon = WAVERLEY_ANCHOR[1] + radius * math.sin(angle) / math.cos(math.radians(48.4))
        approx_note = 'Pinned near the Waverley Park Heritage Conservation District — exact street not in map data'
        district_i += 1
    else:
        unresolved.append((i, r))
        continue

    addr_display = f"{addr_num.strip()} {street_clean}".strip() if addr_num.strip() != '-' else street_clean
    out.append({
        'name': name.strip(), 'addr': addr_display, 'circa': cira.strip(),
        'status': status.strip(), 'year_added': year_added.strip(),
        'bylaw': bylaw.strip(), 'ownership': ownership.strip(),
        'lat': round(lat, 5), 'lon': round(lon, 5), 'approx': approx_note,
    })

print('placed:', len(out))
print('unresolved (omitted from map):')
for i, r in unresolved:
    print(' ', i, r)

json.dump(out, open('heritage_final.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

def js(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)

with open('../heritage_js.txt', 'w', encoding='utf-8') as f:
    f.write('const HERITAGE = ' + js(out) + ';')

from collections import Counter
print(Counter(r['status'] for r in out))
print('district-approx count:', sum(1 for r in out if r['approx'] and 'District' in r['approx']))
