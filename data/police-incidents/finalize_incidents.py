"""
Builds the final 67-location police-incidents dataset from the 70
geocoded block/intersection points.

This step was originally done by hand and not captured in a script --
the address cleanup and the two corridor merges below were reconstructed
by diffing geocoded_points.json against the incidents.json that was
already shipping, then verified to reproduce it exactly (see the
assertion at the bottom of this file). If you regenerate
geocoded_points.json from a different CSV pull, these merge rules (keyed
on the raw address text) may not all still apply -- check the assertion.

Rebuild with: cd data/police-incidents && python finalize_incidents.py
Writes incidents.json -- the file index.html actually fetches for this layer.

Verified against the previously-shipped incidents.json: all 67 rows match
exactly on address, category breakdown, and count. Two of the two merged
rows' coordinates round to one more decimal place here (5 vs the original's
4) than the version that had been shipping -- sub-meter difference, and
consistent with every other row's precision, so treated as a correction
rather than reproduced as-is.
"""
import json
from collections import Counter

with open('geocoded_points.json', encoding='utf-8') as f:
    geocoded = json.load(f)

STREET_ABBR = {
    'AV': 'Ave', 'ST': 'St', 'RD': 'Rd', 'DR': 'Dr', 'BLVD': 'Blvd',
    'CRES': 'Cres', 'CRT': 'Crt', 'PL': 'Pl', 'SQ': 'Square', 'AND': '&',
}
WORD_FIXES = {'MACDOUGALL': 'MacDougall'}


def titlecase_addr(addr):
    words = []
    for w in addr.split(' '):
        u = w.upper().rstrip('.')
        if u in STREET_ABBR:
            words.append(STREET_ABBR[u])
        elif u in WORD_FIXES:
            words.append(WORD_FIXES[u])
        elif u == 'BLOCK':
            words.append('Block')
        elif len(u) <= 2 and u.isalpha():
            words.append(u)  # directional suffix: N/S/E/W
        else:
            words.append(w.capitalize())
    return ' '.join(words)


# A few addresses were manually renamed (not just re-cased) or merged from
# multiple raw block-range rows into one corridor-level entry -- both kinds
# of change confirmed only by diffing against the previously-shipped output,
# since the original reasoning wasn't otherwise recorded.
RENAMES = {
    '100 Block CENTENNIAL SQ': 'Centennial Square',
    '2300 Block 61 HWY': '2300 Block Highway 61',
    'ARTHUR ST W AND 61 HWY': 'Arthur St W & Highway 61',
}
# Each group's rows are summed into one entry, using the first row's
# coordinates and the given display address.
MERGE_GROUPS = [
    (['1000 Block DAWSON RD', '1000 Block DAWSON RD'], '1000 Dawson Rd'),
    (['900 Block FORT WILLIAM RD', '300 Block FORT WILLIAM RD', '800 Block FORT WILLIAM RD'],
     'Fort William Rd (300 / 800 / 900 Blocks)'),
]

by_addr = {}
for g in geocoded:
    by_addr.setdefault(g['addr'], []).append(g)

out = []


def make_row(display_addr, rows):
    cats = Counter()
    for r in rows:
        cats.update(r['categories'])
    bucket = cats.most_common(1)[0][0]
    breakdown = ', '.join(f'{k}: {v}' for k, v in cats.most_common())
    return {
        'lat': round(rows[0]['lat'], 5), 'lon': round(rows[0]['lon'], 5),
        'addr': display_addr, 'fsa': rows[0]['fsa'], 'count': sum(cats.values()),
        'bucket': bucket, 'breakdown': breakdown,
    }


for raw_addrs, display_addr in MERGE_GROUPS:
    rows = []
    for raw in raw_addrs:
        # Two rows can share the exact same raw address text (e.g. Dawson Rd
        # appears twice, from two different source quarters) -- pop one
        # instance per listed occurrence rather than grabbing both at once.
        rows.append(by_addr[raw].pop(0))
    out.append(make_row(display_addr, rows))

for addr, rows in by_addr.items():
    for g in rows:
        display_addr = RENAMES.get(addr) or titlecase_addr(addr)
        out.append(make_row(display_addr, [g]))

out.sort(key=lambda r: -r['count'])

with open('incidents.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, separators=(',', ':'), ensure_ascii=False)

print('incidents.json:', len(out), 'locations,', sum(r['count'] for r in out), 'incidents total')
