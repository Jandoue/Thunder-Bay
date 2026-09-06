"""
Pulls the City's Street Signs Feature Layer (regulatory, warning,
informational, and tourism signs -- everything from stop signs to speed
limits to "hidden driveway" warnings) and writes a compact JSON file.

Source: City of Thunder Bay Open Data Portal, "Street Signs Feature
Layer" (https://opendata.thunderbay.ca/datasets/a505cd484056426b9bd081271d39a80b_0).
The portal's own item description states the underlying data was last
updated February 10, 2020 -- over 5 years stale as of writing, though
sign locations are physical infrastructure that doesn't move nearly as
often as, say, a bus route, so this is disclosed rather than treated as
disqualifying (see root README).

Paginated (22k+ records against a 2000-record-per-request server limit),
requesting WGS84 (outSR=4326) directly so no manual reprojection from the
service's native Web Mercator is needed.
"""
import json
import urllib.request
import urllib.parse
import datetime

BASE = 'https://services5.arcgis.com/h9xShea49ZANgOtx/arcgis/rest/services/Street_Signs_Feature_Layer/FeatureServer/0/query'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'
PAGE_SIZE = 2000


def fetch_page(offset):
    params = {
        'where': '1=1',
        'outFields': '*',
        'outSR': '4326',
        'f': 'geojson',
        'resultOffset': offset,
        'resultRecordCount': PAGE_SIZE,
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

with open('signs_raw.geojson', 'w', encoding='utf-8') as f:
    json.dump({'type': 'FeatureCollection', 'features': features}, f)


def fmt_epoch_ms(ms):
    if not ms:
        return None
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).strftime('%Y-%m-%d')


# UNITTYPE is messy real-world data entry: alongside the three clean
# values (REG/WARN/INFOR) and a smaller TOUR, there's a long tail of
# typos, differently-cased spellouts, and what look like sign-type codes
# accidentally entered into this field instead of SIGNTYPE. Bucketed by a
# lenient 3-letter prefix rather than an exact-match table, so "War",
# "Warning", and "WARN" all land in the same place -- anything that
# doesn't confidently match one of the four clean categories goes to
# 'other' rather than being guessed at.
CATEGORY_PREFIX = {'reg': 'regulatory', 'war': 'warning', 'inf': 'informational', 'tou': 'tourism'}


def categorize(unittype):
    key = (unittype or '').strip().lower()[:3]
    return CATEGORY_PREFIX.get(key, 'other')


signs = []
for feat in features:
    p = feat['properties']
    lon, lat = feat['geometry']['coordinates']
    text = (p.get('SIGNTEXT') or '').strip()
    signs.append({
        'lat': round(lat, 5), 'lon': round(lon, 5),
        'name': (p.get('SIGN_NAME') or '').strip() or None,
        'text': text or None,
        'category': categorize(p.get('UNITTYPE')),
        'type_raw': (p.get('UNITTYPE') or '').strip() or None,
        'code': (p.get('SIGNTYPE') or '').strip() or None,
        'facing': (p.get('FACING') or '').strip() or None,
        'support': (p.get('SUPPTYPE') or '').strip() or None,
        'material': (p.get('SUPPMATL') or '').strip() or None,
        'owner': (p.get('OWN') or '').strip() or None,
        'created': fmt_epoch_ms(p.get('CREATEDDAT')),
        'updated': fmt_epoch_ms(p.get('LASTUPDATE')),
        'objectid': p.get('OBJECTID'),
    })

from collections import Counter
print('by category:', Counter(s['category'] for s in signs))

with open('signs.json', 'w', encoding='utf-8') as f:
    json.dump(signs, f, separators=(',', ':'))

print('wrote signs.json:', len(signs), 'signs')
