chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      if (message && message.type === 'vaultSave') {
        const { site, username, password } = message;
        if (!site || !username || !password) {
          sendResponse({ ok: false, error: 'missing-fields' });
          return;
        }
        const resp = await fetch('http://127.0.0.1:5000/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ site, username, password }),
          cache: 'no-store',
          mode: 'cors',
        });
        sendResponse({ ok: resp.ok });
        return;
      }
      sendResponse({ ok: false, error: 'unknown-message' });
    } catch (e) {
      try {
        sendResponse({ ok: false, error: String(e && e.message || e) });
      } catch (_) {}
    }
  })();
  return true; // async sendResponse
});
