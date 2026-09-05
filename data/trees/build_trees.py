import json, glob

feats = []
for fn in sorted(glob.glob('trees_p*.geojson'), key=lambda s: int(s.split('trees_p')[1].split('.')[0])):
    feats += json.load(open(fn))['features']
print('total trees:', len(feats))

# EXPDATE is empty for all 37,752 records (confirmed on the full pull, not a
# partial one) and TREE_CYCLE is constant ("TREE") for all of them -- both are
# hardcoded in the popup template instead of stored per-record to avoid
# repeating a constant/blank column 37,752 times. Every other field the City's
# viewer requests (STREET, BOTANICAL, COMMON, OVERHEAD, UNITID, CIVIC_ADDRESS,
# GlobalID, OBJECTID) is kept.
out = []
for f in feats:
    lon, lat = f['geometry']['coordinates']
    p = f['properties']
    out.append([
        round(lat, 5), round(lon, 5),
        p.get('COMMON') or '', p.get('BOTANICAL') or '',
        p.get('STREET') or '', p.get('CIVIC_ADDRESS') or '',
        p.get('OVERHEAD') or '', p.get('UNITID') or '',
        p.get('OBJECTID'), p.get('GlobalID') or '',
    ])

def js(obj):
    return json.dumps(obj, separators=(',', ':'))

with open('../trees_js.txt', 'w') as f:
    f.write('const TREES = ' + js(out) + ';')

import os
print('trees_js.txt', os.path.getsize('../trees_js.txt'), 'bytes')
