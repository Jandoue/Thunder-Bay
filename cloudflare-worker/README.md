# Live-data dispatcher (Cloudflare Worker)

Fires GitHub's `workflow_dispatch` API for `update-flights.yml`,
`update-ships.yml`, and `update-buses.yml` on a 5-minute [Cron Trigger](https://developers.cloudflare.com/workers/configuration/cron-triggers/).
GitHub's own `schedule:` cron doesn't reliably run at the interval it's
given for this repo (see the main [README](../README.md)) — this Worker is
what actually keeps live data fresh now; the workflows' own `schedule:`
entries are just an hourly backstop in case this Worker is ever down.

It does nothing else: no data processing, no state, no public write access.
`src/index.js` is the whole thing.

## One-time setup

1. **Generate a GitHub token** — a fine-grained personal access token, not a
   classic one:
   - github.com → Settings → Developer settings → Personal access tokens →
     Fine-grained tokens → Generate new token
   - Repository access: only `Jandoue/Thunder-Bay`
   - Permissions: **Actions → Read and write** (nothing else — it only ever
     calls the dispatch endpoint)
   - Pick an expiration you're comfortable renewing (e.g. 1 year); when it
     expires the Worker starts failing loudly (see Logs below), not
     silently

2. **Deploy the Worker:**
   ```bash
   cd cloudflare-worker
   npm install
   npx wrangler login                    # opens a browser to authorize your Cloudflare account
   npx wrangler secret put GITHUB_TOKEN  # paste the token from step 1 when prompted
   npx wrangler deploy
   ```
   The token is stored as an encrypted Worker secret by Cloudflare — it
   isn't written to any file in this repo and Claude never sees the value.

3. **Confirm it's actually running.** Give it 10–15 minutes, then check that
   new runs are showing up roughly every 5 minutes with `event:
   workflow_dispatch`:
   ```bash
   "C:\Program Files\GitHub CLI\gh.exe" run list --workflow=update-flights.yml --repo Jandoue/Thunder-Bay --limit 8
   ```

## Ongoing

- **Logs:** `npx wrangler tail` while it's deployed, or Cloudflare dashboard
  → Workers & Pages → this worker → Logs. A failed dispatch logs the HTTP
  status and response body from GitHub's API.
- **If the token is ever compromised or just expires:** revoke/replace it
  from GitHub's token settings page, then `npx wrangler secret put
  GITHUB_TOKEN` again with the new value. Until then the Worker keeps
  firing every 5 minutes and failing every time — visible in the logs above,
  not silent — and the workflows fall back to their hourly `schedule:`
  backstop in the meantime.
