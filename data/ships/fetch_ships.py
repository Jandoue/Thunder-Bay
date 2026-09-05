"""
Fetches current vessel positions near Thunder Bay from AISStream.io's free
real-time AIS feed and writes a compact JSON snapshot.

Requires a free API key (https://aisstream.io) supplied via the
AISSTREAM_API_KEY environment variable -- never hardcoded here, never
committed. Like OpenSky for the flights layer, this runs server-side on a
schedule (see .github/workflows/update-ships.yml) rather than from the
browser: AISStream is WebSocket-only and authenticates by putting the API
key in the subscription payload rather than a header, so a browser-embedded
key would be sitting in plain view of anyone who opens the page source. The
key stays a GitHub Actions secret; only the resulting position snapshot --
no key -- gets published to the site.

Connects, subscribes to a bounding box covering Thunder Bay harbour and the
western tip of Lake Superior, listens for a short window, and keeps only the
latest report per vessel (MMSI) seen during that window.
"""
import asyncio
import json
import os
import datetime

import websockets

API_KEY = os.environ["AISSTREAM_API_KEY"]

# Same footprint as the flights layer's bbox -- covers Thunder Bay harbour
# and the lake approach. Ships never appear over the land portion of this
# box, so there's no need for a tighter water-only polygon.
BBOX = [[47.95, -90.05], [48.85, -88.55]]

LISTEN_SECONDS = 25

# Standard ITU-R M.1371 AIS navigational status codes.
NAV_STATUS = {
    0: 'Under way (engine)', 1: 'At anchor', 2: 'Not under command',
    3: 'Restricted manoeuvrability', 4: 'Constrained by draught', 5: 'Moored',
    6: 'Aground', 7: 'Fishing', 8: 'Under way (sailing)',
    11: 'Towing astern', 12: 'Pushing/towing alongside', 14: 'AIS-SART/emergency',
    15: 'Not defined',
}


# Class A vessels report as PositionReport, which is the only one of the
# three that carries NavigationalStatus. Smaller craft (tugs, workboats --
# common in a working harbour like Thunder Bay's) mostly carry Class B
# transponders instead, which report as one of the other two types. Missing
# any of the three means missing most non-Class-A traffic entirely.
POSITION_MESSAGE_TYPES = ('PositionReport', 'StandardClassBPositionReport', 'ExtendedClassBPositionReport')


async def collect():
    ships = {}
    seen_types = {}
    total = 0
    async with websockets.connect('wss://stream.aisstream.io/v0/stream', compression='deflate') as ws:
        await ws.send(json.dumps({
            'APIKey': API_KEY,
            'BoundingBoxes': [[[40, -95], [55, -75]]],  # DIAGNOSTIC: wide Great Lakes box, no type filter
        }))
        try:
            async with asyncio.timeout(LISTEN_SECONDS):
                async for raw in ws:
                    total += 1
                    msg = json.loads(raw)
                    msg_type = msg.get('MessageType')
                    seen_types[msg_type] = seen_types.get(msg_type, 0) + 1
                    if msg_type not in POSITION_MESSAGE_TYPES:
                        continue
                    meta = msg.get('MetaData') or {}
                    pr = (msg.get('Message') or {}).get(msg_type) or {}
                    mmsi = meta.get('MMSI') or pr.get('UserID')
                    lat = pr.get('Latitude', meta.get('Latitude'))
                    lon = pr.get('Longitude', meta.get('Longitude'))
                    if mmsi is None or lat is None or lon is None:
                        continue
                    heading = pr.get('TrueHeading')
                    # Only the Class A PositionReport carries this field --
                    # Class B vessels simply don't transmit it, not an error.
                    nav_status = pr.get('NavigationalStatus')
                    name = (meta.get('ShipName') or pr.get('Name') or '').strip() or None
                    ships[mmsi] = {
                        'mmsi': mmsi,
                        'name': name,
                        'lat': round(lat, 4),
                        'lon': round(lon, 4),
                        'sog_kn': round(pr['Sog'], 1) if pr.get('Sog') is not None else None,
                        'cog_deg': round(pr['Cog'], 1) if pr.get('Cog') is not None else None,
                        'heading_deg': heading if heading is not None and heading != 511 else None,
                        'nav_status': nav_status,
                        'nav_status_label': NAV_STATUS.get(nav_status, 'Unknown' if nav_status is not None else None),
                    }
        except TimeoutError:
            pass
    print('DIAGNOSTIC total messages:', total, 'type breakdown:', seen_types)
    return ships


try:
    ships = asyncio.run(collect())
except Exception as e:
    # Covers a rejected/invalid API key too: AISStream closes the connection
    # abruptly rather than returning a JSON error for that case.
    print('FETCH FAILED:', e)
    raise SystemExit(1)

print(f'{len(ships)} vessel(s) seen in a {LISTEN_SECONDS}s window')

out = {
    'fetched_at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    'bbox': BBOX,
    'ships': list(ships.values()),
}

with open('ships_live.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, separators=(',', ':'))

print('wrote ships_live.json:', len(ships), 'vessels')
