/**
 * Fires GitHub's workflow_dispatch API for the civic map's live-data
 * workflows on a Cron Trigger, because GitHub's own `schedule:` trigger
 * doesn't reliably honor a sub-hourly cron for this repo -- observed
 * running 1.5 to 4.5+ hours apart despite a 10-minute cron (see the main
 * README's "Why flights and ships are architecturally different"). An
 * explicit workflow_dispatch call isn't subject to that same low-priority
 * queue, so this Worker's Cron Trigger is the real clock now; the
 * workflows' own `schedule:` entries are left in only as an hourly
 * backstop in case this Worker is ever down.
 */

const REPO = 'Jandoue/Thunder-Bay';
const WORKFLOWS = ['update-flights.yml', 'update-ships.yml', 'update-buses.yml'];

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(Promise.all(WORKFLOWS.map(wf => dispatch(wf, env))));
  },

  async fetch() {
    return new Response(
      'Thunder Bay live-data dispatcher. Runs on a Cron Trigger (see wrangler.toml) -- nothing to see at this URL.',
      { status: 200 }
    );
  },
};

async function dispatch(workflowFile, env) {
  const res = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/${workflowFile}/dispatches`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'thunder-bay-civic-map-dispatcher',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ref: 'main' }),
    }
  );
  if (!res.ok) {
    console.error(`dispatch failed for ${workflowFile}: HTTP ${res.status} ${await res.text()}`);
  } else {
    console.log(`dispatched ${workflowFile}`);
  }
}
