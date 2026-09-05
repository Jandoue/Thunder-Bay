"""
Fetches current aircraft positions near Thunder Bay from OpenSky Network's
public API (no key required) and writes a compact JSON snapshot.

Run on a schedule (see .github/workflows/update-flights.yml) rather than
from the browser: OpenSky's API sends
  Access-Control-Allow-Origin: https://opensky-network.org
which blocks direct requests from any other page's JavaScript. Fetching
here (server-side, in a GitHub Actions runner) and publishing the result
as a same-origin JSON file is the workaround.
"""
import json
import urllib.request
import datetime

# Local Thunder Bay area (not the wider highway corridor used for cameras) --
# roughly 60-70km around the airport (YQT, 48.3719 N, -89.3239 W).
BBOX = {'lamin': 47.95, 'lomin': -90.05, 'lamax': 48.85, 'lomax': -88.55}

UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'

url = 'https://opensky-network.org/api/states/all?' + '&'.join(f'{k}={v}' for k, v in BBOX.items())
req = urllib.request.Request(url, headers={'User-Agent': UA})

try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = json.loads(resp.read().decode())
except Exception as e:
    print('FETCH FAILED:', e)
    raise SystemExit(1)

states = raw.get('states') or []
print(f'{len(states)} aircraft in bbox')

# OpenSky state vector field order (per their API docs):
# icao24, callsign, origin_country, time_position, last_contact,
# longitude, latitude, baro_altitude, on_ground, velocity, true_track,
# vertical_rate, sensors, geo_altitude, squawk, spi, position_source
aircraft = []
for s in states:
    lon, lat, baro_alt = s[5], s[6], s[7]
    if lon is None or lat is None:
        continue
    callsign = (s[1] or '').strip()
    on_ground = bool(s[8])
    alt_m = baro_alt if baro_alt is not None else (s[13] or 0)
    if on_ground:
        category = 'ground'
    elif alt_m is not None and alt_m < 3000:
        category = 'low'
    else:
        category = 'cruise'
    aircraft.append({
        'icao24': s[0],
        'callsign': callsign or None,
        'country': s[2],
        'lat': round(lat, 4),
        'lon': round(lon, 4),
        'alt_m': round(alt_m, 0) if alt_m is not None else None,
        'on_ground': on_ground,
        'velocity_ms': round(s[9], 1) if s[9] is not None else None,
        'heading_deg': round(s[10], 1) if s[10] is not None else None,
        'vertical_rate_ms': round(s[11], 1) if s[11] is not None else None,
        'squawk': s[14],
        'category': category,
    })

out = {
    'fetched_at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    'opensky_time': raw.get('time'),
    'bbox': BBOX,
    'aircraft': aircraft,
}

with open('flights_live.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, separators=(',', ':'))

print('wrote flights_live.json:', len(aircraft), 'aircraft')
