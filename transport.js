// Zürich Taxi Radar — едно табло за всичко, което докарва клиенти
//
// Четири източника, един панел, един калъп:
//   ✈️ полети   — от flightDetails на app.js
//   🚂 влакове  — transport.opendata.ch, на живо
//   🚌 автобуси — същият API
//   🌍 междуградски — терминалът на Sihlquai
//
// Защо на живо, а не от готовия файл: пристиганията остаряват за час.
// Файлът се пълни четири пъти дневно и когато шофьорът го отвори,
// всичко вече е минало — точно това правеше таблото празно. Швейцарският
// API позволява заявка направо от браузъра, затова питаме него, а
// data/transport.json остава само за резерва, ако мрежата откаже.
(function(){
  'use strict';

  var API = 'https://transport.opendata.ch/v1/stationboard';

  var KINDS = {
    flights: { icon:'✈️', title:'Flight arrivals', gsw:'Aachoendi Flüüg' },
    train:   { icon:'🚂', title:'Train arrivals',  gsw:'Aachoendi Züg'  },
    bus:     { icon:'🚌', title:'Bus arrivals',    gsw:'Aachoendi Büs'  },
    intl:    { icon:'🌍', title:'Intl. coaches',   gsw:'Uslandbüs'      }
  };

  // Спирките, от които идват хора с багаж или бързане
  var STOPS = {
    train: [
      ['Zürich HB',           'HB'],
      ['Zürich Oerlikon',     'Oerlikon'],
      ['Zürich Stadelhofen',  'Stadelhofen'],
      ['Zürich Flughafen',    'Flughafen']
    ],
    bus: [
      ['Zürich, Bahnhofquai/HB', 'Bahnhofquai'],
      ['Zürich, Central',        'Central'],
      ['Zürich, Bellevue',       'Bellevue']
    ],
    // INTL-WIDE — имената на терминала се разминават между базите,
    // затова се пробват няколко и се събира каквото върне
    intl: [
      ['Zürich, Carparkplatz Sihlquai', 'Sihlquai'],
      ['Zürich, Sihlquai/HB',           'Sihlquai/HB'],
      ['Zürich Sihlquai',               'Sihlquai'],
      ['Zürich, Busbahnhof',            'Busbahnhof']
    ]
  };

  var TRAIN_CAT = {S:1,SN:1,IC:1,ICE:1,IR:1,RE:1,R:1,EC:1,TGV:1,RJX:1,NJ:1,PE:1};
  var BUS_CAT   = {B:1,BUS:1,NFB:1,TRO:1,NFO:1,KB:1};
  var TRAM_CAT  = {T:1,TRAM:1,NFT:1};

  var cache = {};          // {kind: {rows, at}}
  var open = null, busy = false;

  function isGsw(){
    try { return localStorage.getItem('zur_lang') === 'gsw'; } catch(e){ return false; }
  }
  function label(k){
    return isGsw() ? KINDS[k].gsw : KINDS[k].title;
  }

  function css(){
    if(document.getElementById('tp-css')) return;
    var s = document.createElement('style');
    s.id = 'tp-css';
    s.textContent = [
      /* бутоните — същият калъп като останалите в колоната */
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

      /* панелът заема целия екран — на телефон половинчатото е нечетимо */
      '#tp-panel{display:none;position:fixed;inset:0;z-index:3200;',
      'background:var(--bg);flex-direction:column}',
      '#tp-panel.on{display:flex}',
      '.tp-head{flex:0 0 auto;display:flex;align-items:center;gap:10px;',
      'padding:14px 16px;border-bottom:1px solid var(--glass-edge);',
      "font:800 16px 'Courier New',monospace;color:var(--cyan);letter-spacing:1px}",
      '.tp-head .tp-x{margin-left:auto;cursor:pointer;color:var(--muted);',
      'font-size:26px;line-height:1;padding:0 6px}',
      '.tp-stamp{font-size:11px;color:var(--muted);font-weight:400;letter-spacing:0}',
      '.tp-body{flex:1 1 auto;overflow-y:auto;-webkit-overflow-scrolling:touch}',

      /* редовете: сега слизащите се открояват, останалите избледняват */
      '.tp-sec{padding:10px 16px 4px;font:800 11px/1 sans-serif;letter-spacing:1.2px;',
      'color:var(--muted);text-transform:uppercase}',
      '.tp-row{display:flex;align-items:center;gap:10px;padding:11px 16px;',
      'border-bottom:1px solid var(--glass-edge)}',
      '.tp-row.now{background:rgba(220,38,38,.10);border-left:3px solid var(--red)}',
      'body.theme-night .tp-row.now{background:rgba(248,113,113,.12)}',
      '.tp-row.past{opacity:.42}',
      ".tp-t{font:800 15px 'Courier New',monospace;color:var(--amber);min-width:52px}",
      '.tp-row.now .tp-t{color:var(--red)}',
      '.tp-line{font-weight:800;font-size:14px;min-width:52px;color:var(--text)}',
      '.tp-to{flex:1;font-size:15px;color:var(--text);overflow:hidden;',
      'text-overflow:ellipsis;white-space:nowrap}',
      '.tp-st{font-size:11px;color:var(--muted);display:block;margin-top:2px}',
      '.tp-plat{font-size:13px;color:var(--muted);min-width:32px;text-align:right}',
      '.tp-late{color:var(--red);font-size:12px;font-weight:700;margin-left:3px}',
      '.tp-empty{padding:40px 20px;text-align:center;color:var(--muted);',
      'font-size:15px;line-height:1.7}',
      '.tp-note{padding:12px 16px 24px;font-size:11px;color:var(--muted);text-align:center}'
    ].join('');
    document.head.appendChild(s);
  }

  function mkButtons(){
    Object.keys(KINDS).forEach(function(k){
      var id = k === 'flights' ? 'flights-btn' : 'tp-' + k;
      var b = document.getElementById(id);
      if(b && b.dataset.tpBound) return;
      if(!b){
        b = document.createElement('button');
        b.id = id;
        b.className = 'tp-btn';
        b.textContent = KINDS[k].icon;
        document.body.appendChild(b);
      } else {
        b.classList.add('tp-btn');
        b.onclick = null;              // маха стария inline onclick
      }
      b.title = label(k);
      b.dataset.tpBound = '1';
      b.addEventListener('click', function(e){
        e.preventDefault();
        toggle(k);
      });
    });
  }

  function mkPanel(){
    if(document.getElementById('tp-panel')) return;
    var p = document.createElement('div');
    p.id = 'tp-panel';
    p.innerHTML = '<div class="tp-head"><span id="tp-title">—</span>'
                + '<span class="tp-stamp" id="tp-stamp"></span>'
                + '<span class="tp-x" id="tp-close">×</span></div>'
                + '<div class="tp-body" id="tp-body"></div>';
    document.body.appendChild(p);
    document.getElementById('tp-close').addEventListener('click', close);
  }

  function close(){
    open = null;
    var p = document.getElementById('tp-panel');
    if(p) p.classList.remove('on');
    document.body.classList.remove('tp-open');
    document.querySelectorAll('.tp-btn').forEach(function(b){ b.classList.remove('on'); });
  }

  // второто докосване прибира панела — иначе трябва да се цели в ×
  function toggle(kind){
    if(open === kind){ close(); return; }
    open = kind;
    var id = kind === 'flights' ? 'flights-btn' : 'tp-' + kind;
    document.querySelectorAll('.tp-btn').forEach(function(b){
      b.classList.toggle('on', b.id === id);
    });
    document.getElementById('tp-panel').classList.add('on');
    document.body.classList.add('tp-open');
    render();
    if(kind !== 'flights') load(kind);
  }

  // ── теглене на живо ──
  function fetchStop(name, key, kind){
    var lim = (kind === 'intl') ? 40 : 15;
    var u = API + '?station=' + encodeURIComponent(name)
          + '&limit=' + lim + '&type=arrival';
    return fetch(u).then(function(r){ return r.ok ? r.json() : null; })
      .then(function(d){
        if(!d || !d.stationboard) return [];
        return d.stationboard.map(function(e){
          var stop = e.stop || {};
          var when = stop.arrival || stop.departure || '';
          if(!when) return null;
          var cat = (e.category || '').toUpperCase();
          if(kind === 'train' && !TRAIN_CAT[cat]) return null;
          if(kind === 'bus' && !BUS_CAT[cat]) return null;
          // INTL-NOTRAM — Sihlquai е и трамвайна спирка. Предишната
          // версия пускаше всичко и таблото се напълни с T50/T51/T17,
          // тоест градски трамваи, обявени за международни автобуси.
          if(kind === 'intl'){
            if(TRAM_CAT[cat]) return null;              // трамвай не е междуградски
            if(!BUS_CAT[cat] && cat !== '') return null;
            var ln = String(e.number || '');
            // градските линии са двуцифрени; международните носят име
            // на превозвача или трицифрен номер
            if(/^\d{1,2}$/.test(ln)) return null;
          }
          var pr = (stop.prognosis || {});
          var pw = pr.arrival || pr.departure;
          var delay = 0;
          if(pw && pw !== when){
            delay = Math.round((new Date(pw) - new Date(when)) / 60000);
          }
          return {
            t: when.slice(11,16),
            ts: (stop.arrivalTimestamp || stop.departureTimestamp || 0) * 1000,
            cat: e.category || '',
            line: e.number || '',
            from: (e.from || e.to || '').trim(),
            plat: (stop.platform || '').trim(),
            delay: delay,
            st: key
          };
        }).filter(Boolean);
      }).catch(function(){ return []; });
  }

  function load(kind){
    var c = cache[kind];
    if(c && Date.now() - c.at < 90000){ render(); return; }   // 90 с е достатъчно свежо
    busy = true; render();
    Promise.all(STOPS[kind].map(function(s){
      return fetchStop(s[0], s[1], kind);
    })).then(function(lists){
      var rows = [];
      lists.forEach(function(l){ rows = rows.concat(l); });
      rows.sort(function(a,b){ return a.ts - b.ts; });
      // една линия от една спирка се повтаря; държим по две
      var seen = {}, keep = [];
      rows.forEach(function(r){
        var sig = (kind === 'intl' ? '' : r.st) + '|'
                + r.cat + r.line + '|' + r.from + '|' + r.t;
        seen[sig] = (seen[sig] || 0) + 1;
        if(seen[sig] <= 2) keep.push(r);
      });
      cache[kind] = { rows: keep, at: Date.now(), live: keep.length > 0 };
      busy = false;
      if(!keep.length) fallback(kind);
      else render();
    }).catch(function(){ busy = false; fallback(kind); });
  }

  // ако мрежата или API-то откажат — показваме последното изтеглено от файла
  function fallback(kind){
    fetch('data/transport.json', {cache:'no-cache'})
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(j){
        if(!j) { render(); return; }
        var rows = (j[kind] || []).map(function(r){
          return {t:r.t, ts:(r.ts||0)*1000, cat:r.cat, line:r.line,
                  from:r.from || r.to || '', plat:r.plat, delay:r.delay, st:r.st};
        });
        cache[kind] = { rows: rows, at: new Date(j.generated).getTime(), live:false };
        render();
      })
      .catch(function(){ render(); });
  }

  // ── полетите идват от app.js ──
  function flightRows(){
    var fd = window.flightDetails || [];
    var now = new Date();
    var nowMin = ((now.getUTCHours() + 2) % 24) * 60 + now.getUTCMinutes();
    return fd.map(function(f){
      var from = f.exitFromH * 60 + f.exitFromM;
      var to   = f.exitToH   * 60 + f.exitToM;
      var adj = function(m){ return m < 300 ? m + 1440 : m; };
      var n = adj(nowMin), a = adj(from), b = adj(to);
      return {
        t: pad(f.exitFromH) + ':' + pad(f.exitFromM),
        t2: pad(f.exitToH) + ':' + pad(f.exitToM),
        ts: 0,
        sortKey: a,
        cat: '', line: f.fn,
        from: f.depAirport || '',
        plat: f.nonSchengen ? '🛂' : '🇪🇺',
        delay: 0, st: '',
        now: a <= n && b >= n,
        past: b < n
      };
    }).sort(function(x,y){ return x.sortKey - y.sortKey; });
  }
  function pad(n){ return String(n).padStart(2,'0'); }

  function esc(s){
    return String(s || '').replace(/[&<>"]/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
    });
  }


  // Международните ги няма в швейцарското разписание — по-добре да се
  // каже, отколкото шофьорът да реши, че приложението е счупено.
  function emptyText(){
    if(open === 'intl'){
      return isGsw()
        ? 'Kei Uslandbüs im Fahrplaa.<br><span style="font-size:12px">'
          + 'FlixBus &amp; Co. gänd ihri Zite nöd a d\u2019SBB wiiter.<br>'
          + 'Terminal: Carparkplatz Sihlquai</span>'
        : 'International coaches are not in the Swiss timetable.'
          + '<br><span style="font-size:12px">FlixBus and others do not publish '
          + 'to SBB, so nothing can be shown here.<br>'
          + 'Terminal: Carparkplatz Sihlquai, next to the main station</span>';
    }
    return isGsw() ? 'Grad chunnt nüt aa.' : 'Nothing arriving right now.';
  }

  function render(){
    if(!open) return;
    var body = document.getElementById('tp-body');
    var head = document.getElementById('tp-title');
    var stamp = document.getElementById('tp-stamp');
    head.textContent = KINDS[open].icon + '  ' + label(open).toUpperCase();

    if(open === 'flights'){
      stamp.textContent = '';
      renderFlights(body);
      return;
    }

    if(busy && !cache[open]){
      stamp.textContent = '';
      body.innerHTML = '<div class="tp-empty">…</div>';
      return;
    }

    var c = cache[open];
    if(!c || !c.rows.length){
      stamp.textContent = '';
      body.innerHTML = '<div class="tp-empty">' + emptyText() + '</div>';
      return;
    }

    stamp.textContent = c.live ? 'live' : 'cached';

    var now = Date.now();
    var html = '';
    var wroteNow = false, wroteLater = false;

    c.rows.forEach(function(r){
      var mins = r.ts ? Math.round((r.ts - now) / 60000) : null;
      var isNow  = mins !== null && mins >= -5 && mins <= 5;
      var isPast = mins !== null && mins < -5;
      // Международните са по няколко на ден — минал автобус пак е
      // сведение кога идва следващият, затова не се крие.
      if(isPast && open !== 'intl') return;

      if(isNow && !wroteNow){
        html += '<div class="tp-sec">' + (isGsw() ? 'Jetzt' : 'Arriving now') + '</div>';
        wroteNow = true;
      } else if(!isNow && !wroteLater){
        html += '<div class="tp-sec">' + (isGsw() ? 'Chunnt' : 'Next') + '</div>';
        wroteLater = true;
      }

      var late = r.delay > 0 ? '<span class="tp-late">+' + r.delay + '</span>' : '';
      var inTxt = mins !== null && mins > 0 ? ' · ' + mins + ' min' : '';
      html += '<div class="tp-row' + (isNow ? ' now' : '') + '">'
            + '<span class="tp-t">' + r.t + late + '</span>'
            + '<span class="tp-line">' + esc(r.cat) + esc(r.line) + '</span>'
            + '<span class="tp-to">' + esc(r.from)
            + '<span class="tp-st">' + esc(r.st) + inTxt + '</span></span>'
            + '<span class="tp-plat">' + esc(r.plat) + '</span>'
            + '</div>';
    });

    if(!html) html = '<div class="tp-empty">' + emptyText() + '</div>';

    body.innerHTML = html + '<div class="tp-note">transport.opendata.ch</div>';
  }

  function renderFlights(body){
    var rows = flightRows();
    if(!rows.length){
      body.innerHTML = '<div class="tp-empty">'
        + (isGsw() ? 'Kei Flugdate.' : 'No flight data.') + '</div>';
      return;
    }
    var html = '';
    var wroteNow = false, wroteNext = false, wrotePast = false;
    // първо тези, които слизат сега — те са същината
    rows.forEach(function(r){
      if(!r.now) return;
      if(!wroteNow){
        html += '<div class="tp-sec">' + (isGsw() ? 'Stiiged jetzt us' : 'Exiting now') + '</div>';
        wroteNow = true;
      }
      html += flightRow(r, 'now');
    });
    rows.forEach(function(r){
      if(r.now || r.past) return;
      if(!wroteNext){
        html += '<div class="tp-sec">' + (isGsw() ? 'Chunnt' : 'Upcoming') + '</div>';
        wroteNext = true;
      }
      html += flightRow(r, '');
    });
    rows.slice().reverse().forEach(function(r){
      if(!r.past) return;
      if(!wrotePast){
        html += '<div class="tp-sec">' + (isGsw() ? 'Scho use' : 'Already out') + '</div>';
        wrotePast = true;
      }
      if((html.match(/tp-row past/g) || []).length < 6) html += flightRow(r, 'past');
    });
    body.innerHTML = html
      + '<div class="tp-note">🇪🇺 Schengen +15–25 min · 🛂 Non-Schengen +25–35 min</div>';
  }

  function flightRow(r, cls){
    return '<div class="tp-row ' + cls + '">'
         + '<span class="tp-t">' + r.t + '</span>'
         + '<span class="tp-line">' + esc(r.line) + '</span>'
         + '<span class="tp-to">' + esc(r.from)
         + '<span class="tp-st">' + r.t + '–' + r.t2 + '</span></span>'
         + '<span class="tp-plat">' + r.plat + '</span>'
         + '</div>';
  }


  // Докато таблото е отворено, останалите бутони служат за затваряне —
  // панелът покрива екрана и иначе трябва да се цели в малкото ×.
  function bindClosers(){
    ['fs-btn','gps-btn','next90-btn','list-btn'].forEach(function(id){
      var b = document.getElementById(id);
      if(!b || b.dataset.tpCloser) return;
      b.dataset.tpCloser = '1';
      b.addEventListener('click', function(e){
        if(open){
          e.preventDefault();
          e.stopImmediatePropagation();
          close();
        }
      }, true);   // capture: изпреварва собственото действие на бутона
    });
  }

  window.ZURTransportRedraw = render;

  function init(){
    css();
    mkPanel();
    mkButtons();
    bindClosers();
    setTimeout(function(){ mkButtons(); bindClosers(); }, 1500);        // app.js може да е пренаписал бутона
    // отвореното табло се освежава, щом човек се върне в приложението
    document.addEventListener('visibilitychange', function(){
      if(!document.hidden && open && open !== 'flights'){
        delete cache[open];
        load(open);
      }
    });
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
