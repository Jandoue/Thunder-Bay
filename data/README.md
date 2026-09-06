# Data catalog

Every dataset behind [the map](https://jandoue.github.io/Thunder-Bay/) is a plain file here — no API key, no auth, no rate limit (for the static ones). Fetch it directly, e.g.:

```bash
curl https://jandoue.github.io/Thunder-Bay/data/fire-hydrants/hydrants.json
```

Each layer folder has the same shape: a rebuild script (`build_*.py` / `finalize_*.py`), whatever raw/intermediate files that script consumes, and the final `<name>.json` the site actually fetches — that final file is always the one to reach for. Coordinates are `[lat, lon]` in WGS84 (EPSG:4326) everywhere except `fire_zones.json`'s `rings`, which are `[lon, lat]` because that's GeoJSON's own convention and these came straight from a GeoJSON source.

**License**: see the root [README](../README.md#license--attribution) for per-source terms — they differ by layer (City of Thunder Bay open data, OpenStreetMap ODbL, CityProtect non-commercial-use, etc.) and aren't repeated per-file here.

---

## Police incidents

**File**: `police-incidents/incidents.json` · 67 records · rebuild: `python parse_crime.py && python geocode_addresses.py && python finalize_incidents.py`

| Field | Type | Meaning |
|---|---|---|
| `lat`, `lon` | number | Location (block/intersection level, not an exact address) |
| `addr` | string | Display address, e.g. `"700 Block Memorial Ave"` |
| `fsa` | string | Forward Sortation Area (first 3 characters of the postal code) |
| `count` | number | Total incidents at this location, Oct 2023–Oct 2024 |
| `bucket` | string | The single largest category by count, used for the marker's fill color |
| `breakdown` | string | Every category and its count, comma-separated, sorted descending |

Source: Thunder Bay Police Service via CityProtect. Only the 67 busiest locations are included (see the root README for why).

## Fire stations

**File**: `fire-hydrants/fire_stations.json` · 9 records · rebuild: `python build_layers.py`

| Field | Type | Meaning |
|---|---|---|
| `name` | string | e.g. `"Station 1"` |
| `addr` | string | Street address |
| `lat`, `lon` | number | Location |

## Fire response zones

**File**: `fire-hydrants/fire_zones.json` · 35 records · rebuild: `python build_layers.py`

| Field | Type | Meaning |
|---|---|---|
| `area` | string | Zone code, e.g. `"3W"` |
| `station` | string | Covering station name |
| `rings` | array | Polygon ring(s): array of `[lon, lat]` pairs (GeoJSON coordinate order, not `[lat, lon]`) — simplified via Douglas-Peucker from ~19,400 points to ~1,200 |

## Hydrants

**File**: `fire-hydrants/hydrants.json` · 4,243 records · rebuild: `python build_layers.py`

Field names match the City's own ArcGIS field abbreviations directly (kept short since this file has 4,243 rows):

| Field | Source field | Meaning |
|---|---|---|
| `lat`, `lon` | — | Location |
| `id` | `OBJECTID` | ArcGIS object ID |
| `loc` | `LOC_ID` | Location ID (the hydrant's own identifier, e.g. `"PC0088"`) |
| `fdmid` | `FDMID` | Fire Department Master ID |
| `beat` | `BEAT` | Patrol/response beat, e.g. `"N 11"` |
| `rot` | `ROT_ANGLE` | Rotation angle in degrees (map symbol orientation) |
| `node` | `NODE_ID` | Water network node ID |
| `gid` | `GLOBALID` | ArcGIS global ID (UUID) |
| `x`, `y` | `X_COORD`, `Y_COORD` | Projected coordinates, NAD83 |
| `created` | `CREATEDDATE` | Install/record-creation date, `YYYY-MM-DD` |
| `updated` | `LASTUPDATE` | Last updated date, `YYYY-MM-DD` |

## Trees

**File**: `trees/trees.json` · 37,752 records (~9 MB) · rebuild: `python build_trees.py`

| Field | Type | Meaning |
|---|---|---|
| `lat`, `lon` | number | Location |
| `common` | string\|null | Common species name, e.g. `"CHERRY SPECIES"` |
| `botanical` | string\|null | Botanical/Latin name (often abbreviated in the source data) |
| `street` | string\|null | Street the tree is on |
| `civic_address` | string\|null | Nearest civic address |
| `overhead` | string\|null | Overhead wires present: `"Y"` / `"N"` |
| `unitid` | string\|null | City unit/inventory ID |
| `objectid` | number | ArcGIS object ID |
| `globalid` | string\|null | ArcGIS global ID (UUID) |

`EXPDATE` and `TREE_CYCLE` exist in the source but are blank/constant for all 37,752 records, so they aren't included here.

## Heritage properties

**File**: `heritage/heritage.json` · 135 records · rebuild: `python geocode_heritage.py && python audit_precision.py && python finalize_heritage.py`

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Property name |
| `addr` | string | Display address |
| `circa` | string | Approximate construction year |
| `status` | string | Register status: `Designated`, `Listed`, or a Waverley Park variant |
| `year_added` | string | Year added to the register |
| `bylaw` | string | By-law or report number |
| `ownership` | string | e.g. `"City of Thunder Bay"`, `"Private"` |
| `lat`, `lon` | number | Location (geocoded — see below) |
| `approx` | string\|null | Present only when the pin is approximate; explains why (see root README's "Known limitations") |

## Restaurants (Justthemenu.ca)

**File**: `restaurants/restaurants.json` · 243 records · rebuild: `python scrape_restaurants.py && python patch_missing.py && python finalize_restaurants.py`

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Restaurant name |
| `addr` | string\|null | Address, when listed on the source site |
| `phone` | string | Phone number, or empty |
| `hours` | string\|null | Free-text hours as listed |
| `lat`, `lon` | number | Location, from the listing's own linked map pin (not text geocoding) |
| `url` | string | Link to the restaurant's page on justthemenu.ca — menu content itself isn't reproduced here |
| `src` | string | Where the coordinate came from: `google_maps_link`, `here_maps_link`, `here_maps_b64`, or `osm_node` |

## Cameras

**File**: `cameras/cameras.json` · 19 records (17 Ontario 511 + 1 YouTube + 1 FAA/NAV CANADA site with 4 directions) · rebuild: `python build_cameras.py`

Three record shapes, distinguished by `source`. 511 records (`source: "511"`):

| Field | Type | Meaning |
|---|---|---|
| `id` | number | 511 Ontario camera ID |
| `location` | string | Description, e.g. `"Highway 11 near Gorge Creek Road"` |
| `roadway` | string | Highway name |
| `direction` | string | Facing direction, or `"Unknown"` |
| `lat`, `lon` | number | Location |
| `views` | array | One or more `{url, desc}` objects — `url` is a *live* snapshot image, not a stored photo; it changes every time it's loaded |

YouTube records (`source: "youtube"`), hand-curated in `cameras/youtube_cams.json` and merged into `cameras.json` by `build_cameras.py` (there's no API to discover these — each one is manually found and verified as an actually-live, ongoing stream, not a one-off recording, before being added):

| Field | Type | Meaning |
|---|---|---|
| `id` | string | A slug, e.g. `"yt-landfill"` (not a numeric 511 ID) |
| `location` | string | Description including the street address where known |
| `lat`, `lon` | number | Location |
| `youtube_id` | string | The video's YouTube ID — embed at `youtube.com/embed/<youtube_id>` |
| `channel` | string | The YouTube channel's display name, for attribution |
| `channel_url` | string | Link to the video/channel on YouTube |

FAA records (`source: "faa"`), hand-curated in `cameras/airport_cams.json`. Unlike the other two sources, this one is a **link-out only, no embedded image**: `weathercams.faa.gov`'s API that reveals which snapshot is current sits behind Akamai bot-detection (confirmed directly — a plain server-side request gets HTTP 401, while the same request from an already-loaded browser session succeeds), and this project treats that as a "please don't automate this" signal rather than something to work around. The underlying image CDN itself isn't protected, but there's no way to discover the current image URL without the protected API, so there's nothing reliable to embed.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | A slug, e.g. `"faa-cyqt"` |
| `location` | string | Site name, e.g. `"Thunder Bay Airport (CYQT)"` |
| `lat`, `lon` | number | Location of the camera site (one physical site, multiple directions) |
| `operator` | string | Who actually runs the cameras (NAV CANADA) — FAA WeatherCams just displays them |
| `site_url` | string | Link to the live viewer on weathercams.faa.gov |
| `directions` | array | `{direction, bearing}` objects, one per camera angle (North/East/South/West here) — all link to the same `site_url`, since a per-camera deep link wasn't reliable to construct |

## Trails

**File**: `trails/trails.json` · 60 named trails + the Trans Canada Trail · rebuild: `python build_trails.py`

Top-level shape is `{trails: [...], tct: {...}}`, not a flat array.

`trails[]`:

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Trail name |
| `type` | string | OSM `highway` value, e.g. `"Path"`, `"Track"` |
| `surface` | string\|null | OSM `surface` tag |
| `length_km` | number | Computed directly from `points` via the haversine formula |
| `points` | array | `[lat, lon]` pairs tracing the trail |
| `part_of_tct` | boolean | Whether this segment is also part of the Trans Canada Trail |
| `osm_id` | number | OpenStreetMap way ID — `openstreetmap.org/way/<osm_id>` |

`tct` (Trans Canada Trail, stitched from 241 OSM way segments into one route):

| Field | Type | Meaning |
|---|---|---|
| `name` | string | `"Trans Canada Trail (Thunder Bay)"` |
| `segments` | array | Array of `[lat, lon]` polylines, one per underlying OSM way |
| `length_km` | number | Total length through the city |

## Live flights

**File**: `flights/flights_live.json` · rewritten roughly every 10 minutes by [a GitHub Action](../.github/workflows/update-flights.yml), not a one-off build

Top-level: `{fetched_at, opensky_time, bbox, aircraft: [...]}`. `fetched_at` (ISO 8601, UTC) is how you tell how fresh a given fetch is — this is polling, not a push feed. `bbox` is the query region sent to OpenSky.

`aircraft[]`:

| Field | Type | Meaning |
|---|---|---|
| `icao24` | string | Aircraft's 24-bit ICAO address (its stable identifier) |
| `callsign` | string\|null | Flight callsign |
| `country` | string | Registered country |
| `lat`, `lon` | number | Position |
| `alt_m` | number\|null | Barometric altitude, metres |
| `on_ground` | boolean | |
| `velocity_ms` | number\|null | Ground speed, m/s |
| `heading_deg` | number\|null | True track, degrees |
| `vertical_rate_ms` | number\|null | Climb (+) / descent (-), m/s |
| `squawk` | string\|null | Transponder code |
| `category` | string | `ground` / `low` (likely near YQT) / `cruise` (likely overflying) — a local heuristic on altitude, not flight-plan data |
| `path` | array\|absent | `[lat, lon]` pairs, present for at most 3 aircraft per fetch (credit-budget reasons — see root README) |

No source/destination airport field — see the root README for why that's a real data-source gap, not an oversight.

## Live ships

**File**: `ships/ships_live.json` · rewritten roughly every 10 minutes by [a GitHub Action](../.github/workflows/update-ships.yml)

Top-level: `{fetched_at, bbox, ships: [...]}`. **An empty `ships` array is a normal, expected state** — Great Lakes shipping is seasonal (roughly late March–December), the feed is terrestrial-AIS-reception only (see root README), and `AISSTREAM_API_KEY` must be configured as a repo secret for this file to populate at all on a fork.

`ships[]`:

| Field | Type | Meaning |
|---|---|---|
| `mmsi` | number | Maritime Mobile Service Identity — the vessel's stable identifier |
| `name` | string\|null | Vessel name, when known |
| `lat`, `lon` | number | Position |
| `sog_kn` | number\|null | Speed over ground, knots |
| `cog_deg` | number\|null | Course over ground, degrees |
| `heading_deg` | number\|null | True heading, degrees (absent for many Class B transponders — see below) |
| `nav_status` | number\|null | Raw ITU-R M.1371 navigational status code |
| `nav_status_label` | string\|null | Human-readable status, e.g. `"At anchor"`, `"Moored"`. `null` specifically means the code is genuinely absent from the AIS message (normal for Class B transponders, common on smaller harbour craft) — not a parsing failure. |

## Live buses

**File**: `buses/buses_live.json` · rewritten roughly every 10 minutes by [a GitHub Action](../.github/workflows/update-buses.yml)

Top-level: `{fetched_at, feed_timestamp, buses: [...]}`. `feed_timestamp` is the Unix timestamp NextLift's own feed header reports (when *they* last updated it), separate from `fetched_at` (when this repo last polled it).

`buses[]`:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Vehicle/fleet number |
| `route` | string | Route number, e.g. `"3C"` — matches Thunder Bay Transit's public route numbering, not looked up from any file here (see root README) |
| `lat`, `lon` | number | Position |
| `heading_deg` | number\|null | Bearing, degrees — `null` below ~2 m/s (7 km/h), where the feed's own bearing reading isn't reliable, checked directly against a live pull (see `fetch_buses.py`) |
| `speed_ms` | number | Speed, m/s |
| `status` | string\|null | `incoming` (approaching a stop) / `stopped` (at a stop) / `in_transit` |
| `stop_id` | string\|null | The stop the vehicle is at/approaching/departing — a raw GTFS stop ID, not a name (no stop-name lookup is used here, see root README) |

Vehicles with no route assigned or no GPS fix (out of service, at the depot) are dropped before this file is written, not included with blank fields.

## What's *not* here

- **Raw/intermediate pulls** (`*_raw.geojson`, `*_scraped.json`, `precision_audit.json`, etc.) exist in each folder for pipeline transparency but aren't meant to be consumed directly — they're pre-cleanup, may have different field names, and in a couple of cases (trees, heritage) are positional or differently-shaped from the final output.
- **A single combined "all layers" file.** Each dataset is independent; there's no manifest endpoint. This file *is* the manifest.
