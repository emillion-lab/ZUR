// Zürich Taxi Radar — превключвател English ⇄ Züridütsch
//
// Приложението е на английски по подразбиране. Швейцарският немски е
// разговорният език в Цюрих и е това, което шофьорът чува по улицата,
// затова е втори равностоен вариант, а не украса.
//
// Работи по data-i18n атрибути и по списък от селектори — така не се
// пипа логиката на app.js, а само надписите.
(function(){
  'use strict';

  var KEY = 'zur_lang';   // 'en' | 'gsw'

  var T = {
    en: {
      title:'ZÜRICH TAXI DEMAND',
      subtitle:'Live map · GPS navigation',
      zones:'▣ Zones by priority',
      list:'📋 List',
      map:'🗺 Map',
      trains:'Arriving trains',
      trams:'Arriving trams',
      buses:'Arriving buses',
      intl:'Intl. coaches',
      flights:'Flight arrivals',
      next90:'Next 90 minutes',
      gps:'GPS location',
      fs:'Fullscreen map',
      theme:'Night theme',
      loading:'Loading…',
      nothing:'Nothing arriving right now.',
      nodata:'No schedule data yet.',
      from:'from',
      justNow:'just now',
      minAgo:'min ago',
      hAgo:'h ago',
      dead:'⚠ DEAD ZONE'
    },
    gsw: {
      title:'ZÜRI TAXI NOCHFROG',
      subtitle:'Live Charte · GPS Navigation',
      zones:'▣ Zone nach Prio',
      list:'📋 Lischte',
      map:'🗺 Charte',
      trains:'Aachoend Züg',
      trams:'Aachoendi Träm',
      buses:'Aachoendi Büs',
      intl:'Uslandbüs',
      flights:'Aachoendi Flüüg',
      next90:'Nächschti 90 Minute',
      gps:'Min Standort',
      fs:'Ganzi Charte',
      theme:'Nachtmodus',
      loading:'Am Lade…',
      nothing:'Grad chunnt nüt aa.',
      nodata:'No kei Fahrplaadate.',
      from:'vo',
      justNow:'grad ebe',
      minAgo:'Min her',
      hAgo:'Std her',
      dead:'⚠ TOTI ZIT'
    }
  };

  var lang = 'en';
  try { lang = localStorage.getItem(KEY) || 'en'; } catch(e){}
  if(lang !== 'gsw') lang = 'en';

  // изнесено навън, за да го ползва и transport.js
  window.ZURLang = {
    get: function(){ return lang; },
    t: function(k){ return (T[lang] && T[lang][k]) || (T.en[k] || k); }
  };

  function css(){
    if(document.getElementById('lang-css')) return;
    var s = document.createElement('style');
    s.id = 'lang-css';
    s.textContent = [
      '#lang-btn{position:fixed;left:12px;bottom:16px;z-index:2400;',
      'min-width:48px;height:34px;padding:0 12px;border:0;border-radius:12px;',
      'display:flex;align-items:center;justify-content:center;gap:5px;',
      "font:800 12px/1 'Courier New',monospace;letter-spacing:1px;",
      'color:var(--text);background:var(--glass);cursor:pointer;',
      'box-shadow:0 6px 18px rgba(15,27,45,.20),',
      '0 1px 0 rgba(255,255,255,.75) inset,0 0 0 1px var(--glass-edge);',
      'backdrop-filter:saturate(180%) blur(16px);',
      '-webkit-backdrop-filter:saturate(180%) blur(16px);',
      'transition:transform .16s ease}',
      '#lang-btn:active{transform:scale(.92)}',
      'body.theme-night #lang-btn{box-shadow:0 6px 20px rgba(0,0,0,.55),',
      '0 1px 0 rgba(255,255,255,.08) inset,0 0 0 1px rgba(34,211,238,.45)}',
      'body.map-fullscreen #lang-btn{display:none}'
    ].join('');
    document.head.appendChild(s);
  }

  function apply(){
    var t = T[lang];
    document.documentElement.setAttribute('lang', lang === 'gsw' ? 'gsw' : 'en');

    set('.header h1', '📍 ' + t.title);
    set('.header p', t.subtitle);
    set('#tl-dead', t.dead);

    var zs = document.querySelector('#zone-sidebar .sidebar-title span');
    if(zs) zs.textContent = t.zones;

    var tm = document.getElementById('toggle-map-btn');
    if(tm) tm.textContent = document.body.classList.contains('list-view') ? t.map : t.list;

    title('#tp-train',  t.trains);
    title('#tp-tram',   t.trams);
    title('#tp-bus',    t.buses);
    title('#tp-intl',   t.intl);
    title('#flights-btn', t.flights);
    title('#next90-btn', t.next90);
    title('#gps-btn',   t.gps);
    title('#fs-btn',    t.fs);
    title('#theme-btn', t.theme);

    var b = document.getElementById('lang-btn');
    if(b) b.textContent = lang === 'en' ? 'EN' : 'GSW';

    // таблото се преначертава само, ако е отворено
    if(window.ZURTransportRedraw) window.ZURTransportRedraw();
  }

  function set(sel, txt){
    var el = document.querySelector(sel);
    if(el) el.textContent = txt;
  }
  function title(sel, txt){
    var el = document.querySelector(sel);
    if(el) el.title = txt;
  }

  function mount(){
    css();
    if(!document.getElementById('lang-btn')){
      var b = document.createElement('button');
      b.id = 'lang-btn';
      b.textContent = lang === 'en' ? 'EN' : 'GSW';
      b.addEventListener('click', function(){
        lang = (lang === 'en') ? 'gsw' : 'en';
        try { localStorage.setItem(KEY, lang); } catch(e){}
        apply();
      });
      document.body.appendChild(b);
    }
    apply();
    // бутоните за транспорта се раждат по-късно; наваксваме веднъж
    setTimeout(apply, 1200);
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
