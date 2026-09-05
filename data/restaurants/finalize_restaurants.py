import json, html, re

data = json.load(open('restaurants_scraped.json', encoding='utf-8'))

def clean(s):
    if not s:
        return s
    prev = None
    while prev != s:
        prev = s
        s = html.unescape(s)
    s = re.sub(r'^Address:\s*', '', s).strip()
    return s

out = []
omitted = []
for d in data:
    if not d.get('lat'):
        omitted.append(d['name'])
        continue
    out.append({
        'name': clean(d['name']),
        'addr': clean(d['address']),
        'phone': d['phone'].strip(),
        'hours': clean(d['hours']),
        'lat': round(d['lat'], 5),
        'lon': round(d['lon'], 5),
        'url': f"https://justthemenu.ca/index.php?id={d['id']}",
        'src': d['coord_source'],
    })

print('placed:', len(out))
print('omitted (no address on source site):', omitted)

from collections import Counter
print(Counter(o['src'] for o in out))

json.dump(out, open('restaurants.json', 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)

import os
print('restaurants.json', os.path.getsize('restaurants.json'), 'bytes')
