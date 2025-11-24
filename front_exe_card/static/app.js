document.addEventListener('DOMContentLoaded', () => {
  const grid = GridStack.init({
    cellHeight: 120,
    margin: 0,
    float: true,
    column: 12,
    disableOneColumnMode: true,
    resizable: { handles: 'e, se, s, sw, w, ne, n, nw' }
  });

  function updateGridBackground() {
    document.documentElement.style.setProperty('--cell', grid.opts.cellHeight + 'px');
    const first = grid.el.querySelector('.grid-stack-item');
    let colW;
    if (first) {
      const w = parseInt(first.getAttribute('gs-w') || '1', 10) || 1;
      const bw = first.getBoundingClientRect().width;
      colW = Math.round(bw / w);
    } else {
      colW = Math.round(grid.el.clientWidth / grid.opts.column);
    }
    document.documentElement.style.setProperty('--col', colW + 'px');
  }
  updateGridBackground();
  window.addEventListener('resize', updateGridBackground);

  function serializeLayout() {
    const items = [];
    grid.engine.nodes.forEach(n => {
      const url = n.el?.querySelector('iframe')?.src || '';
      const card = n.el?.querySelector('.card');
      const collapsed = card?.classList.contains('collapsed') || false;
      const mode = card?.dataset.mode || 'in';
      const home = card?.dataset.home || url;
      const current = card?.dataset.current || url;
      const title = card?.dataset.title || '';
      const zoom = parseFloat(card?.dataset.zoom || '1');
      const titleColor = card?.dataset.titleColor || '';
      const loader = card?.dataset.loader || 'proxy';
      const scroll = card?.dataset.scroll || 'hide';
      items.push({ id: n.id || undefined, x: n.x, y: n.y, w: n.w, h: n.h, url: current, home, mode, collapsed, title, zoom, titleColor, loader, scroll });
    });
    const theme = window.currentTheme;
    return { cellHeight: grid.opts.cellHeight, margin: grid.opts.margin, headerCollapsed: false, locked: grid._isStatic || false, items, theme };
  }

  async function saveLayout() {
    try {
      await fetch('/api/layout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(serializeLayout()) });
    } catch (e) {}
  }

  function addWidget(url, pos) {
    const el = document.createElement('div');
    el.className = 'grid-stack-item';
    const w = pos?.w ?? 4, h = pos?.h ?? 4, x = pos?.x, y = pos?.y;
    if (x != null) el.setAttribute('gs-x', String(x));
    if (y != null) el.setAttribute('gs-y', String(y));
    el.setAttribute('gs-w', String(w));
    el.setAttribute('gs-h', String(h));
    if (x == null || y == null) el.setAttribute('gs-auto-position', 'true');

    const content = document.createElement('div');
    content.className = 'grid-stack-item-content card';
    content.dataset.mode = pos?.mode || 'in';
    content.dataset.home = pos?.home || url;
    content.dataset.current = pos?.url || url;
    content.dataset.zoom = (pos?.zoom != null ? String(pos.zoom) : '1');
    content.dataset.titleColor = pos?.titleColor || '';
    content.dataset.loader = pos?.loader || 'proxy';
    content.dataset.scroll = pos?.scroll || 'hide';
    let history = [content.dataset.current];
    let historyIndex = 0;

    const bar = document.createElement('div');
    bar.className = 'card-bar';
    const titleWrap = document.createElement('div');
    titleWrap.className = 'title-wrap';
    const titleText = document.createElement('div');
    titleText.className = 'title';
    titleText.textContent = (pos?.title ? pos.title : (() => { try { return new URL(content.dataset.current).hostname } catch { return content.dataset.current } })());
    content.dataset.title = titleText.textContent;
    content.dataset.titleCustom = (pos?.title ? '1' : '0');
    if (content.dataset.titleColor) titleText.style.background = content.dataset.titleColor;
    const titleInput = document.createElement('input');
    titleInput.className = 'title-input';
    titleInput.type = 'text';
    titleInput.value = content.dataset.title;
    titleInput.style.width = '160px';
    titleWrap.appendChild(titleText);
    const inputsWrap = document.createElement('div');
    inputsWrap.className = 'inputs hidden';
    const urlSpan = document.createElement('div');
    urlSpan.className = 'url';
    urlSpan.textContent = content.dataset.current;
    const actions = document.createElement('div');
    actions.className = 'actions';
    const toggleBtn = document.createElement('button');
    toggleBtn.textContent = (pos?.collapsed ? '展开' : '收起');
    const urlInput = document.createElement('input');
    urlInput.type = 'text';
    urlInput.placeholder = '输入链接并回车';
    urlInput.style.width = '220px';
    urlInput.value = content.dataset.current;
    const goBtn = document.createElement('button');
    goBtn.textContent = '跳转';
    const backBtn = document.createElement('button');
    backBtn.textContent = '后退';
    const homeBtn = document.createElement('button');
    homeBtn.textContent = '主页';
    const modeSel = document.createElement('select');
    modeSel.innerHTML = '<option value="in">组件内</option><option value="out">外部浏览器</option>';
    modeSel.value = content.dataset.mode;
    const loaderSel = document.createElement('select');
    loaderSel.innerHTML = '<option value="direct">直接</option><option value="proxy">代理</option>';
    loaderSel.value = content.dataset.loader;
    const scrollSel = document.createElement('select');
    scrollSel.innerHTML = '<option value="show">显示滚动条</option><option value="hide">隐藏滚动条</option>';
    scrollSel.value = content.dataset.scroll;
    const fwdBtn = document.createElement('button');
    fwdBtn.textContent = '前进';
    const editToggle = document.createElement('button');
    editToggle.textContent = '编辑';
    const closeBtn = document.createElement('button');
    closeBtn.className = 'danger';
    closeBtn.textContent = '删除';
    actions.appendChild(editToggle);
    actions.appendChild(toggleBtn);
    actions.appendChild(backBtn);
    actions.appendChild(homeBtn);
    actions.appendChild(closeBtn);
    inputsWrap.appendChild(urlInput);
    inputsWrap.appendChild(goBtn);
    inputsWrap.appendChild(modeSel);
    inputsWrap.appendChild(loaderSel);
    inputsWrap.appendChild(scrollSel);
    const zoomSel = document.createElement('input');
    zoomSel.type = 'range';
    zoomSel.min = '0.5';
    zoomSel.max = '2';
    zoomSel.step = '0.05';
    zoomSel.value = content.dataset.zoom;
    const zoomLabel = document.createElement('span');
    zoomLabel.textContent = Math.round(parseFloat(zoomSel.value) * 100) + '%';
    const titleColorSel = document.createElement('input');
    titleColorSel.type = 'color';
    titleColorSel.value = content.dataset.titleColor || '#1677ff';
    inputsWrap.appendChild(zoomSel);
    inputsWrap.appendChild(zoomLabel);
    inputsWrap.appendChild(titleColorSel);
    inputsWrap.appendChild(fwdBtn);
    inputsWrap.appendChild(urlSpan);
    bar.appendChild(titleWrap);
    bar.appendChild(inputsWrap);
    bar.appendChild(actions);

    const body = document.createElement('div');
    body.className = 'card-body';
    const scaleWrap = document.createElement('div');
    scaleWrap.className = 'scale-wrap';
    const iframe = document.createElement('iframe');
    iframe.src = content.dataset.current;
    iframe.setAttribute('allow', 'fullscreen');
    iframe.setAttribute('sandbox', 'allow-forms allow-modals allow-popups allow-pointer-lock allow-scripts allow-same-origin');
    scaleWrap.appendChild(iframe);
    body.appendChild(scaleWrap);

    content.appendChild(bar);
    content.appendChild(body);
    el.appendChild(content);

    grid.addWidget(el);
    if (pos?.collapsed) content.classList.add('collapsed');

    function setEditing(on) {
      inputsWrap.classList.toggle('hidden', !on);
      if (on) {
        if (!titleWrap.contains(titleInput)) titleWrap.appendChild(titleInput);
        editToggle.textContent = '完成';
        titleText.style.display = 'none';
      } else {
        editToggle.textContent = '编辑';
        titleText.style.display = '';
        if (titleWrap.contains(titleInput)) titleWrap.removeChild(titleInput);
      }
    }
    editToggle.addEventListener('click', () => {
      const on = inputsWrap.classList.contains('hidden');
      setEditing(on);
    });
    titleInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        content.dataset.title = titleInput.value.trim() || titleText.textContent;
        titleText.textContent = content.dataset.title;
        content.dataset.titleCustom = '1';
        setEditing(false);
        saveLayout();
      }
    });

    toggleBtn.addEventListener('click', () => {
      const collapsed = content.classList.toggle('collapsed');
      toggleBtn.textContent = collapsed ? '展开' : '收起';
      saveLayout();
    });
    function navigateTo(targetUrl, push=true) {
      const useProxy = loaderSel.value === 'proxy';
      const hide = scrollSel.value === 'hide';
      iframe.src = useProxy ? ('/proxy?url=' + encodeURIComponent(targetUrl) + (hide ? '&hide_scroll=1' : '')) : targetUrl;
      content.dataset.current = targetUrl;
      urlSpan.textContent = targetUrl;
      urlInput.value = targetUrl;
      if (push) {
        if (history[history.length-1] !== targetUrl) {
          history.push(targetUrl);
        }
        historyIndex = history.length - 1;
      }
      saveLayout();
    }
    function updateTitleByUrl() {
      if (content.dataset.titleCustom === '1') {
        titleText.textContent = content.dataset.title;
        return;
      }
      try { content.dataset.title = new URL(content.dataset.current).hostname } catch { content.dataset.title = content.dataset.current }
      titleText.textContent = content.dataset.title;
    }
    urlInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const u = urlInput.value.trim();
        if (!u) return;
        if (modeSel.value === 'out') window.open(u, '_blank'); else navigateTo(u, true);
        updateTitleByUrl();
      }
    });
    goBtn.addEventListener('click', () => {
      const u = urlInput.value.trim();
      if (!u) return;
      if (modeSel.value === 'out') window.open(u, '_blank'); else navigateTo(u, true);
      updateTitleByUrl();
    });
    backBtn.addEventListener('click', () => {
      if (historyIndex > 0) {
        historyIndex -= 1;
        navigateTo(history[historyIndex], false);
      }
    });
    fwdBtn.addEventListener('click', () => {
      if (historyIndex < history.length - 1) {
        historyIndex += 1;
        navigateTo(history[historyIndex], false);
      }
    });
    homeBtn.addEventListener('click', () => {
      const u = content.dataset.home || content.dataset.current;
      navigateTo(u, true);
      updateTitleByUrl();
    });
    modeSel.addEventListener('change', () => {
      content.dataset.mode = modeSel.value;
      saveLayout();
    });
    loaderSel.addEventListener('change', () => { content.dataset.loader = loaderSel.value; saveLayout(); navigateTo(content.dataset.current, false); });
    scrollSel.addEventListener('change', () => { content.dataset.scroll = scrollSel.value; saveLayout(); navigateTo(content.dataset.current, false); });
    function applyZoom(val) {
      const z = parseFloat(val || '1');
      scaleWrap.style.transform = `scale(${z})`;
      scaleWrap.style.width = `calc(100% / ${z})`;
      scaleWrap.style.height = `calc(100% / ${z})`;
      iframe.style.width = '100%';
      iframe.style.height = '100%';
    }
    applyZoom(content.dataset.zoom);
    closeBtn.addEventListener('click', () => { grid.removeWidget(el); saveLayout(); });

    zoomSel.addEventListener('input', () => {
      content.dataset.zoom = zoomSel.value;
      zoomLabel.textContent = Math.round(parseFloat(zoomSel.value) * 100) + '%';
      applyZoom(zoomSel.value);
      saveLayout();
    });
    titleColorSel.addEventListener('input', () => {
      content.dataset.titleColor = titleColorSel.value;
      titleText.style.background = content.dataset.titleColor;
      saveLayout();
    });

    saveLayout();
  }

  document.getElementById('addBtn').addEventListener('click', () => {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) return;
    addWidget(url);
    document.getElementById('urlInput').value = '';
  });

  document.getElementById('urlInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('addBtn').click();
  });

  grid.on('change', () => { saveLayout(); });
  grid.on('dragstop', () => { saveLayout(); });
  grid.on('resizestop', () => { saveLayout(); updateGridBackground(); });

  const THEMES = {
    light: { primary: '#1677ff', bg: '#f7f8fa', card: '#ffffff', grid: '#eaeaea', text: '#1f1f1f' },
    dark: { primary: '#4096ff', bg: '#141414', card: '#1f1f1f', grid: '#303030', text: '#e8e8e8' },
    blue: { primary: '#1554F6', bg: '#eef3ff', card: '#ffffff', grid: '#cfd7ff', text: '#0b1b47' }
  };
  window.currentTheme = { mode: 'light', ...THEMES.light };
  function applyTheme(theme) {
    const t = { ...THEMES[theme.mode || 'light'] };
    window.currentTheme = { mode: theme.mode || 'light', ...t };
    for (const [k, v] of Object.entries(t)) document.documentElement.style.setProperty(`--${k}`, v);
  }
  document.getElementById('themeSelect').addEventListener('change', (e) => {
    applyTheme({ mode: e.target.value });
    saveLayout();
  });

  function applyLock(locked) {
    if (typeof grid.setStatic === 'function') grid.setStatic(locked);
    else {
      if (grid.enableMove) grid.enableMove(!locked);
      if (grid.enableResize) grid.enableResize(!locked);
    }
    const addBtn = document.getElementById('addBtn');
    addBtn.disabled = !!locked;
    addBtn.style.opacity = locked ? '0.6' : '1';
    const lockBtn = document.getElementById('lockBtn');
    lockBtn.textContent = locked ? '解锁布局' : '锁定布局';
    window.__locked = !!locked;
  }
  document.getElementById('lockBtn').addEventListener('click', () => {
    const isLocked = !!window.__locked;
    applyLock(!isLocked);
    saveLayout();
  });

  async function loadLayout() {
    try {
      const res = await fetch('/api/layout');
      const data = await res.json();
      if (data.cellHeight) {
        grid.opts.cellHeight = data.cellHeight;
        document.documentElement.style.setProperty('--cell', data.cellHeight + 'px');
      }
      if (data.margin != null) grid.opts.margin = data.margin;
      updateGridBackground();
      (data.items || []).forEach(item => addWidget(item.url, item));
      applyTheme(data.theme || { mode: 'light' });
      document.getElementById('themeSelect').value = (data.theme?.mode || 'light');
      applyLock(!!data.locked);
    } catch (e) {}
  }

  loadLayout();
});
