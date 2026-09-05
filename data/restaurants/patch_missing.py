import json, re, base64, urllib.request

data = json.load(open('restaurants_scraped.json', encoding='utf-8'))
UA = 'Mozilla/5.0 (compatible; ThunderBayCivicMapBot/1.0; contact via github.com/Jandoue/Thunder-Bay)'

PAT_HERE_L = re.compile(r'here\.com/l/(-?[\d.]+),(-?[\d.]+),')
PAT_HERE_LATLON = re.compile(r'lat=(-?[\d.]+);lon=(-?[\d.]+)')
PAT_OSM_NODE = re.compile(r'openstreetmap\.org/node/(\d+)')

for d in data:
    if d.get('lat'):
        continue
    url = d.get('maps_url', '')
    if not url:
        print(d['name'], '-- no address at all, will be omitted')
        continue

    m = PAT_HERE_L.search(url)
    if m:
        d['lat'], d['lon'] = float(m.group(1)), float(m.group(2))
        d['coord_source'] = 'here_maps_link'
        print(d['name'], '-> HERE direct', d['lat'], d['lon'])
        continue

    if 'here.com/p/s-' in url:
        b64 = url.split('here.com/p/s-')[1].split('?')[0]
        b64 = b64.replace('&amp;', '&')
        try:
            decoded = base64.b64decode(b64 + '=' * (-len(b64) % 4)).decode()
            m2 = PAT_HERE_LATLON.search(decoded)
            if m2:
                d['lat'], d['lon'] = float(m2.group(1)), float(m2.group(2))
                d['coord_source'] = 'here_maps_b64'
                print(d['name'], '-> HERE b64', d['lat'], d['lon'])
                continue
        except Exception as e:
            print(d['name'], 'HERE b64 decode failed', e)

    m3 = PAT_OSM_NODE.search(url)
    if m3:
        node_id = m3.group(1)
        req = urllib.request.Request(f'https://api.openstreetmap.org/api/0.6/node/{node_id}.json',
                                      headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                j = json.loads(resp.read().decode())
            el = j['elements'][0]
            d['lat'], d['lon'] = el['lat'], el['lon']
            d['coord_source'] = 'osm_node'
            print(d['name'], '-> OSM node', d['lat'], d['lon'])
        except Exception as e:
            print(d['name'], 'OSM node fetch failed', e)
        continue

    print(d['name'], '-- unrecognized maps_url format:', url[:80])

json.dump(data, open('restaurants_scraped.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
have = sum(1 for d in data if d.get('lat'))
print()
print(f'{have} / {len(data)} now have coordinates')
for d in data:
    if not d.get('lat'):
        print(' still missing:', d['name'])
