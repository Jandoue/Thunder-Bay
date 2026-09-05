import json

d = json.load(open('cams_511.json', encoding='utf-8'))

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

def js(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)

with open('../cameras_js.txt', 'w', encoding='utf-8') as f:
    f.write('const CAMERAS = ' + js(out) + ';')

json.dump(out, open('cameras_final.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

import os
print('cameras_js.txt', os.path.getsize('../cameras_js.txt'), 'bytes')
for c in out:
    print(c['id'], c['location'], '|', len(c['views']), 'view(s)')
