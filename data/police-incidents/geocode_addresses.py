import json, time, urllib.parse, urllib.request

top = json.load(open('top_addresses.json'))

UA = 'thunderbay-civic-ledger-research/1.0 (one-time batch of ~70 block-level lookups for a civic transparency map; contact via project repo)'

def clean_addr(a):
    a = a.replace('Block ', '')
    a = a.replace(' HWY', ' Highway').replace('HWY ', 'Highway ')
    return a

def geocode(q):
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({
        'q': q, 'format': 'json', 'limit': 1, 'countrycodes': 'ca'
    })
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data:
            return float(data[0]['lat']), float(data[0]['lon']), data[0].get('display_name','')
    except Exception as e:
        print('ERR', q, e)
    return None

results = []
for i, (fsa, addr, count, cats) in enumerate(top):
    caddr = clean_addr(addr)
    q = f'{caddr}, Thunder Bay, Ontario, Canada'
    r = geocode(q)
    if not r:
        # fallback: drop leading house number, just the street
        street = ' '.join(caddr.split(' ')[1:]) if caddr[0].isdigit() else caddr
        q2 = f'{street}, Thunder Bay, Ontario, Canada'
        r = geocode(q2)
        time.sleep(1.1)
    if r:
        lat, lon, disp = r
        results.append({'fsa': fsa, 'addr': addr, 'count': count, 'categories': cats, 'lat': lat, 'lon': lon})
        print(i, fsa, addr, count, '->', lat, lon)
    else:
        print(i, fsa, addr, count, '-> FAILED')
    time.sleep(1.1)

json.dump(results, open('geocoded_points.json', 'w'), indent=1)
print('done', len(results), '/', len(top))
