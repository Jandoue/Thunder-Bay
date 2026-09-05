# Thunder Bay Civic Map

A scalable, multi-layer map of open civic data for Thunder Bay, Ontario — built to grow one layer at a time rather than serve one single purpose.

**Live site:** https://jandoue.github.io/Thunder-Bay/

## Built with AI

This project was built collaboratively with [Claude](https://claude.com/claude-code) (Anthropic's Claude Code), directed by [@Jandoue](https://github.com/Jandoue). Claude did the research, data fetching, geocoding, scraping, and front-end code; the human directed scope, caught real bugs (including a couple of genuine data-precision mistakes — see [Known limitations](#known-limitations--things-we-got-wrong-and-fixed)), and made the calls on what to include and how to source it responsibly. Nothing here is presented as more authoritative than its source data actually is — see each layer's notes below, and the in-app description text under each layer's expandable card on the map itself.

If you're evaluating this repo: the `data/` folder is deliberately kept alongside `index.html` specifically so the whole pipeline — raw pull → script → final embedded JSON — is inspectable, not just the finished map.

## Layers

| Layer | Records | Source | Notes |
|---|---|---|---|
| Police incidents | 3,758 of 9,276 (top 67 locations) | [Thunder Bay Police Service via CityProtect](https://www.cityprotect.com/agency/tbps) | Oct 2023–Oct 2024 only — TBPS's public feed hasn't been refreshed since Oct 24, 2024. Aggregated to block/intersection level (source data itself is block-level, not exact addresses). Data used under CityProtect's non-commercial research terms. |
| Fire stations | 9 | [City of Thunder Bay Open Data — ES Fire Stations](https://opendata.thunderbay.ca/maps/0d4b1b8a09ea492bba9815d958d11438) | Direct from the City's ArcGIS FeatureServer. |
| Fire response zones | 35 | [City of Thunder Bay Open Data — ES Fire Zones](https://opendata.thunderbay.ca/maps/aa3bc60010c14ede9ab6cee151abc6fe) | Boundary polygons simplified (Douglas-Peucker) from ~19,400 points down to ~1,200 for a fast render; colored by covering station. |
| Hydrants | 4,243 | [City of Thunder Bay Open Data — Hydrants Feature Layer](https://opendata.thunderbay.ca/maps/9d778b0ada6243c6b6a4399dbac1f526) | Full attribute set (matches the City's own ArcGIS viewer field-for-field). |
| Trees | 37,752 | [City of Thunder Bay Open Data — City of Thunder Bay Trees](https://opendata.thunderbay.ca/datasets/28aa2232c5654e84827158cf1a4cb073) | Full attribute set; rendered on canvas for performance at this density. |
| Heritage properties | 135 of 136 | [City of Thunder Bay Municipal Heritage Register](https://opendata.thunderbay.ca/datasets/bd50ba0dc1534a13b4cb6f057646b049) | The register lists names/addresses, not coordinates — every point here was geocoded (see [Known limitations](#known-limitations--things-we-got-wrong-and-fixed)). 1 property omitted (source address doesn't match any real Thunder Bay street). 53 pins are flagged approximate in their own popup where OpenStreetMap has no address-point data for that street. |
| Restaurants (menus) | 243 of 245 | [justthemenu.ca](https://justthemenu.ca/) (community-run menu directory, not affiliated with this project or the restaurants) | Only directory basics (name/address/phone/hours) plus a link back to the restaurant's menu page — menu text itself is their content and isn't reproduced here. Coordinates come from each listing's own linked Google/HERE/OSM map pin, not text geocoding. 2 listings have no address on the source site (delivery/online-only) and are omitted. |
| Highway cameras | 17 | [Ontario 511](https://511on.ca/) (Ministry of Transportation public API) | Covers the Northwestern Ontario highway corridor (Hwy 11/17/61/527/595, roughly Ignace to Nipigon), not just the city — that's the actual coverage area of this data, and it's what 511 cameras are for. Each popup embeds a live snapshot image (reloads on open, not a static photo). Other "Thunder Bay webcam" sources found while researching this (an old personal page, a CBC link) were dead; a NOAA "Thunder Bay" webcam turned out to be a different Thunder Bay, in Michigan. |
| Trails | 61 (60 named segments + the Trans Canada Trail) | [OpenStreetMap](https://www.openstreetmap.org/) via the [Overpass API](https://overpass-api.de/) | Not AllTrails — that site's terms prohibit scraping and it has no free API. OSM has no popularity or difficulty ratings (it just isn't tracked data), but coverage is genuinely strong for actively-mapped networks like Thunder Bay's mountain-bike singletrack. The Trans Canada Trail is stitched from its full 241-member route relation (42.9 km through the city) and highlighted separately from the other named trails. Length for each trail is computed directly from its own OSM geometry. |

Map tiles: [OpenStreetMap](https://www.openstreetmap.org/copyright) (© OpenStreetMap contributors, ODbL). Map library: [Leaflet](https://leafletjs.com/).

## Repo structure

```
index.html              the live map — self-contained, all layer data inlined
data/
  fire-hydrants/         build_layers.py + raw ArcGIS pulls + the merged bundle it produces
  trees/                 build_trees.py + the raw ArcGIS pull (37,752 features)
  heritage/              geocode_heritage.py, audit_precision.py, finalize_heritage.py
                          + the source CSV, intermediate geocoding results, and final output
  restaurants/           scrape_restaurants.py, patch_missing.py, finalize_restaurants.py
                          + the scraped list and final output
  police-incidents/      parse_crime.py, geocode_addresses.py + the 5 quarterly source CSVs
                          + aggregated/geocoded intermediate results
  cameras/               build_cameras.py + the raw 511 Ontario API pull and final output
  trails/                build_trails.py, the Overpass query used, the raw response, and final output
```

Each `data/<layer>/` folder holds the actual scripts that pulled and processed that layer, plus the raw and intermediate files they produced — the exact chain from source to what's embedded in `index.html`. Re-running a script re-fetches from the live source and reproduces its output; nothing here is generated from anything not in this repo.

## Rebuilding a layer

Each script is a self-contained Python file, run from inside its own `data/<layer>/` folder (they use relative paths). Examples:

```bash
cd data/fire-hydrants && python build_layers.py
cd data/trees && python build_trees.py
cd data/heritage && python geocode_heritage.py && python audit_precision.py && python finalize_heritage.py
cd data/restaurants && python scrape_restaurants.py && python patch_missing.py && python finalize_restaurants.py
cd data/police-incidents && python parse_crime.py
cd data/cameras && python build_cameras.py
cd data/trails && python build_trails.py
```

The heritage and restaurant geocoding scripts call the public [Nominatim](https://nominatim.org/) API and are rate-limited (~1 request/second) out of courtesy to that free service — expect a few minutes for a full run. Re-embedding a rebuilt layer's output into `index.html` is currently a manual step (find the layer's `const X = [...]` block and replace it).

## Known limitations — things we got wrong and fixed

Kept here on purpose rather than quietly cleaned up, since it's the more useful record:

- **Hydrant attributes were silently incomplete at first.** An early pull only requested `OBJECTID` and `BEAT`, then a later check of "is this field populated?" ran against that same trimmed data and wrongly concluded the City's own dataset was missing `LOC_ID` for every record. It wasn't — the field was never fetched. Refetched with the full field list once caught.
- **Heritage geocoding silently fell back to a street centroid** for addresses Nominatim couldn't match to an exact house number, rather than erroring. This got caught when a specific address ("1100 Ridgeway St E") turned out to just be pinned somewhere else on the same road. An audit pass checked every match's actual OSM classification (`class=highway` = a road-segment fallback, not a real address point) and reran Overpass queries directly against the raw address tags to confirm the data genuinely isn't in OpenStreetMap for ~53 addresses — those are now flagged as approximate in their own popup instead of presented as exact.
- **A restaurant-geocoding condition matched on the string `'google'`**, but every address link on the source site is a `maps.app.goo.gl` short link — which doesn't contain that substring. The check silently matched zero restaurants until it was changed to accept any `http` URL instead of guessing the domain.
- **Row-matching by name breaks when names repeat.** The heritage register has 13 different "Queen Anne Revival style house" entries at 13 different addresses; an early script matched geocoding results back to source rows by name and would have collapsed all 13 onto one coordinate. Fixed by matching on row index instead.
- **Camera popups rendered off-screen at first.** Their thumbnails are `<img>` tags pointing at live 511 Ontario snapshots, which load asynchronously — Leaflet sizes and positions a popup before its content has finished loading, so the popup ended up positioned for a much smaller box than the one that actually rendered. Fixed by calling the popup's `update()` once each image's `load` (or `error`) event fires.

## Contributing

This is a personal side project, not a City of Thunder Bay product. If you spot bad data, a better geocode, or want another open-data layer added:

- Open an issue or PR on this repo.
- For a new layer: add a `data/<layer>/` folder with whatever script(s) pulled the source data, plus its output, and add a `LAYERS.push({...})` block to `index.html` following the pattern of the existing layers (each one is self-contained: an id, a color, a description, and a `render()` function).
- If something here is factually wrong about a specific business, address, or property, the most durable fix is usually at the source (the City's open data portal, OpenStreetMap, or the relevant listing site) rather than only here — this map will re-pull from source if a layer is rebuilt.

## License / attribution

This repo mixes several sources with different terms — check the table above for which applies to which layer:

- City of Thunder Bay open data: [Open Data License](https://www.thunderbay.ca/en/city-services/resources/City-of-Thunder-Bay-Open-Data-Licence.pdf).
- OpenStreetMap data and tiles: [ODbL](https://www.openstreetmap.org/copyright), © OpenStreetMap contributors.
- Police incident data: via CityProtect, for non-commercial research/informational use.
- Restaurant listings: directory info only, linked back to [justthemenu.ca](https://justthemenu.ca/) for the actual menu content.

The code in this repo (`index.html`, the `data/*/*.py` scripts) is not separately licensed — ask if you want to reuse it for something specific.
