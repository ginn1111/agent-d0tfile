// Shared mock of the 5 tools. Each variant only sets CSS role variables.
document.body.innerHTML = `
<div class="tabs">
  <span class="tab on" data-tab>◇ cindy</span><span class="tab" data-tab>ginb</span><span class="tab" data-tab>gintary</span><span class="tab" data-tab>logs</span>
  <span class="brand">herdr · ${document.title}</span>
</div>
<div class="main">
  <div class="pane agents" data-pane><span class="label">agents</span>
    <div class="row cur"><span>◇ cindy</span><span class="c-green">idle</span></div>
    <div class="row"><span>ginb</span><span class="c-yellow">run</span></div>
    <div class="row"><span>gintary</span><span class="c-dim">off</span></div>
    <div class="row"><span>kanban</span><span class="c-err">2 blk</span></div>
    <br><div class="c-dim">priority</div>
    <div class="row"><span class="c-acc">P0</span><span>1</span></div>
    <div class="row"><span class="c-acc2">P1</span><span>3</span></div>
  </div>
  <div class="pane nvim focus" data-pane><span class="label">nvim · install-tool-theme.sh</span>
    <div class="code" id="code"></div>
    <div class="lualine">
      <span class="bar">▊</span><span class="mode" id="mode">NORMAL</span><span>4.5k</span>
      <span class="fname">install-tool-theme.sh</span><span>87:12</span><span class="c-dim">61%</span>
      <span class="c-err">E1</span><span class="c-yellow">W2</span>
      <span class="spacer"></span><span class="c-cyan">LSP: bashls</span>
      <span class="c-cyan">UTF-8</span><span class="c-yellow">UNIX</span><span class="c-cyan">⎇ main</span>
      <span class="c-green">+12</span><span class="c-yellow">~3</span><span class="c-err">-1</span><span class="bar">▊</span>
    </div>
    <div class="modes c-dim">mode:
      <button data-mode="n">normal</button><button data-mode="i">insert</button>
      <button data-mode="v">visual</button><button data-mode="c">command</button>
    </div>
  </div>
  <div class="pane yazi" data-pane><span class="label">yazi</span>
    <div class="head"><span class="cwd">~/dev/agent-d0tfile/agent-tool-themes/cindy</span></div>
    <div class="cols">
      <div class="col"><div class="f dir hov">cindy</div><div class="f dir">ginb</div><div class="f dir">gintary</div><div class="f">tools.md</div></div>
      <div class="col" id="files"></div>
      <div class="col c-dim" style="padding:2px 8px">[character]<br>success_symbol =<br>&nbsp;<span class="c-acc">"[◇](bold red)"</span><br>error_symbol =<br>&nbsp;<span class="c-err">"[✗](bold magenta)"</span></div>
    </div>
    <div class="status"><span class="ymode" id="ymode">NOR</span><span class="ymode2" id="ymode2">main</span><span style="margin-left:auto;padding:0 8px" class="c-dim">click twice: select</span></div>
  </div>
  <div class="pane" data-pane><span class="label">zsh · starship</span>
    <div class="shell" id="shell"></div>
  </div>
</div>
<div class="status"><span class="strong">◇ Cindy</span><span>herdr 0.9</span><span class="c-green">● 3 agents</span><span>1 board</span><span class="c-yellow">▲ 1 warn</span><span class="c-err">✗ 2 blocked</span><span style="margin-left:auto">22:41</span></div>
<div class="toast" id="toast"></div>`;

