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
        'source': '511',
        'location': c['Location'],
        'roadway': c['Roadway'],
        'direction': c['Direction'],
        'lat': c['Latitude'],
        'lon': c['Longitude'],
        'views': views,
    })

print('cameras with at least one enabled view:', len(out))

# Independent YouTube live streams -- not from an API, hand-curated (and
# hand-verified as actually live, not a one-off recording) in
# youtube_cams.json. Merged in here so index.html only has to fetch one file.
youtube_cams = json.load(open('youtube_cams.json', encoding='utf-8'))
print('youtube live cams:', len(youtube_cams))
out.extend(youtube_cams)

# FAA WeatherCams (weathercams.faa.gov) -- also hand-curated, not pulled from
# an API: the endpoint that reveals which image is current is behind Akamai
# bot-detection, so this links out to the live viewer instead of embedding a
# thumbnail. See data/README.md for why.
airport_cams = json.load(open('airport_cams.json', encoding='utf-8'))
print('airport link-out cams:', len(airport_cams))
out.extend(airport_cams)

json.dump(out, open('cameras.json', 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)

import os
print('cameras.json', os.path.getsize('cameras.json'), 'bytes')
for c in out:
    if c.get('source') == '511':
        tag = f"{len(c['views'])} view(s)"
    elif c.get('source') == 'youtube':
        tag = f"youtube:{c.get('youtube_id')}"
    else:
        tag = f"{len(c.get('directions', []))} direction(s)"
    print(c['id'], c['location'], '|', tag)
