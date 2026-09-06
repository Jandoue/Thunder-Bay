"""
Fetches current Thunder Bay Transit bus positions from the City's public
GTFS-Realtime Vehicle Positions feed and writes a compact JSON snapshot.

Run on a schedule (see .github/workflows/update-buses.yml) rather than
from the browser, same reason as the flights/ships layers: fetching
server-side sidesteps any CORS restriction a browser fetch might hit.
The feed is published by NextLift (Thunder Bay Transit's AVL vendor) --
discovered via the City's open data portal
(https://opendata.thunderbay.ca), which links to this and two sibling
GTFS-RT feeds (trip updates, service alerts) that aren't used here since
neither is meaningfully mappable (trip updates are per-stop arrival
predictions, alerts are text advisories -- see README for why only
vehicle positions made the cut).

Deliberately NOT using the static route/stop/shapes GTFS file also on
that portal: it's a schedule snapshot from November 2019, and while the
route *numbers* still match this live feed (checked directly), the actual
street-level route paths and stop list can't be trusted to still be
current. Route coloring here is derived from the route number itself
(see ROUTE_COLOR in index.html) rather than pulling in that stale file.
"""
import json
import urllib.request
import datetime
from google.transit import gtfs_realtime_pb2

FEED_URL = 'http://api.nextlift.ca/gtfs-realtime/vehicleupdates.pb'
UA = 'thunderbay-civic-map/1.0 (github.com/Jandoue/Thunder-Bay)'

# Below this speed (m/s), the feed's reported bearing is noise -- checked
# directly against a live pull: every vehicle under ~2 m/s reported
# bearing exactly 0.0 regardless of which way it was actually facing,
# while every faster one reported a real, plausible heading. Treated as
# unknown rather than shown as due-north.
MIN_SPEED_FOR_BEARING = 2.0

STATUS_LABEL = {0: 'incoming', 1: 'stopped', 2: 'in_transit'}

req = urllib.request.Request(FEED_URL, headers={'User-Agent': UA})
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
except Exception as e:
    print('FETCH FAILED:', e)
    raise SystemExit(1)

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(raw)
print(f'{len(feed.entity)} vehicles in feed')

buses = []
for entity in feed.entity:
    v = entity.vehicle
    route = v.trip.route_id
    lat, lon = v.position.latitude, v.position.longitude
    # Vehicles not currently on a route (depot, out of service, no GPS
    # fix yet) report an empty route_id and/or (0, 0) -- both nonsensical
    # for Thunder Bay, so skip rather than show a bus at the equator.
    if not route or (lat == 0 and lon == 0):
        continue
    moving = v.position.speed >= MIN_SPEED_FOR_BEARING
    buses.append({
        'id': v.vehicle.id or v.vehicle.label or entity.id,
        'route': route,
        'lat': round(lat, 5),
        'lon': round(lon, 5),
        'heading_deg': round(v.position.bearing, 1) if moving else None,
        'speed_ms': round(v.position.speed, 1),
        'status': STATUS_LABEL.get(v.current_status),
        'stop_id': v.stop_id or None,
    })

print(f'{len(buses)} valid buses of {len(feed.entity)} entities')

out = {
    'fetched_at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    'feed_timestamp': feed.header.timestamp,
    'buses': buses,
}

with open('buses_live.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, separators=(',', ':'))

print('wrote buses_live.json:', len(buses), 'buses')
