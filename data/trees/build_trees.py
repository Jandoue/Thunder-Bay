"""
Builds the tree inventory dataset from the raw ArcGIS pull.

Rebuild with: cd data/trees && python build_trees.py
Writes trees.json -- the file index.html actually fetches for this layer.
"""
import json

with open('trees_raw.geojson', encoding='utf-8') as f:
    feats = json.load(f)['features']
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
    out.append({
        'lat': round(lat, 5), 'lon': round(lon, 5),
        'common': p.get('COMMON') or None, 'botanical': p.get('BOTANICAL') or None,
        'street': p.get('STREET') or None, 'civic_address': p.get('CIVIC_ADDRESS') or None,
        'overhead': p.get('OVERHEAD') or None, 'unitid': p.get('UNITID') or None,
        'objectid': p.get('OBJECTID'), 'globalid': p.get('GlobalID') or None,
    })

with open('trees.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, separators=(',', ':'), ensure_ascii=False)

import os
print('trees.json:', os.path.getsize('trees.json'), 'bytes,', len(out), 'trees')
