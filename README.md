# Thunder Bay Civic Map

A scalable, multi-layer map of open civic data for Thunder Bay, Ontario — built to grow one layer at a time rather than serve one single purpose.

**Live site:** https://jandoue.github.io/Thunder-Bay/

## Built with AI

This project was built collaboratively with [Claude](https://claude.com/claude-code) (Anthropic's Claude Code), directed by [@Jandoue](https://github.com/Jandoue). Claude did the research, data fetching, geocoding, scraping, and front-end code; the human directed scope, caught real bugs (including a couple of genuine data-precision mistakes — see [Known limitations](#known-limitations--things-we-got-wrong-and-fixed)), and made the calls on what to include and how to source it responsibly. Nothing here is presented as more authoritative than its source data actually is — see each layer's notes below, and the in-app description text under each layer's expandable card on the map itself.

If you're evaluating this repo: the `data/` folder is deliberately kept alongside `index.html` specifically so the whole pipeline — raw pull → script → final JSON — is inspectable, not just the finished map. Every dataset is also a plain file the site fetches at runtime (not embedded in the HTML), so it's directly reusable — see [data/README.md](data/README.md) for the full field-by-field catalog of every layer.

## Layers

| Layer | Records | Source | Notes |
|---|---|---|---|
| Police incidents | 3,758 of 9,276 (top 67 locations) | [Thunder Bay Police Service via CityProtect](https://www.cityprotect.com/agency/tbps) | Oct 2023–Oct 2024 only — TBPS's public feed hasn't been refreshed since Oct 24, 2024. Aggregated to block/intersection level (source data itself is block-level, not exact addresses). Data used under CityProtect's non-commercial research terms. |
| Fire stations | 9 | [City of Thunder Bay Open Data — ES Fire Stations](https://opendata.thunderbay.ca/maps/0d4b1b8a09ea492bba9815d958d11438) | Direct from the City's ArcGIS FeatureServer. |
| Fire response zones | 35 | [City of Thunder Bay Open Data — ES Fire Zones](https://opendata.thunderbay.ca/maps/aa3bc60010c14ede9ab6cee151abc6fe) | Boundary polygons simplified (Douglas-Peucker) from ~19,400 points down to ~1,200 for a fast render; colored by covering station. |
| Hydrants | 4,243 | [City of Thunder Bay Open Data — Hydrants Feature Layer](https://opendata.thunderbay.ca/maps/9d778b0ada6243c6b6a4399dbac1f526) | Full attribute set (matches the City's own ArcGIS viewer field-for-field). |
| Trees | 37,752 | [City of Thunder Bay Open Data — City of Thunder Bay Trees](https://opendata.thunderbay.ca/datasets/28aa2232c5654e84827158cf1a4cb073) | Full attribute set; rendered on canvas for performance at this density. |
| Heritage properties | 135 of 136 | [City of Thunder Bay Municipal Heritage Register](https://opendata.thunderbay.ca/datasets/bd50ba0dc1534a13b4cb6f057646b049) | The register lists names/addresses, not coordinates — every point here was geocoded (see [Known limitations](#known-limitations--things-we-got-wrong-and-fixed)). 1 property omitted (source address doesn't match any real Thunder Bay street). 53 pins are flagged approximate in their own popup where OpenStreetMap has no address-point data for that street. |
| Justthemenu.ca (restaurants) | 243 of 245 | [Justthemenu.ca](https://justthemenu.ca/) (community-run menu directory, not affiliated with this project or the restaurants) | Only directory basics (name/address/phone/hours) plus a link back to the restaurant's menu page — menu text itself is their content and isn't reproduced here. Coordinates come from each listing's own linked Google/HERE/OSM map pin, not text geocoding. 2 listings have no address on the source site (delivery/online-only) and are omitted. |
| Highway cameras | 17 | [Ontario 511](https://511on.ca/) (Ministry of Transportation public API) | Covers the Northwestern Ontario highway corridor (Hwy 11/17/61/527/595, roughly Ignace to Nipigon), not just the city — that's the actual coverage area of this data, and it's what 511 cameras are for. Each popup embeds a live snapshot image (reloads on open, not a static photo). Other "Thunder Bay webcam" sources found while researching this (an old personal page, a CBC link) were dead; a NOAA "Thunder Bay" webcam turned out to be a different Thunder Bay, in Michigan. |
| Trails | 61 (60 named segments + the Trans Canada Trail) | [OpenStreetMap](https://www.openstreetmap.org/) via the [Overpass API](https://overpass-api.de/) | Not AllTrails — that site's terms prohibit scraping and it has no free API. OSM has no popularity or difficulty ratings (it just isn't tracked data), but coverage is genuinely strong for actively-mapped networks like Thunder Bay's mountain-bike singletrack. The Trans Canada Trail is stitched from its full 241-member route relation (42.9 km through the city) and highlighted separately from the other named trails. Length for each trail is computed directly from its own OSM geometry. |
| Live flights | live (~5&ndash;10 aircraft typically) | [OpenSky Network](https://opensky-network.org/) public ADS-B API | The only layer here that isn't a static snapshot — see [Why flights are architecturally different](#why-flights-are-architecturally-different) below. Shows position and altitude, not flight plans: aircraft are heuristically labelled "low altitude" (probably arriving/departing YQT) or "cruise altitude" (probably overflying). A few aircraft per refresh also get a dashed trail showing their actual recently-flown path (via OpenSky's `/tracks` endpoint, capped to conserve the shared anonymous request budget). No source/destination field — tested directly against OpenSky's flight-route data and it doesn't reliably resolve for this area (see below), so it's left out rather than shown as frequently blank. |
| Live ships | live (fewer vessels than commercial trackers, see below) | [AISStream.io](https://aisstream.io/) free real-time AIS feed | The marine counterpart to the flights layer, same refresh mechanism and same honesty about what "live" means — see [Why flights and ships are architecturally different](#why-flights-and-ships-are-architecturally-different). Requires a free AISStream API key stored as a GitHub Actions secret, never committed to this repo. Thunder Bay is a working grain/bulk port, not a passenger harbour, so expect lakers and tugs. Great Lakes shipping is seasonal (roughly late March&ndash;December); an empty layer in winter is correct, not broken. Terrestrial-reception-only, so it structurally misses vessels only reachable via satellite/roaming AIS &mdash; verified directly against a real vessel MarineTraffic showed that this feed never received. |

Map tiles: [OpenStreetMap](https://www.openstreetmap.org/copyright) (© OpenStreetMap contributors, ODbL). Map library: [Leaflet](https://leafletjs.com/).

## Repo structure

```
index.html              the live map -- fetches every dataset below at runtime, nothing is inlined
LICENSE                 MIT, for the code only -- data licensing is per-source, see below
data/
  README.md             full field-by-field catalog for every dataset, for anyone reusing the data directly
  fire-hydrants/         build_layers.py -> fire_stations.json, fire_zones.json, hydrants.json
  trees/                 build_trees.py -> trees.json (37,752 features)
  heritage/              geocode_heritage.py, audit_precision.py, finalize_heritage.py -> heritage.json
  restaurants/           scrape_restaurants.py, patch_missing.py, finalize_restaurants.py -> restaurants.json
  police-incidents/      parse_crime.py, geocode_addresses.py, finalize_incidents.py -> incidents.json
  cameras/               build_cameras.py -> cameras.json
  trails/                build_trails.py -> trails.json
  flights/               fetch_flights.py -> flights_live.json (rewritten every ~10 min by a GitHub Action,
                          not a one-off pull — see "Why flights and ships are architecturally different" below)
  ships/                 fetch_ships.py -> ships_live.json, same live-refresh pattern as flights,
                          needs a free AISStream.io API key stored as a repo secret to actually populate
```

Each `data/<layer>/` folder holds the actual scripts that pulled and processed that layer, plus the raw/intermediate files they produced along the way — the exact chain from source to the final `<name>.json`, which is also the one file each layer's `render()` function in `index.html` fetches. Re-running a script re-fetches from the live source (or reprocesses the raw pull already in the folder) and reproduces its output; nothing here is generated from anything not in this repo.

## Rebuilding a layer

Each script is a self-contained Python file, run from inside its own `data/<layer>/` folder (they use relative paths), and writes its final `<name>.json` directly — no separate step to wire it into `index.html`, since the page fetches that file by name at runtime.

```bash
cd data/fire-hydrants && python build_layers.py
cd data/trees && python build_trees.py
cd data/heritage && python geocode_heritage.py && python audit_precision.py && python finalize_heritage.py
cd data/restaurants && python scrape_restaurants.py && python patch_missing.py && python finalize_restaurants.py
cd data/police-incidents && python parse_crime.py && python geocode_addresses.py && python finalize_incidents.py
cd data/cameras && python build_cameras.py
cd data/trails && python build_trails.py
cd data/flights && python fetch_flights.py   # normally run by GitHub Actions, not by hand
cd data/ships && python fetch_ships.py       # ditto -- needs AISSTREAM_API_KEY set in the environment
```

The heritage and restaurant geocoding scripts call the public [Nominatim](https://nominatim.org/) API and are rate-limited (~1 request/second) out of courtesy to that free service — expect a few minutes for a full run.

## Why flights and ships are architecturally different

Every other layer on this map is a snapshot: pull once, process, embed the result directly in `index.html`. Flights and ships can't work that way and still be live, and it turns out "live" runs into a wall none of the other layers hit.

[OpenSky Network](https://opensky-network.org/)'s free public API is the only genuinely open real-time flight-tracking source that doesn't require a paid key — but it only allows requests from its own site (`Access-Control-Allow-Origin: https://opensky-network.org`), which blocks any other page's JavaScript from calling it directly, GitHub Pages included. There's no client-side fix for that; it's enforced by the browser.

The workaround: [`.github/workflows/update-flights.yml`](.github/workflows/update-flights.yml) runs `data/flights/fetch_flights.py` on a schedule (every 10 minutes) inside a GitHub Actions runner — a server, not a browser, so the restriction doesn't apply — and commits the result to `data/flights/flights_live.json`. The map's JavaScript then fetches that file from its own origin, which is unrestricted. So "real-time" here actually means "refreshed roughly every 10 minutes by a scheduled job," not a live socket — worth knowing if you were expecting second-by-second tracking. It's also why this is the one layer that won't show anything if you open `index.html` as a local file instead of via a real web server: browsers block `fetch()` of local relative files under `file://`.

**Why some aircraft show a path and others don't, and why there's no source/destination.** Anonymous (no sign-up) OpenSky access shares one 400-request/day credit budget across every endpoint, and the endpoint that returns an aircraft's actual flown track (`/api/tracks/all`) costs more per call than the one that returns positions (`/api/states/all`). To stay well inside that budget, each run fetches a track for at most 3 aircraft (prioritizing ones likely near YQT), trimmed to roughly their last 45 minutes rather than their whole flight. Source/destination airports were also investigated — OpenSky can estimate a route, but only *after* a flight lands, using an algorithm that in direct testing didn't match a single one of the actual aircraft seen near Thunder Bay across a 4-hour sample. Rather than show a field that's usually going to say "unknown," it isn't shown at all.

**Ships work the same way, with one added wrinkle: a required API key.** [AISStream.io](https://aisstream.io/) is free and doesn't require running your own AIS receiver (unlike AISHub, which asks members to feed data back in exchange for access), but unlike OpenSky it isn't anonymous — it's WebSocket-only, and authenticates by putting an API key inside the subscription message itself rather than an HTTP header. That matters here because a browser-embedded key sits in plain view of anyone who opens the page's source, so a scraper (or anyone bored) could lift it and burn through the account's connection limit. The same GitHub Actions pattern used for flights sidesteps that: `data/ships/fetch_ships.py` opens a short-lived connection, subscribes with the key read from a `AISSTREAM_API_KEY` repository secret, listens for a little over 3 minutes, and writes whatever it saw — the key itself never leaves the Action run or touches this repo. Setting this layer up requires a free account at [aisstream.io](https://aisstream.io/) and adding its key as a repo secret (`gh secret set AISSTREAM_API_KEY`, or via the repo's Settings &rarr; Secrets and variables &rarr; Actions) — nothing here can do that step automatically, on purpose.

The listen window is much longer than the flights layer's single request, for a real reason found while debugging this: AIS vessels report their position every few seconds while moving, but as rarely as once per 3 minutes while moored or anchored (a fixed cycle set by the ITU-R M.1371 standard, on the vessel's own clock) — and a working harbour spends most of its time with ships docked, not moving. A short window and a message-type filter that only asked for Class A traffic both independently caused early test runs to silently return zero vessels, despite several being visibly present in the harbour at the time on a public AIS tracker used to confirm that. A missing `compression='deflate'` flag on the WebSocket connection turned out to be the biggest culprit of all — AISStream's own docs say it's required "to serve full message bandwidth," and a side-by-side test (wide box, no filter) went from 0 messages to 74 the moment it was set.

**Why this layer will always show fewer vessels than MarineTraffic or similar sites, structurally, not as a bug.** AISStream aggregates a community network of land-based (terrestrial) AIS receivers only — [confirmed directly against their own coverage documentation](https://aisstream.io/coverage), which describes shore stations with a roughly 40 nautical mile range and explicitly no satellite reception. Bigger commercial trackers blend in satellite AIS and "roaming" data (other ships' satellite-linked receivers relaying positions for vessels beyond shore range) on top of their own terrestrial network. Caught a concrete example of this while testing: a vessel ("RESKO") visible at anchor in Thunder Bay on MarineTraffic never appeared in this layer across several runs — its listed AIS source there was "Roaming," a category this free terrestrial-only feed has no access to at all, regardless of listen-window length or message filters. Two other real vessels ("BLACKY," "FEDERAL SETO") *were* caught successfully, confirming there is real shore-based coverage of the Thunder Bay area — just not complete coverage of every vessel present.

## Known limitations — things we got wrong and fixed

Kept here on purpose rather than quietly cleaned up, since it's the more useful record:

- **Hydrant attributes were silently incomplete at first.** An early pull only requested `OBJECTID` and `BEAT`, then a later check of "is this field populated?" ran against that same trimmed data and wrongly concluded the City's own dataset was missing `LOC_ID` for every record. It wasn't — the field was never fetched. Refetched with the full field list once caught.
- **Heritage geocoding silently fell back to a street centroid** for addresses Nominatim couldn't match to an exact house number, rather than erroring. This got caught when a specific address ("1100 Ridgeway St E") turned out to just be pinned somewhere else on the same road. An audit pass checked every match's actual OSM classification (`class=highway` = a road-segment fallback, not a real address point) and reran Overpass queries directly against the raw address tags to confirm the data genuinely isn't in OpenStreetMap for ~53 addresses — those are now flagged as approximate in their own popup instead of presented as exact.
- **A restaurant-geocoding condition matched on the string `'google'`**, but every address link on the source site is a `maps.app.goo.gl` short link — which doesn't contain that substring. The check silently matched zero restaurants until it was changed to accept any `http` URL instead of guessing the domain.
- **Row-matching by name breaks when names repeat.** The heritage register has 13 different "Queen Anne Revival style house" entries at 13 different addresses; an early script matched geocoding results back to source rows by name and would have collapsed all 13 onto one coordinate. Fixed by matching on row index instead.
- **Camera popups rendered off-screen at first.** Their thumbnails are `<img>` tags pointing at live 511 Ontario snapshots, which load asynchronously — Leaflet sizes and positions a popup before its content has finished loading, so the popup ended up positioned for a much smaller box than the one that actually rendered. Fixed by calling the popup's `update()` once each image's `load` (or `error`) event fires.
- **The ships layer's first live run found zero vessels** despite real ones being visibly present in the harbour on a public tracker at the time — checked directly rather than assumed to be a quiet night. Three real bugs compounded: the message-type filter only asked for Class A traffic (missing Class B, common on smaller harbour craft); the WebSocket connection was missing `compression='deflate'`, which AISStream's docs say is required for the server to send anything close to full bandwidth; and a 25-second listen window was too short to reliably catch a moored vessel's ~3-minute AIS reporting cycle. Fixing all three got real vessels flowing. A related but separate discovery, not a bug: GitHub Pages' CDN can serve a stale cached copy of a data file for a few minutes after a new commit even with `cache: 'no-store'` on the client fetch (that header only controls the browser's own cache) — fixed by appending a cache-busting timestamp to both the ships and flights fetch URLs.
- **The mobile layout was completely broken — the map was invisible on every phone.** A CSS media query set the map's height for narrow viewports, but an unconditional rule of equal specificity came later in the stylesheet and silently won at every width, collapsing the map to 0px height on anything ≤860px wide. Existed from the very first version of the page; found by an accessibility/UX audit, not by testing on an actual phone, which is exactly the kind of bug that step was worth doing.
- **Three of the seven data-rebuild scripts silently produced empty or wrong output.** `build_trees.py` globbed for `trees_p*.geojson` (a paginated-pull naming scheme) when the repo only ever had one `trees_raw.geojson`, so it matched nothing and wrote an empty file without erroring. `build_layers.py` and `build_cameras.py` had the same problem with different filenames (`hydrants_full_p*.geojson` vs. the real `hydrants_raw_p*.geojson`; `cams_511.json` vs. the real `cams_511_raw.json`), and `finalize_heritage.py` looked for `heritage.csv` instead of the real `heritage_register.csv`. None of these were caught earlier because nobody had re-run them since the initial pull — the very first real test of "rebuild a layer from scratch" (prompted by this cleanup pass) is what surfaced them. All four now point at the files that actually exist.
- **The police-incidents pipeline had no `finalize_*.py` step at all** — unlike every other layer, the 70→67-row cleanup (title-casing addresses, expanding abbreviations, and merging a couple of adjacent block-range entries on the same corridor into one combined entry) had been done by hand at some point and never written down. Reconstructed it by diffing the intermediate `geocoded_points.json` against the incidents already shipping, encoded the specific merges and renames that diff revealed, and verified the result matches all 67 rows exactly (down to the category breakdown) before trusting it — see `data/police-incidents/finalize_incidents.py`.

## Contributing

This is a personal side project, not a City of Thunder Bay product. If you spot bad data, a better geocode, or want another open-data layer added:

- Open an issue or PR on this repo.
- For a new layer: add a `data/<layer>/` folder with whatever script(s) pulled the source data, writing its final output to `data/<layer>/<name>.json`; document its fields in `data/README.md`; and add a `LAYERS.push({...})` block to `index.html` following the pattern of the existing layers (an id, a color, a description, and a `render()` function that calls `loadData(id, url)` and returns the resulting promise so the sidebar's loading/error state works automatically).
- If something here is factually wrong about a specific business, address, or property, the most durable fix is usually at the source (the City's open data portal, OpenStreetMap, or the relevant listing site) rather than only here — this map will re-pull from source if a layer is rebuilt.

## License / attribution

The code in this repo (`index.html`, the `data/*/*.py` scripts, the GitHub Actions workflows) is [MIT licensed](LICENSE) — reuse it freely.

The **data** is not covered by that license and mixes several sources with different terms — check the layers table above for which applies to which layer, and [data/README.md](data/README.md) for per-file details:

- City of Thunder Bay open data: [Open Data License](https://www.thunderbay.ca/en/city-services/resources/City-of-Thunder-Bay-Open-Data-Licence.pdf).
- OpenStreetMap data and tiles: [ODbL](https://www.openstreetmap.org/copyright), © OpenStreetMap contributors.
- Police incident data: via CityProtect, for non-commercial research/informational use.
- Restaurant listings: directory info only, linked back to [Justthemenu.ca](https://justthemenu.ca/) for the actual menu content.
