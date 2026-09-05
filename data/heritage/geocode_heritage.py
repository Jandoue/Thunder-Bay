import csv, json, time, urllib.parse, urllib.request

rows = list(csv.reader(open('heritage.csv', encoding='utf-8-sig')))
header = rows[0]
data = [r for r in rows[1:] if any(c.strip() for c in r)]

UA = 'thunderbay-civic-map-research/1.0 (one-time batch of 136 heritage-register address lookups for a civic map; contact via project repo)'
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
            return float(d[0]['lat']), float(d[0]['lon'])
    except Exception as e:
        print('ERR', q, e)
    return None

results = []
failed = []
for i, r in enumerate(data):
    name, addr_num, street, cira, status, year_added, bylaw, ownership = r
    street = street.strip()
    addr_num = addr_num.strip()
    if addr_num and addr_num != '-':
        # use just the primary number if it's a range like "38-40" or "312-314 "
        num = addr_num.split('-')[0].strip()
        q = f'{num} {street}, Thunder Bay, Ontario, Canada'
    else:
        q = f'{street}, Thunder Bay, Ontario, Canada'
    r_ll = geocode(q)
    if not r_ll and addr_num and addr_num != '-':
        # fallback: drop house number, just the street
        r_ll = geocode(f'{street}, Thunder Bay, Ontario, Canada')
        time.sleep(1.1)
    if r_ll:
        lat, lon = r_ll
        results.append({
            'name': name, 'addr_num': addr_num, 'street': street, 'circa': cira,
            'status': status, 'year_added': year_added, 'bylaw': bylaw, 'ownership': ownership.strip(),
            'lat': lat, 'lon': lon,
        })
        print(i, name, '->', lat, lon)
    else:
        failed.append(r)
        print(i, name, '-> FAILED', q)
    time.sleep(1.1)

json.dump(results, open('heritage_geocoded.json', 'w'), indent=1)
json.dump(failed, open('heritage_failed.json', 'w'), indent=1)
print('done:', len(results), 'geocoded,', len(failed), 'failed')
