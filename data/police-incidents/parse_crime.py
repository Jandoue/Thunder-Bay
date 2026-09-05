import csv, json, glob, re
from collections import Counter, defaultdict

files = sorted(glob.glob('*.csv'))
print(files)

rows = []
for f in files:
    with open(f, encoding='utf-8-sig', newline='') as fh:
        reader = csv.reader(fh)
        header = next(reader)
        for r in reader:
            if len(r) < 10:
                continue
            rows.append(r)

print('total rows', len(rows))
print('header', header)
print(rows[0])

# columns: ccn,date,updateDate,city,state,postalCode,blocksizedAddress,incidentType,parentIncidentType,narrative
def parse_date(s):
    # "07/01/2024, 6:54:37 AM"
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', s)
    if not m:
        return None
    mo, da, yr = m.groups()
    return f'{yr}-{mo}-{da}'

dates = []
fsa_counter = Counter()
category_counter = Counter()
month_counter = Counter()
month_category = defaultdict(Counter)
postal_counter = Counter()
category_by_fsa = defaultdict(Counter)

for r in rows:
    ccn, date, updateDate, city, state, postalCode, blockAddr, incidentType, parentType, narrative = r[:10]
    d = parse_date(date)
    if not d:
        continue
    dates.append(d)
    ym = d[:7]
    month_counter[ym] += 1
    cat = parentType.strip() or 'Unknown'
    category_counter[cat] += 1
    month_category[ym][cat] += 1
    pc = postalCode.strip().replace(' ', '').upper()
    fsa = pc[:3] if len(pc) >= 3 else 'UNK'
    fsa_counter[fsa] += 1
    postal_counter[pc] += 1
    category_by_fsa[fsa][cat] += 1

dates.sort()
print('date range:', dates[0], 'to', dates[-1])
print()
print('=== category counts ===')
for c, n in category_counter.most_common():
    print(f'{n:6d}  {c}')
print()
print('=== FSA counts ===')
for f_, n in fsa_counter.most_common(20):
    print(f'{n:6d}  {f_}')
print()
print('=== monthly counts ===')
for m in sorted(month_counter):
    print(m, month_counter[m])

json.dump({
    'total': len(dates),
    'date_min': dates[0],
    'date_max': dates[-1],
    'category_counts': dict(category_counter),
    'fsa_counts': dict(fsa_counter),
    'month_counts': dict(sorted(month_counter.items())),
    'month_category': {m: dict(c) for m, c in month_category.items()},
    'category_by_fsa': {f_: dict(c) for f_, c in category_by_fsa.items()},
}, open('../crime_summary.json', 'w'), indent=1)
