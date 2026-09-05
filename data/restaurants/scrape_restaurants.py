import json, re, time, urllib.request, urllib.error

restaurants = json.load(open('restaurant_list.json', encoding='utf-8'))
print('total restaurants:', len(restaurants))

UA_SITE = 'Mozilla/5.0 (compatible; ThunderBayCivicMapBot/1.0; contact via github.com/Jandoue/Thunder-Bay)'

def fetch(url, headers=None, redirect=True):
    req = urllib.request.Request(url, headers=headers or {'User-Agent': UA_SITE})
    try:
        opener = urllib.request.build_opener()
        if not redirect:
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *a, **k):
                    return None
            opener = urllib.request.build_opener(NoRedirect)
        with opener.open(req, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='replace'), resp.status, dict(resp.headers)
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            return None, e.code, dict(e.headers)
        return None, e.code, {}
    except Exception as e:
        print('  ERR', url, e)
        return None, None, {}

PAT_HOURS = re.compile(r"Hours:\s*(.*?)<br", re.S)
PAT_PHONE = re.compile(r"Telephone:\s*<a href = 'tel:([^']+)'")
PAT_ADDR_TEXT = re.compile(r"Address:\s*<a href = '([^']+)'>([^<]*)</a>")
PAT_ADDR_PLAIN = re.compile(r"Address:\s*([^<]*)<br")
PAT_LATLNG = re.compile(r'!3d(-?[\d.]+)!4d(-?[\d.]+)')
PAT_ATPOS = re.compile(r'/@(-?[\d.]+),(-?[\d.]+),')

results = []
for i, r in enumerate(restaurants):
    rid = r['id']
    html, status, _ = fetch(f'https://justthemenu.ca/index.php?id={rid}')
    if not html:
        print(i, r['name'], '-> PAGE FETCH FAILED', status)
        results.append({**r, 'error': 'page_fetch_failed'})
        time.sleep(0.4)
        continue

    hours_m = PAT_HOURS.search(html)
    phone_m = PAT_PHONE.search(html)
    addr_link_m = PAT_ADDR_TEXT.search(html)
    addr_plain_m = PAT_ADDR_PLAIN.search(html) if not addr_link_m else None

    hours = hours_m.group(1).strip() if hours_m else ''
    phone = phone_m.group(1).strip() if phone_m else ''
    maps_url = addr_link_m.group(1).strip() if addr_link_m else ''
    addr_text = (addr_link_m.group(2).strip() if addr_link_m
                 else (addr_plain_m.group(1).strip() if addr_plain_m else ''))

    lat = lon = None
    coord_source = None

    if maps_url and maps_url.startswith('http'):
        _, status2, headers2 = fetch(maps_url, redirect=False)
        location = headers2.get('Location', '') if headers2 else ''
        if location:
            m = PAT_LATLNG.search(location)
            if not m:
                m = PAT_ATPOS.search(location)
            if m:
                lat, lon = float(m.group(1)), float(m.group(2))
                coord_source = 'google_maps_link'
        time.sleep(0.15)

    results.append({
        'name': r['name'], 'id': rid, 'hours': hours, 'phone': phone,
        'address': addr_text, 'maps_url': maps_url,
        'lat': lat, 'lon': lon, 'coord_source': coord_source,
    })
    print(i, r['name'], '->', lat, lon, coord_source or 'NEEDS FALLBACK', '|', addr_text[:50])
    time.sleep(0.35)

json.dump(results, open('restaurants_scraped.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
have_coord = sum(1 for r in results if r.get('lat'))
print()
print(f'{have_coord} / {len(results)} have coordinates from Google Maps links')
