import json

d = json.load(open('cams_511_raw.json', encoding='utf-8'))

# Northwestern Ontario highway corridor around Thunder Bay: roughly
# Ignace/Kashabowie in the west to Nipigon/Terrace Bay in the east,
# covering Highways 11, 17, 61, 527 and 595.
wide = [c for c in d if -91.5 <= c['Longitude'] <= -87.0 and 48.0 <= c['Latitude'] <= 49.7]
print('cameras in scope:', len(wide))

out = []
for c in wide:
    views = [{'url': v['Url'], 'desc': (v.get('Description') or '').strip()}
              for v in c['Views'] if v.get('Status') == 'Enabled']
    if not views:
        continue
    out.append({
        'id': c['Id'],
        'location': c['Location'],
        'roadway': c['Roadway'],
        'direction': c['Direction'],
        'lat': c['Latitude'],
        'lon': c['Longitude'],
        'views': views,
    })

print('cameras with at least one enabled view:', len(out))

json.dump(out, open('cameras.json', 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)

import os
print('cameras.json', os.path.getsize('cameras.json'), 'bytes')
for c in out:
    print(c['id'], c['location'], '|', len(c['views']), 'view(s)')
