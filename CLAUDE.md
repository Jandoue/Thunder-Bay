# Thunder Bay Civic Map — project notes for Claude

Live site: https://jandoue.github.io/Thunder-Bay/
Repo: https://github.com/Jandoue/Thunder-Bay (owner: @Jandoue)
Local path: `C:\Users\jlano\thunder-bay-civic-map`

This file is operating context for Claude Code, not user-facing docs — for
that, see [README.md](README.md) (project overview, per-layer sourcing and
limitations, license) and [data/README.md](data/README.md) (field-by-field
schema for every dataset). Read those two before making changes; this file
just covers things a fresh session needs to know that aren't written down
there.

## What this is

A single-page Leaflet map (`index.html`, ~45KB) of open civic data for
Thunder Bay, Ontario. No build step, no framework — plain HTML/CSS/JS,
hosted on GitHub Pages directly from `main`. Every dataset is a separate
JSON file under `data/<layer>/`, fetched lazily the first time its layer is
switched on (see `loadData()` in index.html).

## UI architecture

Top bar → horizontal category tabs → a chip panel for the active category's
layers → the map, in a fixed-height flex shell (`.app-shell{height:100vh}`)
so the map always gets whatever space the header/tabs/panel don't need. The
footer lives *outside* that shell on purpose, so it can never squeeze the
map's share — this was a real bug once (map rendered at 0px on mobile from
a CSS ordering mistake); the current structure makes that class of bug
structurally hard to reintroduce, don't undo it for a quick fix.

- `CATEGORIES` (in index.html): the 4 tabs — Public Safety, Nature & Trails,
  Explore, Transportation. Each layer declares which one it belongs to via
  `category`.
- `LAYERS`: the registry. Each entry needs `id`, `category`, `name`, `color`,
  `count` (a static string, not computed at load time), `desc`, optionally
  `legendHTML()` and `afterRender()`, and `render(group)` which populates the
  passed `L.layerGroup` and **returns a Promise** (call `loadData(id, url)`
  for anything under `data/`) — the panel's loading/error state depends on
  that promise resolving/rejecting.
- Toggles are real `<input type="checkbox" role="switch">` wrapped in a
  `<label class="switch">` — **must** be a `<label>`, not a `<span>`: the
  visible track/thumb sit on top of the input in stacking order, so without
  native label-to-control forwarding, clicks on the switch don't toggle
  anything (this exact bug shipped once and was reported by the user before
  being fixed).
- Nothing defaults on. Don't reintroduce a `defaultOn: true` layer without
  being asked — that was deliberately removed per user request.

## Layers by category

| Category | Layers | Notes |
|---|---|---|
| Public Safety | Police Incidents, Fire Stations, Fire Response Zones, Hydrants | All static, City of Thunder Bay open data + CityProtect |
| Nature & Trails | Trees (37,752 records, ~9MB — the one dataset that matters most to keep lazy), Trails (OSM/Overpass) | Static |
| Explore | Heritage Properties, Justthemenu.ca (restaurants) | Static; both went through real geocoding-precision problems, see README's "Known limitations" |
| Transportation | Cameras (511 + YouTube + FAA, see below), Street Signs (22,066 records, filterable by category), Live Flights, Live Ships, Live Buses | Cameras/signs are static-ish (rebuilt by hand); flights/ships/buses are the only three live layers |

### Cameras layer specifically (three source types in one dataset)

`data/cameras/cameras.json` merges three sources, distinguished by a
`source` field, built by `data/cameras/build_cameras.py`:
- `511`: Ontario 511 API pull, embeds a live-reloading snapshot `<img>`.
- `youtube`: hand-curated in `youtube_cams.json`, embeds a YouTube iframe
  (no autoplay). There's no API to discover these — each one has to be
  manually found and verified as an actually-ongoing live stream (not a
  one-off recording) before adding. Searching "Thunder Bay" for more of
  these has twice surfaced results for Alpena, Michigan (also has a
  "Thunder Bay") — always confirm the location, not just the name.
- `faa`: hand-curated in `airport_cams.json`, **link-out only, no embedded
  image**. The API that reveals which FAA WeatherCams image is current is
  behind Akamai bot-detection (confirmed: plain server-side request → 401,
  same request from a loaded browser session → 200). Don't try to work
  around that — it's a deliberate "don't automate this" signal. If asked to
  add more cameras from a site like this, check for bot-protection first
  and default to linking out rather than trying to defeat it.

## Live layers: flights, ships, and buses

All three follow the same pattern because all three hit a direct CORS
block on their data source (OpenSky, AISStream, NextLift's GTFS-RT feed):
1. A GitHub Actions workflow (`.github/workflows/update-*.yml`) runs a
   Python script (`data/flights/fetch_flights.py`,
   `data/ships/fetch_ships.py`, `data/buses/fetch_buses.py`) server-side
   (no CORS there).
2. That script writes `<layer>_live.json`, which the workflow commits and
   pushes back to `main`. **All three use a pull-and-retry loop around
   `git push`, not a bare push** — the three workflows now fire together
   every ~5 minutes (see below), so whichever finishes first moves `main`
   out from under the others; a bare `git push` failed almost every time
   for ships once this went from hours-apart to actually-every-5-minutes.
   If you add a fourth live layer, copy that retry block, not a bare push.
3. index.html fetches that JSON at runtime with `?t=Date.now()` — required,
   not decorative: GitHub Pages' CDN caches static files (`max-age=600`+),
   so without a cache-busting query param the page can serve stale live data
   for several minutes after a new commit. This bit multiple layers once.

**Actual refresh cadence is driven by [`cloudflare-worker/`](cloudflare-worker/),
not by each workflow's own `schedule:` entry.** GitHub doesn't reliably
honor a sub-hourly `schedule:` cron for this repo (see README) — the
Worker's Cron Trigger calls `workflow_dispatch` on all three workflows
every 5 minutes instead, confirmed against real run history. Each
workflow's `schedule:` is just an hourly backstop now. If you add a
fourth live layer, add its workflow filename to `WORKFLOWS` in
`cloudflare-worker/src/index.js` **and tell the user to `npx wrangler
deploy` again** — editing that file alone doesn't redeploy the already-
running Worker.

`ships_live.json` will often be empty — that's correct, not broken (Great
Lakes shipping is seasonal, and AISStream is terrestrial-reception-only, so
it structurally misses vessels a site like MarineTraffic would show via
satellite/roaming AIS). Don't "fix" this by trying to widen the fetch
window indefinitely; there's a real content-vs-cost tradeoff documented in
the README.

