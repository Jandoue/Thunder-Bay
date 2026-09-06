"""
Pulls the City's Waste Disposal Site Feature Layer and writes a compact
JSON file.

Source: City of Thunder Bay Open Data Portal, "Waste Disposal Site
Feature Layer" (https://opendata.thunderbay.ca/datasets/79093390cfd24528803870eb12818fd8_0).
Solid waste/recycling facilities, recycling depots, and water/sewage
treatment sites -- both active and closed -- traced from Figure 5 of the
2019 Official Plan (older sites cite Figure 6 of the 2002 plan or a CAD
file as their own source). Last updated June 17, 2025 per the portal's
listing.

Only 26 records, well under the server's per-request limit, so no
pagination needed.
"""
import json
import urllib.request
import urllib.parse

BASE = 'https://services5.arcgis.com/h9xShea49ZANgOtx/arcgis/rest/services/Waste_Disposal_Site_Feature_Layer/FeatureServer/0/query'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'

params = {'where': '1=1', 'outFields': '*', 'outSR': '4326', 'f': 'geojson'}
url = BASE + '?' + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={'User-Agent': UA})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())

features = data['features']
print(f'{len(features)} features fetched')

with open('waste_raw.geojson', 'w', encoding='utf-8') as f:
    json.dump(data, f)

sites = []
for feat in features:
    p = feat['properties']
    lon, lat = feat['geometry']['coordinates']
    site_type = (p.get('Site_Type') or '').strip()
    # The source's own Site_Type text says "Closed"/"Active" for most
    # rows; the one that doesn't ("Water Treatment Plant") has no such
    # qualifier at all, so it defaults to active rather than unknown --
    # a water treatment plant not flagged closed is presumably running.
    status = 'closed' if 'closed' in site_type.lower() else 'active'
    sites.append({
        'type': site_type or None,
        'status': status,
        'source': (p.get('Souce') or '').strip() or None,  # 'Souce' is a typo in the City's own field name
        'lat': round(lat, 5), 'lon': round(lon, 5),
    })

from collections import Counter
print('by status:', Counter(s['status'] for s in sites))

with open('waste_sites.json', 'w', encoding='utf-8') as f:
    json.dump(sites, f, separators=(',', ':'))

print('wrote waste_sites.json:', len(sites), 'sites')
