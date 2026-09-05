"""
Fetches current aircraft positions near Thunder Bay from OpenSky Network's
public API (no key required) and writes a compact JSON snapshot.

Run on a schedule (see .github/workflows/update-flights.yml) rather than
from the browser: OpenSky's API sends
  Access-Control-Allow-Origin: https://opensky-network.org
which blocks direct requests from any other page's JavaScript. Fetching
here (server-side, in a GitHub Actions runner) and publishing the result
as a same-origin JSON file is the workaround.

Also fetches each airborne aircraft's recent flown path via /api/tracks/all,
trimmed to roughly the last 45 minutes so it reads as "where this plane has
been near Thunder Bay," not its entire cross-country track. Anonymous OpenSky
access is capped at 400 request credits/day shared across all endpoints, and
a track lookup costs more than a state-vector lookup, so this is capped to a
handful of aircraft per run (favoring ones likely relevant to YQT) and fails
silently per-aircraft rather than risking the whole run.
"""
import json
import urllib.request
import urllib.error
import datetime

# Local Thunder Bay area (not the wider highway corridor used for cameras) --
# roughly 60-70km around the airport (YQT, 48.3719 N, -89.3239 W).
BBOX = {'lamin': 47.95, 'lomin': -90.05, 'lamax': 48.85, 'lomax': -88.55}

# Ceiling on /tracks/all calls per run, to stay well inside the shared
# anonymous credit budget even if OpenSky prices tracks at their upper range.
MAX_TRACK_FETCHES = 3
TRACK_LOOKBACK_SECONDS = 45 * 60

UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'


def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


url = 'https://opensky-network.org/api/states/all?' + '&'.join(f'{k}={v}' for k, v in BBOX.items())
try:
    raw = fetch_json(url)
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

# Recent flown path for a capped, prioritized subset of airborne aircraft.
# 'low' (likely near YQT) first, then 'cruise' -- 'ground' aircraft aren't
# going anywhere interesting and are skipped to save credits.
priority = {'low': 0, 'cruise': 1, 'ground': 2}
candidates = sorted((a for a in aircraft if a['category'] != 'ground'), key=lambda a: priority[a['category']])

fetched_tracks = 0
for a in candidates:
    if fetched_tracks >= MAX_TRACK_FETCHES:
        break
    try:
        track = fetch_json(f"https://opensky-network.org/api/tracks/all?icao24={a['icao24']}&time=0")
    except urllib.error.HTTPError as e:
        print(f"track fetch skipped for {a['icao24']}: HTTP {e.code}")
        continue
    except Exception as e:
        print(f"track fetch skipped for {a['icao24']}: {e}")
        continue
    fetched_tracks += 1

    points = track.get('path') or []
    if not points:
        continue
    last_t = points[-1][0]
    recent = [p for p in points if p[0] is not None and p[0] >= last_t - TRACK_LOOKBACK_SECONDS]
    if len(recent) > 40:
        stride = len(recent) // 40 + 1
        recent = recent[::stride]
    coords = [[round(p[1], 4), round(p[2], 4)] for p in recent if p[1] is not None and p[2] is not None]
    if len(coords) >= 2:
        a['path'] = coords

print(f'fetched {fetched_tracks} track(s), {sum(1 for a in aircraft if "path" in a)} aircraft got a path')

out = {
    'fetched_at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    'opensky_time': raw.get('time'),
    'bbox': BBOX,
    'aircraft': aircraft,
}

with open('flights_live.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, separators=(',', ':'))

print('wrote flights_live.json:', len(aircraft), 'aircraft')