`AISSTREAM_API_KEY` is a repo secret — never ask the user to paste it into
chat, never put it in a file. If it's ever missing, ships_live.json's own
`note` field explains why (see fetch_ships.py).

`buses_live.json` needs no API key (NextLift's GTFS-RT feed is anonymous).
Buses are still colored/labeled by route number computed from the number
itself (`routeColor()` in index.html), not looked up from the static
GTFS file's official branding — that file's internal dates are November
2019, checked directly, so its `route_color` field isn't trusted.

`routes.json` (built by `data/buses/build_routes.py`, run manually/
occasionally, not on a schedule) *does* use that same static file, but
only `shapes.txt` joined to `trips.txt` (verified 1:1 shape→route in this
feed) for a reference route-line layer. It's drawn one route at a time,
on click (via the marker's `popupopen`/`popupclose` events in
index.html), not all 17 at once — that was tried first and read as a
tangle of colored lines, not an answer to "where does this bus go."
Disclosed as possibly-outdated in the UI, not presented as current.
`stops.txt`/`stop_times.txt`/
`calendar_dates.txt` are still untouched. If ever asked to add a stops
layer, re-verify that file's currency first (route *numbers* checked out
against the live feed; stop locations have no equivalent live signal to
check against, so don't assume the same confidence carries over). Routes
15, 17, and 18 are live in the Vehicle Positions feed but absent from the
2019 file entirely — concrete evidence it's missing more than just
alignment drift, not just a hedge.

## Deployment workflow

- Static site, no build step: pushing to `main` deploys directly. GitHub
  Pages typically takes 10-40s to pick up a push.
- **Always `git pull origin main --no-edit` before pushing.** The flights
  and ships cron jobs commit to `main` every ~10 minutes; a push without
  pulling first will very often be rejected as non-fast-forward.
- To confirm a specific commit has actually deployed (don't just assume):
  ```bash
  gh api repos/Jandoue/Thunder-Bay/pages/builds/latest -q '.commit + " " + .status'
  ```
  Compare `.commit` against the SHA you just pushed; wait for `.status` to
  read `built`.
- `gh` is not on PATH in the Bash tool's environment on this machine — call
  it via the full path: `"C:\Program Files\GitHub CLI\gh.exe"` (PowerShell
  needs the same treatment).
- **If waiting on a background command** (e.g. polling the Pages build
  status in a loop), do not add an error-swallowing fallback like
  `$(cmd || echo default)` inside the loop condition — if the command is
  silently failing (wrong cwd for a `gh` command that needs repo context,
  auth hiccup, etc.), that fallback hides the failure and the loop spins
  forever instead of erroring. This happened twice in one session. Test the
  exact command once directly before trusting it in a background loop.

## Local testing

`.claude/launch.json` (gitignored) configures `preview_start` to serve the
repo over a real local HTTP server. This matters because `fetch()` of a
relative path is blocked under `file://` — several layers (all the lazy
static ones, plus flights/ships) will silently fail if you just open
`index.html` by double-clicking it. Always test through the preview server,
not by opening the file directly.

When testing a specific data change, prefer temporarily swapping in a small
test fixture (e.g. ships at a few different headings to check icon
rotation) over trusting a JS-dispatched `.click()`/`.dispatchEvent()` on an
element — those bypass real hit-testing and won't catch stacking-order bugs
like the toggle-switch one above. Use `computer` tool clicks at real pixel
coordinates when testing anything about click targets specifically.

## Working conventions this project has established

- **Verify before adding a data source.** Every layer in this repo has been
  checked against the real API/website before being trusted — geocoding
  precision, CORS headers, bot-detection, whether a "live" stream is
  actually ongoing. Don't add a source on the strength of its name or a
  search-result snippet alone.
- **Don't scrape or evade anti-bot protection**, even when technically
  possible (headless-browser session solving, etc.). If a source is
  protected, either find the legitimate access path or degrade gracefully
  (link out, as with the FAA cameras) and say why in the README.
- **Disclose limitations in the UI and README, don't quietly work around
  them.** The "Known limitations" section in README.md is deliberately kept
  as a running record of real mistakes and constraints, not cleaned up
  after the fact. Add to it rather than deleting history from it.
- **Round coordinates to 5 decimal places** for consistency with the rest
  of the data (matches most existing datasets' precision).
- **Rebuild scripts write directly to the canonical `<name>.json`** that
  index.html fetches — no separate "paste this into index.html" step
  anymore. If you add a new layer, follow that pattern (see any
  `build_*.py`/`finalize_*.py` for the shape).
- Commit messages in this repo are detailed and explain *why*, including
  root causes of bugs fixed — match that style rather than writing terse
  one-liners.
