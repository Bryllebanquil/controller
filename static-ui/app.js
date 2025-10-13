(function(){
  const root = document.documentElement;
  const state = {
    theme: localStorage.getItem('neural-control-hub-theme') || 'system',
    activeTab: 'overview',
    subTab: 'terminal',
    agents: [],
    selectedAgentId: null,
    commandHistory: [],
  };

  // Theme handling
  function applyTheme(theme){
    if(theme === 'system'){
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', prefersDark);
    } else {
      root.classList.toggle('dark', theme === 'dark');
    }
  }
  function setTheme(theme){
    state.theme = theme;
    localStorage.setItem('neural-control-hub-theme', theme);
    applyTheme(theme);
    const label = document.querySelector('#themeBtn .label');
    if(label){ label.textContent = theme === 'system' ? 'Auto' : (theme[0].toUpperCase()+theme.slice(1)); }
  }
  applyTheme(state.theme);

  // Theme menu interactions
  const themeBtn = document.getElementById('themeBtn');
  const themeMenu = document.getElementById('themeMenu');
  if(themeBtn && themeMenu){
    themeBtn.addEventListener('click', () => {
      themeMenu.classList.toggle('hidden');
    });
    themeMenu.addEventListener('click', (e)=>{
      const t = e.target.closest('[data-theme]');
      if(!t) return;
      setTheme(t.getAttribute('data-theme'));
      themeMenu.classList.add('hidden');
    });
    document.addEventListener('click',(e)=>{
      if(!themeMenu.contains(e.target) && !themeBtn.contains(e.target)){
        themeMenu.classList.add('hidden');
      }
    });
  }

  // Sidebar toggle (mobile)
  const sidebar = document.getElementById('sidebar');
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  if(mobileMenuBtn && sidebar){
    mobileMenuBtn.addEventListener('click', ()=>{
      sidebar.classList.toggle('open');
    });
  }

  // Tabs handling
  function activateTab(tab){
    state.activeTab = tab;
    document.querySelectorAll('.tabs .tab').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
    });
    document.querySelectorAll('.tab-content').forEach(section => {
      section.classList.toggle('active', section.getAttribute('data-tab') === tab);
    });
    document.querySelectorAll('.nav .nav-item, .sidebar-footer .nav-item').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
    });
    if(window.innerWidth < 768 && sidebar){ sidebar.classList.remove('open'); }
  }
  document.querySelectorAll('[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => activateTab(btn.getAttribute('data-tab')));
  });
  activateTab('overview');

  // Nested tabs (commands)
  function activateSubTab(sub){
    state.subTab = sub;
    document.querySelectorAll('#commandsTabs .tab').forEach(btn=>{
      btn.classList.toggle('active', btn.getAttribute('data-subtab') === sub);
    });
    document.querySelectorAll('.tab-subcontent').forEach(section=>{
      section.style.display = section.getAttribute('data-subtab') === sub ? 'block' : 'none';
    });
  }
  document.querySelectorAll('#commandsTabs .tab').forEach(btn=>{
    btn.addEventListener('click', ()=> activateSubTab(btn.getAttribute('data-subtab')));
  });
  activateSubTab('terminal');

  // Mock data to mirror structure
  function seedAgents(){
    const platforms = ['Windows','Linux','macOS'];
    const statuses = ['online','offline'];
    state.agents = Array.from({length: 8}).map((_,i)=>({
      id: 'agent-'+(i+1),
      name: 'Agent '+(i+1),
      platform: platforms[i%3],
      status: statuses[i%2],
    }));
    renderAgents();
  }

  function renderAgents(){
    const grid = document.getElementById('agentsGrid');
    const empty = document.getElementById('agentsEmpty');
    const onlineCount = state.agents.filter(a=>a.status==='online').length;
    document.getElementById('stat-online-agents').textContent = String(onlineCount);
    document.getElementById('stat-total-agents').textContent = String(state.agents.length);
    if(!grid) return;
    const query = (document.getElementById('agentSearch')?.value||'').toLowerCase();
    const items = state.agents.filter(a=>
      a.name.toLowerCase().includes(query) ||
      a.id.toLowerCase().includes(query) ||
      a.platform.toLowerCase().includes(query)
    );
    grid.innerHTML = '';
    items.forEach(agent=>{
      const el = document.createElement('div');
      el.className = 'card';
      el.innerHTML = `
        <div class="card-header">
          <div class="card-title">${agent.name}</div>
          <span class="badge">${agent.status==='online'?'Online':'Offline'}</span>
        </div>
        <div class="card-body">
          <div class="muted text-xs">${agent.platform} • ${agent.id}</div>
        </div>
      `;
      grid.appendChild(el);
    });
    empty.classList.toggle('hidden', items.length !== 0);
  }

  const agentSearch = document.getElementById('agentSearch');
  if(agentSearch){ agentSearch.addEventListener('input', renderAgents); }
  seedAgents();

  // Activity feed (mock)
  const feed = document.getElementById('activityFeed');
  if(feed){
    const append = (text)=>{
      const item = document.createElement('div');
      item.className = 'feed-item';
      item.textContent = text;
      feed.prepend(item);
    };
    ['Controller connected','Agent 1 registered','Ping broadcast sent','Agent 2 offline']
      .forEach(append);
    setInterval(()=>{
      const ts = new Date().toLocaleTimeString();
      append(`[${ts}] Heartbeat OK`);
    }, 4000);
  }

  // Terminal mock
  const termInput = document.getElementById('terminalInput');
  const termRun = document.getElementById('terminalRun');
  const termOut = document.getElementById('terminalOutput');
  function runCommand(){
    const cmd = (termInput?.value||'').trim();
    if(!cmd) return;
    state.commandHistory.push(cmd);
    const line = document.createElement('div');
    line.textContent = `$ ${cmd}`;
    termOut.appendChild(line);
    const res = document.createElement('div');
    res.className = 'muted';
    res.textContent = 'Command executed (static mock)';
    termOut.appendChild(res);
    termOut.scrollTop = termOut.scrollHeight;
    termInput.value = '';
    const total = document.getElementById('stat-commands');
    if(total){ total.textContent = String(state.commandHistory.length); }
  }
  if(termRun){ termRun.addEventListener('click', runCommand); }
  if(termInput){ termInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter') runCommand(); }); }

  // Throughput mock
  const throughput = document.getElementById('metric-throughput');
  if(throughput){
    setInterval(()=>{
      const v = (Math.random()*2).toFixed(1);
      throughput.textContent = `${v} MB/s`;
    }, 2000);
  }
})();


