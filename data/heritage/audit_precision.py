import csv, json, time, urllib.parse, urllib.request

rows = list(csv.reader(open('heritage.csv', encoding='utf-8-sig')))
data = [r for r in rows[1:] if any(c.strip() for c in r)]

UA = 'thunderbay-civic-map-research/1.0 (precision audit of prior geocoding pass; contact via project repo)'
VB = 'viewbox=-89.6,48.55,-88.9,48.05&bounded=1'

def geocode(q):
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({
        'q': q, 'format': 'json', 'limit': 1, 'countrycodes': 'ca'
    }) + '&' + VB
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            d = json.loads(resp.read().decode())
        if d:
            return d[0]
    except Exception as e:
        print('ERR', q, e)
    return None

FAILED_INDICES = {13, 26, 29, 33, 35, 36, 38, 39, 40, 42, 52, 54, 61, 62, 63,
                   64, 65, 66, 67, 68, 73, 77, 84, 98, 113, 115, 122, 133}

results = {}
for i, r in enumerate(data):
    if i in FAILED_INDICES:
        continue
    name, addr_num, street, cira, status, year_added, bylaw, ownership = r
    street = street.strip()
    addr_num = addr_num.strip()
    num = addr_num.split('-')[0].strip()
    q = f'{num} {street}, Thunder Bay, Ontario, Canada'
    res = geocode(q)
    precision = res.get('addresstype') if res else None
    results[i] = {'name': name, 'query': q, 'lat': float(res['lat']) if res else None,
                  'lon': float(res['lon']) if res else None, 'addresstype': precision,
                  'osm_type': res.get('osm_type') if res else None}
    flag = '' if precision == 'house' else '  <-- NOT house-level'
    print(i, name, '|', precision, flag)
    time.sleep(1.1)

json.dump(results, open('precision_audit.json', 'w'), indent=1)
not_house = [v for v in results.values() if v['addresstype'] != 'house']
print()
print(f'{len(not_house)} / {len(results)} are NOT precise house-level matches')