const code = [
  ['c-dim', '# Herdr config holds keys/session settings too.'],
  ['', '<span class="c-green">merge_herdr</span>() {'],
  ['', '  <span class="c-green">local</span> src=<span class="c-cyan">"$SRC_DIR/herdr.toml"</span>'],
  ['', '  [[ -f <span class="c-cyan">"$src"</span> ]] || <span class="c-green">return</span> <span class="c-orange">0</span>'],
  ['', '  <span class="c-green">if</span> [[ <span class="c-cyan">"$MODE"</span> == <span class="c-cyan">"list"</span> ]]; <span class="c-green">then</span>'],
  ['cur', '    <span class="c-blue">printf</span> <span class="c-cyan">\'merge   %s\\n\'</span> <span class="c-cyan">"$<span class="hit">dest</span>"</span>'],
  ['', '  <span class="c-green">fi</span>'],
  ['', '  tmp=$(<span class="c-blue">mktemp</span> <span class="c-cyan">"${<span class="hit">dest</span>}.XXXXXX"</span>)'],
  ['', '  <span class="c-blue">awk</span> -v frag=<span class="c-cyan">"$src"</span> <span class="c-cyan">\'...\'</span>'],
  ['', '}'],
  ['c-dim', ''],
  ['', '<span class="c-blue">link_file</span> yazi-theme.toml <span class="c-cyan">"$CONFIG_HOME/yazi/theme.toml"</span>'],
  ['', '<span class="c-blue">link_file</span> starship.toml <span class="c-cyan">"$CONFIG_HOME/starship.toml"</span>'],
];
document.getElementById('code').innerHTML = code.map(([k, t], i) =>
  `<div class="${k === 'cur' ? 'cur-line' : k}"><span class="ln">${i + 82}</span>${t}</div>`).join('');

const files = ['nvim/', 'herdr.toml', 'starship.toml', 'yazi-theme.toml', 'README.md'];
let hov = 2; const sel = new Set();
function drawFiles() {
  document.getElementById('files').innerHTML = files.map((f, i) =>
    `<div class="f ${f.endsWith('/') ? 'dir' : ''} ${i === hov ? 'hov' : ''} ${sel.has(i) ? 'sel' : ''}" data-f="${i}">${f}</div>`).join('');
}
drawFiles();
document.getElementById('files').addEventListener('click', e => {
  const i = +e.target.closest('[data-f]')?.dataset.f; if (isNaN(i)) return;
  if (i === hov) sel.has(i) ? sel.delete(i) : sel.add(i); hov = i; drawFiles();
  document.getElementById('ymode').textContent = sel.size ? 'SEL' : 'NOR';
  document.body.classList.toggle('ysel', sel.size > 0);
});

const shellLines = [];
function prompt(ok, cmd, out) {
  shellLines.push(`<div><span class="prompt-dir">agent-d0tfile</span> <span class="c-yellow">⎇ main</span> <span class="c-orange">!?</span> <span class="sym ${ok ? '' : 'bad'}">${ok ? '◇' : '✗'}</span> ${cmd}</div>` + (out ? `<div class="c-dim">${out}</div>` : ''));
  while (shellLines.length > 4) shellLines.shift();
  document.getElementById('shell').innerHTML = shellLines.join('') +
    `<div><span class="prompt-dir">agent-d0tfile</span> <span class="c-yellow">⎇ main</span> <span class="sym ${ok ? '' : 'bad'}">${ok ? '◇' : '✗'}</span> <span class="c-dim">▏</span></div>
     <div class="actions"><button id="ok">run make itt-dry-run</button><button id="bad">run failing cmd</button></div>`;
  document.getElementById('ok').onclick = () => prompt(true, 'make itt-dry-run', 'merge   ~/.config/herdr/config.toml [theme]');
  document.getElementById('bad').onclick = () => prompt(false, 'make itt TOOL_THEME=nope', 'Theme not found: agent-tool-themes/nope');
}
prompt(true, 'make itt-dry-run TOOL_THEME=cindy', 'link    yazi-theme.toml -> ~/.config/yazi/theme.toml');

const modeName = { n: 'NORMAL', i: 'INSERT', v: 'VISUAL', c: 'COMMAND' };
document.querySelectorAll('[data-mode]').forEach(b => b.onclick = e => {
  e.stopPropagation();
  const m = b.dataset.mode;
  document.documentElement.style.setProperty('--mode', `var(--mode-${m})`);
  document.getElementById('mode').textContent = modeName[m];
});
document.querySelectorAll('[data-pane]').forEach(p => p.onclick = () => {
  document.querySelectorAll('[data-pane]').forEach(q => q.classList.remove('focus')); p.classList.add('focus');
});
document.querySelectorAll('[data-tab]').forEach(t => t.onclick = () => {
  document.querySelectorAll('[data-tab]').forEach(q => q.classList.remove('on')); t.classList.add('on');
  const toast = document.getElementById('toast'); toast.textContent = 'switched to ' + t.textContent;
  toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 1200);
});
