// Zürich Taxi Radar — разписания по вид транспорт
//
// Едно табло обслужва четирите бутона. Швейцарският API връща всичко
// от един endpoint с поле `category`, затова тук няма четири отделни
// реализации — има един панел и филтър, който се сменя.
//
// Данните идват от data/transport.json (пълни се от scripts/fetch_transport.py).
(function(){
  'use strict';

  var KINDS = {
    train: { icon:'🚂', title:'Trains',          bottom:240 },
    tram:  { icon:'🚊', title:'Trams',           bottom:296 },
    bus:   { icon:'🚌', title:'Buses',           bottom:352 },
    intl:  { icon:'🌍', title:'Intl. coaches',   bottom:408 }
  };

  var STATIONS = {
    hb:'Zürich HB', oerlikon:'Oerlikon', stadelhofen:'Stadelhofen',
    airport:'Flughafen', quai:'Bahnhofquai', sihlquai:'Sihlquai'
  };

  var DATA = null, open = null, loading = false;

  function css(){
    if(document.getElementById('tp-css')) return;
    var s = document.createElement('style');
    s.id = 'tp-css';
    s.textContent = [
      '.tp-btn{position:fixed;right:12px;width:48px;height:48px;border-radius:16px;',
      'padding:0;border:0;display:flex;align-items:center;justify-content:center;',
      'font-size:22px;line-height:1;color:var(--text);background:var(--glass);',
      'box-shadow:0 6px 18px rgba(15,27,45,.20),0 1px 0 rgba(255,255,255,.75) inset,',
      '0 0 0 1px var(--glass-edge);backdrop-filter:saturate(180%) blur(16px);',
      '-webkit-backdrop-filter:saturate(180%) blur(16px);z-index:2400;cursor:pointer;',
      'transition:transform .16s ease}',
      '.tp-btn:active{transform:scale(.9)}',
      '.tp-btn.on{color:var(--cyan);box-shadow:0 6px 18px rgba(15,27,45,.20),0 0 0 2px var(--cyan)}',
      'body.theme-night .tp-btn{box-shadow:0 6px 20px rgba(0,0,0,.55),',
      '0 1px 0 rgba(255,255,255,.08) inset,0 0 0 1px rgba(34,211,238,.45)}',
      'body.list-view .tp-btn{display:none}',
      '#tp-panel{display:none;position:fixed;left:8px;right:8px;bottom:12px;z-index:2500;',
      'max-height:52vh;overflow-y:auto;overscroll-behavior:contain;',
      'background:var(--glass);border:1px solid var(--glass-edge);border-radius:18px;',
      'backdrop-filter:saturate(180%) blur(18px);-webkit-backdrop-filter:saturate(180%) blur(18px);',
      'box-shadow:0 18px 50px rgba(15,27,45,.22)}',
      '#tp-panel.on{display:block}',
      '.tp-head{position:sticky;top:0;z-index:2;display:flex;align-items:center;gap:10px;',
      'padding:11px 14px;background:var(--glass);backdrop-filter:saturate(180%) blur(18px);',
      'border-bottom:1px solid var(--glass-edge);border-radius:18px 18px 0 0;',
      "font:800 15px 'Courier New',monospace;color:var(--cyan);letter-spacing:1px}",
      '.tp-head .tp-x{margin-left:auto;cursor:pointer;color:var(--muted);font-size:18px;padding:0 4px}',
      '.tp-stamp{font-size:11px;color:var(--muted);font-weight:400;letter-spacing:0}',
      '.tp-row{display:flex;align-items:center;gap:10px;padding:9px 14px;',
      'border-bottom:1px solid var(--glass-edge)}',
      '.tp-row:last-child{border-bottom:none}',
      ".tp-t{font:700 15px 'Courier New',monospace;color:var(--amber);min-width:48px}",
      '.tp-line{font-weight:800;font-size:14px;min-width:42px;color:var(--text)}',
      '.tp-to{flex:1;font-size:14px;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
      '.tp-st{font-size:11px;color:var(--muted);display:block;margin-top:1px}',
      '.tp-plat{font-size:12px;color:var(--muted);min-width:26px;text-align:right}',
      '.tp-late{color:var(--red);font-size:12px;font-weight:700;margin-left:4px}',
      '.tp-empty{padding:22px 16px;text-align:center;color:var(--muted);font-size:14px;line-height:1.6}'
    ].join('');
    document.head.appendChild(s);
  }

  function mkButtons(){
    Object.keys(KINDS).forEach(function(k){
      if(document.getElementById('tp-' + k)) return;
      var b = document.createElement('button');
      b.id = 'tp-' + k;
      b.className = 'tp-btn';
      b.style.bottom = KINDS[k].bottom + 'px';
      b.textContent = KINDS[k].icon;
      b.title = KINDS[k].title;
      b.addEventListener('click', function(){ toggle(k); });
      document.body.appendChild(b);
    });
    // на тесни телефони колоната се свива, за да не изяде картата
    if(window.innerWidth <= 400){
      var n = 0;
      Object.keys(KINDS).forEach(function(k){
        var b = document.getElementById('tp-' + k);
        if(!b) return;
        b.style.width = b.style.height = '42px';
        b.style.fontSize = '19px';
        b.style.borderRadius = '13px';
        b.style.bottom = (214 + n * 50) + 'px';
        n++;
      });
    }
  }

  function mkPanel(){
    if(document.getElementById('tp-panel')) return;
    var p = document.createElement('div');
    p.id = 'tp-panel';
    p.innerHTML = '<div class="tp-head"><span id="tp-title">—</span>'
                + '<span class="tp-stamp" id="tp-stamp"></span>'
                + '<span class="tp-x" id="tp-close">✕</span></div>'
                + '<div id="tp-body"></div>';
    document.body.appendChild(p);
    document.getElementById('tp-close').addEventListener('click', close);
  }

  function close(){
    open = null;
    var p = document.getElementById('tp-panel');
    if(p) p.classList.remove('on');
    document.querySelectorAll('.tp-btn').forEach(function(b){ b.classList.remove('on'); });
  }

  function toggle(kind){
    if(open === kind){ close(); return; }
    open = kind;
    document.querySelectorAll('.tp-btn').forEach(function(b){
      b.classList.toggle('on', b.id === 'tp-' + kind);
    });
    document.getElementById('tp-panel').classList.add('on');
    render();
    if(!DATA && !loading) load();
  }

  function fmtStamp(iso){
    if(!iso) return '';
    var d = new Date(iso);
    if(isNaN(d)) return '';
    var mins = Math.round((Date.now() - d.getTime()) / 60000);
    if(mins < 2) return 'just now';
    if(mins < 60) return mins + ' min ago';
    return Math.round(mins / 60) + ' h ago';
  }

  function render(){
    if(!open) return;
    var body = document.getElementById('tp-body');
    var head = document.getElementById('tp-title');
    var stamp = document.getElementById('tp-stamp');
    head.textContent = KINDS[open].icon + ' ' + KINDS[open].title.toUpperCase();

    if(loading){
      body.innerHTML = '<div class="tp-empty">Loading…</div>';
      return;
    }
    if(!DATA){
      body.innerHTML = '<div class="tp-empty">No schedule data yet.<br>'
                     + 'It is fetched a few times a day.</div>';
      return;
    }

    stamp.textContent = fmtStamp(DATA.generated);

    var rows = (DATA[open] || []).filter(function(r){
      // миналите тръгвания не помагат на никого
      return !r.ts || r.ts * 1000 > Date.now() - 120000;
    });

    if(!rows.length){
      body.innerHTML = '<div class="tp-empty">Nothing scheduled right now.</div>';
      return;
    }

    body.innerHTML = rows.slice(0, 30).map(function(r){
      var late = r.delay > 0 ? '<span class="tp-late">+' + r.delay + '</span>' : '';
      var st = STATIONS[r.st] || '';
      return '<div class="tp-row">'
           + '<span class="tp-t">' + r.t + late + '</span>'
           + '<span class="tp-line">' + (r.cat || '') + (r.line || '') + '</span>'
           + '<span class="tp-to">' + esc(r.to)
           + (st ? '<span class="tp-st">from ' + st + '</span>' : '') + '</span>'
           + '<span class="tp-plat">' + (r.plat || '') + '</span>'
           + '</div>';
    }).join('');
  }

  function esc(s){
    return String(s || '').replace(/[&<>"]/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
    });
  }

  function load(){
    loading = true;
    render();
    fetch('data/transport.json', {cache:'no-cache'})
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(j){ DATA = j; loading = false; render(); })
      .catch(function(){ loading = false; render(); });
  }

  function init(){
    css();
    mkButtons();
    mkPanel();
    load();
    // разписанието остарява; освежаваме, когато човек се върне в приложението
    document.addEventListener('visibilitychange', function(){
      if(!document.hidden && DATA){
        var age = Date.now() - new Date(DATA.generated).getTime();
        if(age > 20 * 60000) load();
      }
    });
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
