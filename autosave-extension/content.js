let lastSent = "";
function extractCreds(root){
  const pass = root.querySelector && root.querySelector("input[type='password']");
  if(!pass) return null;
  let user = null;
  const candidates = root.querySelectorAll
    ? root.querySelectorAll("input[type='text'], input[type='email'], input[name*='user'], input[name*='email'], input[id*='user'], input[id*='email']")
    : [];
  for(const el of candidates){
    const t = (el.getAttribute('type')||'').toLowerCase();
    if(t==='hidden' || el.disabled) continue;
    if((el.value||'').trim()){
      user = el;
      break;
    }
    user = user || el;
  }
  if(!user) return null;
  return { user, pass };
}
async function send(site, username, password){
  const key = `${site}|${username}|${password}`;
  if(key===lastSent) return;
  lastSent = key;
  try{
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      await new Promise((resolve)=> {
        try{
          chrome.runtime.sendMessage({ type: 'vaultSave', site, username, password }, ()=>{
            resolve();
          });
        }catch(e){ resolve(); }
      });
    } else {
      // Fallback (may be blocked by CSP)
      await fetch("http://127.0.0.1:5000/save",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({site,username,password})
      });
    }
  }catch(e){}
}
function attachToForm(form){
  if(!form || form.__vaultHooked) return;
  form.__vaultHooked = true;
  const handler = ()=> {
    try{
      const creds = extractCreds(form);
      if(!creds) return;
      const u = (creds.user.value||'').trim();
      const p = (creds.pass.value||'').trim();
      if(!u || !p) return;
      send(location.hostname, u, p);
    }catch(e){}
  };
  form.addEventListener("submit", handler, true);
  try{
    const creds = extractCreds(form);
    if(creds && creds.pass){
      creds.pass.addEventListener('keydown', (ev)=>{
        if(ev && (ev.key==='Enter' || ev.keyCode===13)){
          setTimeout(handler, 0);
        }
      }, true);
    }
    const btns = form.querySelectorAll("button, input[type='submit']");
    btns.forEach(b=>{
      b.addEventListener('click', ()=> setTimeout(handler, 0), true);
    });
  }catch(e){}
}
function setupAutoSave(){
  try{
    document.querySelectorAll("form").forEach(attachToForm);
    const obs = new MutationObserver((muts)=>{
      for(const m of muts){
        m.addedNodes && m.addedNodes.forEach(n=>{
          try{
            if(n && n.querySelectorAll){
              n.querySelectorAll("form").forEach(attachToForm);
              // also attach to standalone password fields (non-form flows)
              const p = n.querySelector("input[type='password']");
              if(p){
                const fakeForm = document.createElement('form');
                if(p.parentElement) fakeForm.appendChild(p.cloneNode(false));
                attachToForm(fakeForm);
              }
            }
          }catch(e){}
        });
      }
    });
    obs.observe(document.documentElement || document.body, { childList:true, subtree:true });
    document.addEventListener('submit', (ev)=>{
      try{
        const f = ev.target;
        if(f && f.tagName==='FORM') attachToForm(f);
      }catch(e){}
    }, true);
  }catch(e){}
}
setupAutoSave();
