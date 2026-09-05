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

json.dump(out, open('restaurants_final.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

def js(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)

with open('../restaurants_js.txt', 'w', encoding='utf-8') as f:
    f.write('const RESTAURANTS = ' + js(out) + ';')

import os
print('restaurants_js.txt', os.path.getsize('../restaurants_js.txt'), 'bytes')
