document.addEventListener('DOMContentLoaded', function() {

if (typeof L === 'undefined') {
  document.getElementById('map').innerHTML =
    '<div style="color:#ef4444;padding:20px;font-family:monospace">Leaflet failed to load.</div>';
  return;
}

// ═══════════════════════════════════════════════
// GLOBAL STATE
// ═══════════════════════════════════════════════
let currentHour       = 16;
let karykMode         = false;
let autoTime          = true;
let weatherBoost      = 0;
let userLat           = null;
let userLng           = null;
let watchId           = null;
let userMarker        = null;
let navTarget         = null;
let deviceHeading     = null;
let dirHintZid        = null;
let dirHintSuppressed = false;
let flightHours       = Array(24).fill(0);
let flightDetails     = []; // [{from, exitFrom, exitTo, fn, nonSchengen}]
let airportStatus     = 'offline';
let demandCurve       = [];
let alertedEvents     = new Set();

// ═══════════════════════════════════════════════
// ZONE DEFINITIONS
// ═══════════════════════════════════════════════
const ZONES = [
  { id:"airport",      name:"Flughafen Zürich (ZRH)",              icon:"✈️", lat:47.4515, lng:8.5646, radius:800, type:"airport",  wazeName:"Zurich Airport" },
  { id:"hb",           name:"Zürich HB (Hauptbahnhof)",            icon:"🚉", lat:47.3779, lng:8.5403, radius:420, type:"transit",  wazeName:"Zurich HB" },
  { id:"oerlikon_bhf", name:"Bahnhof Oerlikon",                    icon:"🚉", lat:47.4116, lng:8.5441, radius:300, type:"transit",  wazeName:"Bahnhof Oerlikon" },
  { id:"stadelhofen",  name:"Bahnhof Stadelhofen",                 icon:"🚉", lat:47.3664, lng:8.5484, radius:250, type:"transit",  wazeName:"Stadelhofen" },
  { id:"enge_bhf",     name:"Bahnhof Enge",                        icon:"🚉", lat:47.3641, lng:8.5312, radius:240, type:"transit",  wazeName:"Bahnhof Enge" },
  { id:"paradeplatz",  name:"Paradeplatz / Bahnhofstrasse",        icon:"🏦", lat:47.3699, lng:8.5390, radius:300, type:"office",   wazeName:"Paradeplatz Zurich" },
  { id:"cityring",     name:"City / Bürkliplatz (lake)",        icon:"🏢", lat:47.3665, lng:8.5410, radius:300, type:"office",   wazeName:"Burkliplatz" },
  { id:"zurich_west",  name:"Zürich West / Prime Tower",           icon:"🏢", lat:47.3861, lng:8.5170, radius:380, type:"office",   wazeName:"Prime Tower Zurich" },
  { id:"opfikon_gl",   name:"Glattpark / The Circle offices",        icon:"🏢", lat:47.4310, lng:8.5610, radius:380, type:"office",   wazeName:"The Circle Zurich Airport" },
  { id:"oerlikon_of",  name:"Oerlikon offices (ABB/Google)",         icon:"🏢", lat:47.4090, lng:8.5380, radius:340, type:"office",   wazeName:"Oerlikon Zurich" },
  { id:"glatt",        name:"Glattzentrum",                        icon:"🛍", lat:47.4104, lng:8.5940, radius:320, type:"mall",     wazeName:"Glattzentrum Wallisellen" },
  { id:"sihlcity",     name:"Sihlcity",                            icon:"🛍", lat:47.3595, lng:8.5253, radius:280, type:"mall",     wazeName:"Sihlcity Zurich" },
  { id:"letzipark",    name:"Letzipark",                           icon:"🛍", lat:47.3877, lng:8.4996, radius:260, type:"mall",     wazeName:"Letzipark Zurich" },
  { id:"hotels_ctr",   name:"Hotels City (Baur au Lac/Savoy)",   icon:"🏨", lat:47.3690, lng:8.5395, radius:300, type:"hotel",    wazeName:"Baur au Lac Zurich" },
  { id:"hotels_apt",   name:"Hotels Airport (Hyatt/Radisson)",      icon:"🏨", lat:47.4520, lng:8.5710, radius:350, type:"hotel",    wazeName:"Radisson Blu Zurich Airport" },
  { id:"langstrasse",  name:"Langstrasse (nightlife)",           icon:"🍸", lat:47.3785, lng:8.5290, radius:320, type:"nightlife",wazeName:"Langstrasse Zurich" },
  { id:"niederdorf",   name:"Niederdorf / Old Town bars",        icon:"🍸", lat:47.3730, lng:8.5440, radius:260, type:"nightlife",wazeName:"Niederdorf Zurich" },
  { id:"zw_clubs",     name:"Zürich West clubs (Hive/Escherwyss)",icon:"🍸",lat:47.3900, lng:8.5150, radius:300, type:"nightlife",wazeName:"Escher Wyss Platz" },
  { id:"hallenstadion",name:"Hallenstadion / Messe Oerlikon",      icon:"🎤", lat:47.4111, lng:8.5517, radius:380, type:"venue",    wazeName:"Hallenstadion Zurich" },
  { id:"letzigrund",   name:"Letzigrund Stadion",                  icon:"🏟", lat:47.3826, lng:8.5039, radius:360, type:"venue",    wazeName:"Letzigrund" },
  { id:"usz",          name:"UniversitätsSpital (USZ)",            icon:"🏥", lat:47.3768, lng:8.5510, radius:280, type:"hospital", wazeName:"Universitatsspital Zurich" },
  { id:"triemli",      name:"Stadtspital Triemli",                 icon:"🏥", lat:47.3670, lng:8.4970, radius:280, type:"hospital", wazeName:"Triemli Spital" },
  { id:"waid",         name:"Stadtspital Waid",                    icon:"🏥", lat:47.3990, lng:8.5210, radius:240, type:"hospital", wazeName:"Waid Spital" },
  { id:"uni_eth",      name:"ETH / Universität Zürich",            icon:"🎓", lat:47.3763, lng:8.5480, radius:300, type:"university",wazeName:"ETH Zurich" },
  { id:"irchel",       name:"Uni Irchel / students",             icon:"🎓", lat:47.3974, lng:8.5482, radius:280, type:"university",wazeName:"Irchel Zurich" },
  { id:"seefeld",      name:"Seefeld (upscale residential)",              icon:"🏘", lat:47.3600, lng:8.5560, radius:340, type:"residential_lux", wazeName:"Seefeld Zurich" },
  { id:"altstetten",   name:"Altstetten (residential)",                icon:"🏘", lat:47.3890, lng:8.4850, radius:380, type:"residential", wazeName:"Altstetten" },
];

// ═══════════════════════════════════════════════
// BASE DEMAND
// ═══════════════════════════════════════════════
const BASE = {
  airport:1.5, hb:1.2, oerlikon_bhf:0.7, stadelhofen:0.6, enge_bhf:0.5,
  paradeplatz:0.8, cityring:0.7, zurich_west:0.6, opfikon_gl:0.6, oerlikon_of:0.6,
  glatt:0.6, sihlcity:0.6, letzipark:0.5,
  hotels_ctr:0.9, hotels_apt:0.8,
  langstrasse:0.8, niederdorf:0.6, zw_clubs:0.7,
  hallenstadion:0.4, letzigrund:0.3,
  usz:0.9, triemli:0.7, waid:0.6,
  uni_eth:0.5, irchel:0.5,
  seefeld:0.5, altstetten:0.4,
};

// ═══════════════════════════════════════════════
// EVENTS
// ═══════════════════════════════════════════════
const EVENTS = [
  { zone:"paradeplatz",  name:"Banks/offices — out",        endHour:17.5, boost:2.6, repeat:"mon-fri" },
  { zone:"zurich_west",  name:"Zürich West — out",        endHour:18.0, boost:2.4, repeat:"mon-fri" },
  { zone:"opfikon_gl",   name:"The Circle — out",         endHour:17.5, boost:2.2, repeat:"mon-fri" },
  { zone:"langstrasse",  name:"Bars closing",      endHour:2.0,  boost:3.0, repeat:"fri-sat" },
  { zone:"zw_clubs",     name:"Clubs closing",        endHour:4.0,  boost:3.2, repeat:"fri-sat" },
  { zone:"hallenstadion",name:"Hallenstadion event (demo)",endHour:22.5, boost:3.5, repeat:"sat" },
  { zone:"hb",           name:"Last trains",           endHour:0.5,  boost:2.4, repeat:"daily" },
];

// ═══════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════
function demandColor(score, type) {
  if (type === 'hospital')
    return score>=2.0 ? {fill:"#ff2020",fillAlpha:0.75,stroke:"#ff6060",label:"🏥 Active"}
         : score>=1.3 ? {fill:"#ef4444",fillAlpha:0.60,stroke:"#ff5555",label:"🏥"}
         :              {fill:"#991b1b",fillAlpha:0.40,stroke:"#cc3333",label:"🏥"};
  if (type === 'karyk')
    return {fill:"#f97316",fillAlpha:0.0,stroke:"transparent",label:"🥉"};
  if (score>=3.2) return {fill:"#ef4444",fillAlpha:0.55,stroke:"#ff7777",label:"PEAK 🔥"};
  if (score>=2.4) return {fill:"#f97316",fillAlpha:0.50,stroke:"#ffaa55",label:"High ▲"};
  if (score>=1.6) return {fill:"#f59e0b",fillAlpha:0.45,stroke:"#ffd060",label:"Medium"};
  if (score>=0.8) return {fill:"#22c55e",fillAlpha:0.35,stroke:"#55ee88",label:"Normal"};
  return               {fill:"#1a3050",fillAlpha:0.20,stroke:"#2a4870",label:"Quiet"};
}

function karykColor(ks) {
  if (ks>=4.0) return {fill:"#ff6b00",stroke:"#ff9040",label:"🔥 Karyk PEAK"};
  if (ks>=3.0) return {fill:"#f97316",stroke:"#ffaa55",label:"▲ Excellent"};
  if (ks>=2.0) return {fill:"#fbbf24",stroke:"#ffd060",label:"Good"};
  if (ks>=1.0) return {fill:"#a3a300",stroke:"#d4d400",label:"Low"};
  return              {fill:"#1a1030",stroke:"#2a2050",label:"Avoid"};
}

function fmtHour(h) {
  return String(Math.floor(h)).padStart(2,'0') + ':' + (h%1===0.5?'30':'00');
}

const TODAY    = new Date();
const todayStr = TODAY.toISOString().slice(0,10);
const todayDay = TODAY.getDay();

function dayMatches(ev) {
  if (ev.date    && ev.date    !== todayStr)  return false;
  if (ev.endDate && todayStr   >  ev.endDate) return false;
  const r = ev.repeat;
  if (!r || r==="daily")    return true;
  if (r==="mon-fri")        return todayDay>=1 && todayDay<=5;
  if (r==="fri-sat")        return [5,6].includes(todayDay);
  if (r==="tue-sat")        return todayDay>=2 && todayDay<=6;
  if (r==="tue-sun")        return todayDay>=2 || todayDay===0;
  if (r==="thu-sat")        return [4,5,6].includes(todayDay);
  if (r==="wed-sat")        return todayDay>=3 && todayDay<=6;
  return true;
}

function deadZoneFactor(h) {
  if (h>=20 && h<=21) {
    const m=20.5;
    return 0.42 + 0.58*Math.pow(Math.abs(h-m)/0.5, 2);
  }
  return 1.0;
}

function computeScores(hour) {
  const scores={}, activeEvents={};
  ZONES.forEach(z => { scores[z.id]=BASE[z.id]||0.3; activeEvents[z.id]=[]; });
  const dz = deadZoneFactor(hour);
  for (const ev of EVENTS) {
    if (!dayMatches(ev)) continue;
    const diff = hour - ev.endHour;
    let f = 0;
    if (diff>=-0.75 && diff<=0)   f = (diff+0.75)/0.75;
    else if (diff>0 && diff<=1.5) f = 1 - diff/1.5;
    if (f>0.05) {
      scores[ev.zone] = (scores[ev.zone]||0) + ev.boost*f*dz;
      activeEvents[ev.zone].push({name:ev.name, f});
    }
  }
  // Weather boost
  if (weatherBoost>0) {
    ZONES.forEach(z => {
      if (['residential','residential_lux','hospital','karyk'].includes(z.type))
        scores[z.id] += weatherBoost*0.6;
      else if (['mall','hotel'].includes(z.type))
        scores[z.id] += weatherBoost*0.3;
    });
  }
  if (dz<1) ZONES.forEach(z => { if(z.id!=='airport') scores[z.id]*=(0.7+0.3*dz); });
  return {scores, activeEvents};
}

function totalDemand(hour) {
  const {scores}=computeScores(hour);
  return Object.values(scores).reduce((a,b)=>a+b,0);
}

function computeKarykScore(zid, scores) {
  const z = ZONES.find(x=>x.id===zid);
  if (!z) return 0;
  const demand = scores[zid]||0;
  const typeBonus = {
    karyk:1.8, residential_lux:1.2, residential:1.0,
    hospital:0.8, leisure:0.5,
    university:-0.3, theatre:-0.2, venue:-0.2,
    office:-0.5, mall:-0.8, hotel:-0.8,
    airport:-1.5, transit:-0.6,
  };
  let ks = demand + (typeBonus[z.type]||0);
  if (demand<1.0) ks += 0.8;
  return Math.max(0, Math.min(5, ks));
}

// ═══════════════════════════════════════════════
// TRAFFIC JAM INFO
// ═══════════════════════════════════════════════
const TRAFFIC_INFO = {
};

const trafficMarkers={};
function makeTrafficIcon(info,active){
  const op=active?'1':'0.35', sz=active?14:10;
  const glow=active?`0 0 8px #a855f7`:'none';
  return L.divIcon({className:'',
    html:`<div style="width:${sz}px;height:${sz}px;border-radius:50%;background:#a855f7;box-shadow:${glow};opacity:${op};${active?'animation:jam-blink 2s ease-in-out infinite':''}"></div>`,
    iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]});
}

// ═══════════════════════════════════════════════
// HOSPITAL CROSS ICON
// ═══════════════════════════════════════════════
function makeHospitalIcon(score){
  const bright=score>=2.0?'#ff2020':score>=1.3?'#ef4444':'#cc2222';
  const sz=score>=2.0?26:score>=1.3?22:18;
  const glow=score>=1.3?`drop-shadow(0 0 5px ${bright})`:'none';
  return L.divIcon({className:'',
    html:`<div style="width:${sz}px;height:${sz}px;position:relative;filter:${glow}">
      <div style="position:absolute;left:50%;top:20%;transform:translateX(-50%);width:30%;height:60%;background:${bright};border-radius:2px"></div>
      <div style="position:absolute;top:50%;left:15%;transform:translateY(-50%);width:70%;height:28%;background:${bright};border-radius:2px"></div>
    </div>`,iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]});
}

// ═══════════════════════════════════════════════
// KARYK SCORE ALGORITHM
// ═══════════════════════════════════════════════
const KARYK_PREFER=['hospital','residential','residential_lux','karyk','leisure'];
const KARYK_AVOID =['airport','mall','hotel','office','university','nightlife','transit','venue','theatre','cinema','traffic'];

function computeKarykScore(zid,scores){
  const z=ZONES.find(x=>x.id===zid); if(!z) return 0;
  const demand=scores[zid]||0;
  const typeBonus={
    karyk:1.8, residential_lux:1.2, residential:1.0,
    hospital:0.8, leisure:0.5,
    university:-0.3, theatre:-0.2, cinema:-0.1, venue:-0.2, nightlife:-0.2,
    office:-0.5, mall:-0.8, hotel:-0.8,
    airport:-1.5, transit:-0.6, traffic:0,
  };
  let ks=demand+(typeBonus[z.type]||0);
  if(demand<1.0) ks+=0.8;
  if(!['airport','hb','paradeplatz','glatt','hotels_ctr'].includes(zid)) ks+=0.3;
  return Math.max(0,Math.min(5,ks));
}

// ═══════════════════════════════════════════════
// NOMINATIM GEOCODING (кешира за 7 дни)
// ═══════════════════════════════════════════════
const NOMINATIM_QUERIES = {
};

const CACHE_KEY='sofia_taxi_coords_v4', CACHE_TTL=7*24*3600*1000;

async function geocodeZones(){
  let cache={};
  try{
    const raw=localStorage.getItem(CACHE_KEY);
    if(raw){const p=JSON.parse(raw);if(Date.now()-p.ts<CACHE_TTL)cache=p.coords;}
  }catch(e){}
  const zMap={}; ZONES.forEach(z=>{zMap[z.id]=z;});
  const missing=ZONES.filter(z=>!cache[z.id]&&NOMINATIM_QUERIES[z.id]);
  if(!missing.length){applyGeoCache(cache,zMap);return;}
  const badge=document.getElementById('airport-badge');
  const orig=badge.textContent;
  let i=0;
  for(const z of missing){
    try{
      const r=await fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(NOMINATIM_QUERIES[z.id])}`,
        {headers:{'User-Agent':'SofiaTaxiDemand/1.0'}});
      const d=await r.json();
      if(d&&d[0]) cache[z.id]={lat:parseFloat(d[0].lat),lng:parseFloat(d[0].lon)};
    }catch(e){}
    badge.textContent=`📡 ${++i}/${missing.length}`;
    await new Promise(r=>setTimeout(r,1100));
  }
  try{localStorage.setItem(CACHE_KEY,JSON.stringify({ts:Date.now(),coords:cache}));}catch(e){}
  badge.textContent=orig;
  applyGeoCache(cache,zMap);
}

function applyGeoCache(cache,zMap){
  let n=0;
  for(const[id,coords]of Object.entries(cache)){
    if(zMap[id]&&coords){zMap[id].lat=coords.lat;zMap[id].lng=coords.lng;n++;}
  }
  if(n>0){
    ZONES.forEach(z=>{circleMap[z.id]?.setLatLng?.([z.lat,z.lng]);});
    Object.values(hospitalMarkers).forEach(({marker,circle},id)=>{
      const z=ZONES.find(x=>x.id===id); if(!z) return;
      marker?.setLatLng([z.lat,z.lng]); circle?.setLatLng([z.lat,z.lng]);
    });
    render(currentHour);
  }
}

// ═══════════════════════════════════════════════
// NEXT 90 MINUTES PANEL
// ═══════════════════════════════════════════════
let next90Open=false;
document.getElementById('next90-btn')?.addEventListener('click',()=>{
  next90Open=!next90Open;
  document.getElementById('next90-btn').classList.toggle('active',next90Open);
  const panel=document.getElementById('next90-panel');
  if(next90Open){buildNext90();panel.style.display='block';}
  else panel.style.display='none';
});
window.closeNext90=function(){
  next90Open=false;
  document.getElementById('next90-btn')?.classList.remove('active');
  document.getElementById('next90-panel').style.display='none';
};

function buildNext90(){
  const h=currentHour; // следва slider-а
  const end=Math.min(24,h+1.5);
  const zMap={}; ZONES.forEach(z=>{zMap[z.id]=z;});
  const upcoming=EVENTS.filter(ev=>dayMatches(ev)&&!ev._fromFlight)
    .filter(ev=>ev.endHour>h&&ev.endHour<=end)
    .sort((a,b)=>a.endHour-b.endHour);
  const list=document.getElementById('next90-list');
  if(!list) return;
  if(!upcoming.length){
    list.innerHTML='<div style="padding:14px;color:var(--muted);font-size:15px">No major events in the next 90 min</div>';
    return;
  }
  list.innerHTML=upcoming.map(ev=>{
    const z=zMap[ev.zone]; if(!z) return '';
    const min=Math.round((ev.endHour-h)*60);
    const c=demandColor(ev.boost,z.type);
    return `<div class="n90-item">
      <div class="n90-time">${fmtHour(ev.endHour)}</div>
      <div class="n90-icon">${z.icon}</div>
      <div class="n90-info">
        <div class="n90-name">${ev.name}</div>
        <div class="n90-zone">${z.name.split('(')[0].trim()} · in ${min} min</div>
      </div>
      <div class="n90-score" style="color:${c.fill}">+${ev.boost.toFixed(1)}</div>
    </div>`;
  }).join('');
}

// ═══════════════════════════════════════════════
const map = L.map('map', {center:[47.3900,8.5417], zoom:12, zoomControl:true, attributionControl:false});
L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
  maxZoom:19, subdomains:['a','b','c','d']
}).addTo(map);
document.getElementById('map').style.filter='brightness(0.85) saturate(0.6)';
setTimeout(()=>map.invalidateSize(), 300);
setTimeout(()=>map.invalidateSize(), 800);

const circleMap={}, hospitalMarkers={};

function makeHospitalIcon(score) {
  const bright = score>=2.0?'#ff2020':score>=1.3?'#ef4444':'#cc2222';
  const sz = score>=2.0?26:score>=1.3?22:18;
  const glow = score>=1.3?`drop-shadow(0 0 5px ${bright})`:'none';
  return L.divIcon({
    className:'',
    html:`<div style="width:${sz}px;height:${sz}px;position:relative;filter:${glow}">
      <div style="position:absolute;left:50%;top:20%;transform:translateX(-50%);width:30%;height:60%;background:${bright};border-radius:2px"></div>
      <div style="position:absolute;top:50%;left:15%;transform:translateY(-50%);width:70%;height:28%;background:${bright};border-radius:2px"></div>
    </div>`,
    iconSize:[sz,sz], iconAnchor:[sz/2,sz/2],
  });
}

function buildCircles() {
  ZONES.forEach(z => {
    if (z.type==='traffic') {
      const info=TRAFFIC_INFO[z.id];
      if(info){
        const m=L.marker([z.lat,z.lng],{icon:makeTrafficIcon(info,false),zIndexOffset:600}).addTo(map);
        m.on('click',()=>showZonePopup(z.id));
        trafficMarkers[z.id]=m; circleMap[z.id]=m;
      }
      return;
    }
    if (z.type==='karyk') {
      const c=L.circle([z.lat,z.lng],{radius:z.radius,fillOpacity:0,opacity:0,weight:0});
      c.on('click',()=>z.type==='airport'?showAirportSchedule():z.type==='transit'?showTransitPopup(z.id):showZonePopup(z.id)); c.addTo(map); circleMap[z.id]=c;
      return;
    }
    if (z.type==='hospital') {
      const hm=L.marker([z.lat,z.lng],{icon:makeHospitalIcon(BASE[z.id]||0.5),zIndexOffset:400}).addTo(map);
      hm.on('click',()=>showZonePopup(z.id));
      const hc=L.circle([z.lat,z.lng],{radius:z.radius,color:'#991b1b',fillColor:'#991b1b',fillOpacity:0.12,weight:1}).addTo(map);
      hc.on('click',()=>showZonePopup(z.id));
      hospitalMarkers[z.id]={marker:hm,circle:hc};
      circleMap[z.id]={setStyle:(o)=>hc.setStyle({fillColor:o.fillColor||'#991b1b',fillOpacity:o.fillOpacity||0.12,color:o.color||'#cc2222'}),_hm:hm,_hc:hc};
      return;
    }
    const c=L.circle([z.lat,z.lng],{radius:z.radius,...getScoreStyle(BASE[z.id]||0.3,z.type)});
    c.on('click',()=>z.type==='airport'?showAirportSchedule():z.type==='transit'?showTransitPopup(z.id):showZonePopup(z.id)); c.addTo(map); circleMap[z.id]=c;
  });
}

function getScoreStyle(score, type) {
  const c=demandColor(score,type);
  return {color:c.stroke, fillColor:c.fill, fillOpacity:c.fillAlpha, weight:1.5, opacity:0.85};
}

function updateCircles() {
  const {scores}=computeScores(currentHour);
  ZONES.forEach(z => {
    const s=scores[z.id]||0;
    if (z.type==='traffic') {
      const info=TRAFFIC_INFO[z.id];
      const marker=trafficMarkers[z.id];
      if(marker&&info) marker.setIcon(makeTrafficIcon(info,s>=1.5));
      return;
    }
    if (z.type==='hospital') {
      const cm=circleMap[z.id];
      if(cm?._hm) cm._hm.setIcon(makeHospitalIcon(s));
      cm?.setStyle(getScoreStyle(s,z.type));
      return;
    }
    if (z.type==='karyk') {
      if (karykMode) {
        const ks=computeKarykScore(z.id,scores);
        const kc=karykColor(ks);
        circleMap[z.id]?.setStyle({color:kc.stroke,fillColor:kc.fill,fillOpacity:ks>=1?0.6:0.1,weight:2,opacity:ks>=1?0.9:0.2});
      } else {
        circleMap[z.id]?.setStyle({fillOpacity:0,opacity:0,weight:0});
      }
      return;
    }
    if (karykMode) {
      const ks=computeKarykScore(z.id,scores);
      const kc=karykColor(ks);
      circleMap[z.id]?.setStyle({color:kc.stroke,fillColor:kc.fill,fillOpacity:Math.max(0.08,0.1+ks*0.08),weight:ks>=3?2:1,opacity:ks>=2?0.8:0.3});
      return;
    }
    circleMap[z.id]?.setStyle(getScoreStyle(s,z.type));
  });
}


// (дублираната bus система е премахната — виж BUS SCHEDULE по-долу)
function showTransitPopup(zid){
  const z = ZONES.find(x=>x.id===zid);
  if(!z) return;

  const fmt = (h,m) => String(h).padStart(2,'0')+':'+String(m).padStart(2,'0');

  let html = '<div style="font-size:14px;max-height:60vh;overflow-y:auto">';
  html += `<div style="font-weight:800;font-size:15px;margin-bottom:10px;color:var(--cyan)">${z.icon||'🚌'} ${z.name}</div>`;

  // Plovdiv buses arriving at Central Autogara (cab_north)
  if(zid === 'cab_north'){
    const arrivals = getSofiaArrivals(12);
    if(arrivals.length){
      html += '<div style="font-size:12px;font-weight:800;color:var(--muted);letter-spacing:.6px;margin-bottom:8px">🚌 ARRIVALS AT ZÜRICH HB</div>';
      arrivals.forEach(b=>{
        const untilArr = b.arrMin - b.nowMin; // minути до пристигане
        const isSoon = untilArr>=-5 && untilArr<=40;
        const bg = isSoon?'rgba(239,68,68,.1)':'transparent';
        const col = untilArr<=0?'var(--muted)':untilArr<=40?'#ef4444':untilArr<=90?'var(--amber)':'var(--muted)';
        const label = untilArr<=0?`arrived ~${b.arrTime}`:
                      untilArr<=90?`~${b.arrTime} · in ${untilArr} min`:
                      `~${b.arrTime}`;
        const origin = b.route.name.replace(' → Zürich','');
        html += `<div style="padding:6px 8px;border-radius:7px;background:${bg};margin-bottom:3px;display:flex;justify-content:space-between;gap:8px">
          <span style="font-weight:800;color:var(--text)">${origin} <span style="font-weight:400;color:var(--muted);font-size:11px">(${b.dep}${b.route.approx?' ≈':''})</span></span>
          <span style="font-size:12px;color:${col};text-align:right;white-space:nowrap">${label}</span>
        </div>`;
      });
    } else {
      html += '<div style="color:var(--muted);padding:8px">No arrivals in the coming hours / loading…</div>';
    }
    html += '<div style="font-size:11px;color:var(--muted);margin-top:8px;padding-top:6px;border-top:1px solid var(--border)">≈ schedule model per operator. Sorted by arrival time.</div>';
  }

  // Expo Center bus stop
  if(zid === 'iec' || zid === 'expo2000'){
    // Автобуси по Тракия, minаващи през Expo/Цариградско, по route stops offset
    const data = busSchedule;
    const now = new Date();
    const nowMin = now.getHours()*60 + now.getMinutes();
    const rows = [];
    for(const route of (data?.routes||[])){
      const expo = (route.stops||[]).find(s=>s.name.includes('Expo'));
      if(!expo || !route.to || !route.to.includes('Zürich HB')) continue;
      for(const dep of route.departures){
        const [h,m] = dep.split(':').map(Number);
        const atExpo = h*60+m+(expo.offset_min||0);
        let delta = atExpo - nowMin;
        if(delta < -10) continue;
        if(delta > 240) continue;
        rows.push({route, dep, atExpo, delta});
      }
    }
    rows.sort((a,b)=>a.atExpo-b.atExpo);
    if(rows.length){
      html += '<div style="font-size:12px;font-weight:800;color:var(--muted);letter-spacing:.6px;margin-bottom:8px">🚌 Passing corridors</div>';
      rows.slice(0,6).forEach(b=>{
        const t = `${String(Math.floor((b.atExpo%1440)/60)).padStart(2,'0')}:${String(b.atExpo%60).padStart(2,'0')}`;
        const origin = (b.route.name||'').replace(' → Zürich','');
        const col = b.delta<40?'#ef4444':'var(--amber)';
        html += `<div style="padding:6px 8px;border-radius:7px;margin-bottom:3px;display:flex;justify-content:space-between">
          <span>${origin} <span style="color:var(--muted);font-size:11px">${b.dep}${b.route.approx?' ≈':''}</span></span>
          <span style="font-weight:800;color:${col}">~${t}</span>
        </div>`;
      });
    }
  }

  // Generic transit info
  if(!['cab_north','iec','expo2000'].includes(zid)){
    html += '<div style="color:var(--muted);padding:8px 0">Transit hub zone. Schedules coming.</div>';
  }

  html += '</div>';

  L.popup({maxWidth:Math.min(340,window.innerWidth-30), className:'transit-popup'})
    .setLatLng([z.lat, z.lng])
    .setContent(html)
    .openOn(map);
}

// ═══ AIRPORT SCHEDULE POPUP ═══
function showAirportSchedule() {
  const now = new Date();
  const nowMin = ((now.getUTCHours()+3)%24)*60 + now.getUTCMinutes();

  const fmt = (h,m) => String(h).padStart(2,'0')+':'+String(m).padStart(2,'0');
  const flag = f => f.nonSchengen ? '🛂' : '🇪🇺';

  // Sort all details by exit start time
  const all = [...flightDetails].sort((a,b)=>{
    const am = a.exitFromH*60+a.exitFromM;
    const bm = b.exitFromH*60+b.exitFromM;
    return am-bm;
  });

  const upcoming=[], past=[];
  all.forEach(f=>{
    const exitTo = f.exitToH*60+f.exitToM;
    const exitFrom = f.exitFromH*60+f.exitFromM;
    // Handle midnight crossover - treat early morning hours as "next day"
    const toAdj   = exitTo   < 300 ? exitTo+1440   : exitTo;
    const fromAdj = exitFrom < 300 ? exitFrom+1440 : exitFrom;
    const nowAdj  = nowMin   < 300 ? nowMin+1440   : nowMin;
    // Show as upcoming if exit window ends in future (within last 15 min too)
    if(toAdj >= nowAdj - 15) upcoming.push(f);
    else past.push(f);
  });
  // If still nothing upcoming (cache is old/yesterday), show all as reference
  const cacheIsOld = upcoming.length === 0 && past.length > 0;

  let html='<div style="font-size:14px">';
  html+='<div style="font-weight:800;font-size:15px;margin-bottom:10px;color:var(--cyan)">✈️ Passenger exits — ZRH</div>';

  // Find truly next flights even if none "upcoming" now
  const allSorted = [...flightDetails].sort((a,b)=>(a.exitFromH*60+a.exitFromM)-(b.exitFromH*60+b.exitFromM));
  if(upcoming.length===0 || cacheIsOld){
    const next = allSorted.find(f=>{
      const fm=f.exitFromH*60+f.exitFromM;
      const adj=fm<300?fm+1440:fm;
      const na=nowMin<300?nowMin+1440:nowMin;
      return adj>na;
    });
    if(cacheIsOld){
      // Cache is from yesterday - show today's expected pattern
      html+=`<div style="background:rgba(245,197,24,.1);border:1px solid var(--amber);border-radius:10px;padding:12px;text-align:center;margin-bottom:10px">
        <div style="font-size:12px;color:var(--muted);margin-bottom:4px">⚠️ Cache refreshes at 08:00, 13:00, 18:00</div>
        <div style="font-size:13px;color:var(--amber)">Showing the typical arrival pattern</div>
      </div>`;
    } else if(next){
      html+=`<div style="background:rgba(2,132,199,.1);border:1px solid var(--cyan);border-radius:10px;padding:14px;text-align:center;margin-bottom:10px">
        <div style="font-size:13px;color:var(--muted);margin-bottom:4px">No passengers exiting right now</div>
        <div style="font-size:18px;font-weight:900;color:var(--cyan)">Next: ${String(next.exitFromH).padStart(2,'0')}:${String(next.exitFromM).padStart(2,'0')}</div>
        <div style="font-size:13px;color:var(--muted);margin-top:3px">${next.fn} от ${(next.depAirport||'').slice(0,20)} ${next.nonSchengen?'🛂':'🇪🇺'}</div>
      </div>`;
    } else if(past.length===0){
      if(airportStatus==='fallback'){
        html+='<div style="color:#f59e0b;padding:10px 0;text-align:center;font-size:12px">⚠️ No live flight data — forecast mode'+(window.__flErr?('<br><span style="color:#888;font-size:10px;word-break:break-all">debug: '+window.__flErr+'</span>'):'')+'</div>';
      } else {
        html+='<div style="color:var(--muted);padding:16px 0;text-align:center">Loading flights…</div>';
      }
    }
  }

  if(upcoming.length){
    html+='<div style="font-size:11px;font-weight:800;color:var(--muted);letter-spacing:.8px;margin-bottom:6px">UPCOMING / NOW</div>';
    upcoming.slice(0,12).forEach(f=>{
      const fromMin = f.exitFromH*60+f.exitFromM;
      const toMin   = f.exitToH*60+f.exitToM;
      const nowAdj  = nowMin<180?nowMin+1440:nowMin;
      const fromAdj = fromMin<180?fromMin+1440:fromMin;
      const toAdj   = toMin<180?toMin+1440:toMin;
      const isNow = fromAdj<=nowAdj && toAdj>=nowAdj;
      const isDone = toAdj < nowAdj;
      const bg = isNow?'rgba(239,68,68,.15)':'transparent';
      const brd = isNow?'1px solid rgba(239,68,68,.5)':'1px solid transparent';
      const col = isNow?'#ef4444': isDone?'var(--muted)':'var(--amber)';
      html+=`<div style="display:flex;align-items:center;gap:6px;padding:7px 8px;border-radius:8px;background:${bg};border:${brd};margin-bottom:3px">
        <span style="font-weight:800;font-size:13px;min-width:44px;color:var(--text)">${f.fn}</span>
        <span style="flex:1;font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${(f.depAirport||'').slice(0,22)}</span>
        <span style="font-size:14px">${flag(f)}</span>
        <span style="font-weight:800;font-size:13px;color:${col};white-space:nowrap">${fmt(f.exitFromH,f.exitFromM)}–${fmt(f.exitToH,f.exitToM)}</span>
      </div>`;
    });
  }

  if(past.length){
    const shown = past.slice(-4);
    html+=`<div style="font-size:11px;font-weight:800;color:var(--muted);letter-spacing:.8px;margin:10px 0 6px">ALREADY OUT (last ${shown.length})</div>`;
    shown.forEach(f=>{
      html+=`<div style="display:flex;align-items:center;gap:6px;padding:5px 8px;opacity:.45;font-size:12px">
        <span style="min-width:44px;font-weight:700">${f.fn}</span>
        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${(f.depAirport||'').slice(0,20)}</span>
        <span>${flag(f)}</span>
        <span style="white-space:nowrap">${fmt(f.exitFromH,f.exitFromM)}–${fmt(f.exitToH,f.exitToM)}</span>
      </div>`;
    });
  }

  html+='<div style="font-size:11px;color:var(--muted);margin-top:10px;padding-top:8px;border-top:1px solid var(--border)">🇪🇺 Schengen +15–25 min &nbsp;|&nbsp; 🛂 Non-Schengen +25–35 min</div>';
  html+='</div>';

  const airportZone=ZONES.find(z=>z.id==='airport');
  if(airportZone){
    L.popup({maxWidth:Math.min(340,window.innerWidth-30),maxHeight:Math.min(420,window.innerHeight*0.6),className:'airport-popup',autoPan:true})
      .setLatLng([airportZone.lat,airportZone.lng])
      .setContent(html)
      .openOn(map);
  }
}

function showZonePopup(zid) {
  const z=ZONES.find(x=>x.id===zid); if(!z) return;
  const {scores,activeEvents}=computeScores(currentHour);
  const s=scores[zid]||0;
  const isTraffic=z.type==='traffic';
  const ti=TRAFFIC_INFO[zid];
  let c, label, evHtml;
  if (karykMode&&!isTraffic) {
    const ks=computeKarykScore(zid,scores);
    c=karykColor(ks); label=`К:${ks.toFixed(1)} ${c.label}`;
  } else {
    c=demandColor(s,z.type); label=c.label;
  }
  if (isTraffic&&ti) {
    const active=s>=1.5;
    const sc=active?'#ef4444':'#22c55e';
    evHtml=`<div style="background:${active?'#1a0808':'#081a0d'};border:1px solid ${sc};border-radius:5px;padding:5px 8px;margin-bottom:5px;color:${sc};font-size:15px;font-weight:600">${active?'🔴 JAMMED NOW':'🟢 CLEAR RIGHT NOW'}</div>
      <div style="font-size:15px;color:#a855f7;margin-bottom:3px">🚦 ${ti.jamDir}</div>
      <div style="font-size:15px;color:#00e5ff;margin-bottom:5px">✅ Clear: ${ti.freeDir}</div>
      ${active?`<div style="background:#1a0a2e;border:1px solid #a855f7;border-radius:5px;padding:5px 8px;font-size:15px;color:#d08dff;margin-bottom:4px">💡 Drive ${ti.freeArrow} the other way — you'll get there faster!</div>`:''}
      <div style="font-size:14px;color:#4a6080">⏰ Peak: ${ti.time}</div>`;
  } else {
    const evs=(activeEvents[zid]||[]).slice(0,3);
    evHtml=evs.length?evs.map(e=>`<div>• ${e.name}</div>`).join(''):'<div style="color:#4a6080">Baseline demand</div>';
  }
  const pct=Math.min(100,(s/4.5)*100);
  L.popup({maxWidth:240}).setLatLng([z.lat,z.lng]).setContent(`
    <div style="font-family:'Share Tech Mono',monospace;font-size:16px;color:#00e5ff;margin-bottom:5px">${z.icon} ${z.name}</div>
    <div style="font-size:18px;font-weight:bold;color:${c.fill};margin-bottom:4px">${s.toFixed(1)} <span style="font-size:15px">${label}</span></div>
    <div style="height:4px;background:#182d47;border-radius:2px;margin:5px 0"><div style="width:${pct}%;height:100%;background:${c.fill};border-radius:2px"></div></div>
    <div style="font-size:15px;color:#c8daf0;margin:6px 0">${evHtml}</div>
    ${!isTraffic?`<button onclick="startNav('${zid}')" style="width:100%;background:#00e5ff;color:#000;border:none;border-radius:4px;padding:5px;font-size:15px;cursor:pointer;margin-top:4px">🧭 Navigate</button>
    <div style="display:flex;gap:5px;margin-top:5px">
      <a href="https://waze.com/ul?q=${encodeURIComponent(z.wazeName||z.name)}&navigate=yes" target="_blank"
         style="flex:1;text-align:center;font-size:14px;color:#00e5ff;padding:4px;background:#0d1929;border:1px solid #182d47;border-radius:4px;text-decoration:none">🚗 Waze</a>
      <a href="https://www.google.com/maps?q=${z.lat},${z.lng}" target="_blank"
         style="flex:1;text-align:center;font-size:14px;color:#4a6080;padding:4px;background:#0d1929;border:1px solid #182d47;border-radius:4px;text-decoration:none">📍 Google</a>
    </div>`:''}
  `).openOn(map);
}
window.startNav=function(zid){
  const z=ZONES.find(x=>x.id===zid); if(!z) return;
  navTarget=z; map.closePopup();
  window.open(`https://waze.com/ul?q=${encodeURIComponent(z.wazeName||z.name)}&navigate=yes`,'_blank');
};

// ═══════════════════════════════════════════════
// SPARKLINE
// ═══════════════════════════════════════════════
const canvas=document.getElementById('demand-canvas');
const ctx=canvas.getContext('2d');
const MIN_H=6, MAX_H=24, STEPS=72;

function buildCurve() {
  demandCurve=[];
  for(let i=0;i<=STEPS;i++) demandCurve.push(totalDemand(MIN_H+(i/STEPS)*(MAX_H-MIN_H)));
}

function drawSparkline(h) {
  const dpr=window.devicePixelRatio||1;
  const W=Math.max(canvas.offsetWidth,canvas.parentElement?.offsetWidth||300);
  const H=40;
  canvas.width=W*dpr; canvas.height=H*dpr; ctx.scale(dpr,dpr);
  if(!demandCurve.length) return;
  const maxD=Math.max(...demandCurve), minD=Math.min(...demandCurve)*0.85;
  const xOf=i=>(i/STEPS)*W;
  const yOf=v=>H-3-((v-minD)/(maxD-minD))*(H-8);
  // Dead zone shade
  const x20=((20-MIN_H)/(MAX_H-MIN_H))*W;
  const x21=((21-MIN_H)/(MAX_H-MIN_H))*W;
  ctx.fillStyle='rgba(239,68,68,0.08)'; ctx.fillRect(x20,0,x21-x20,H);
  // Red bands for airport exit windows
  if(flightDetails && flightDetails.length) {
    flightDetails.forEach(f=>{
      const x1=((f.exitFromH + f.exitFromM/60 - MIN_H)/(MAX_H-MIN_H))*W;
      const x2=((f.exitToH   + f.exitToM/60   - MIN_H)/(MAX_H-MIN_H))*W;
      if(x2>0 && x1<W) {
        ctx.fillStyle='rgba(239,68,68,0.18)';
        ctx.fillRect(Math.max(0,x1),0,Math.min(W,x2)-Math.max(0,x1),H);
      }
    });
  }
  // Fill
  const grad=ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,'rgba(239,68,68,0.28)');
  grad.addColorStop(0.5,'rgba(245,158,11,0.14)');
  grad.addColorStop(1,'rgba(34,197,94,0.02)');
  ctx.beginPath(); ctx.moveTo(xOf(0),yOf(demandCurve[0]));
  for(let i=1;i<=STEPS;i++) ctx.lineTo(xOf(i),yOf(demandCurve[i]));
  ctx.lineTo(W,H); ctx.lineTo(0,H); ctx.closePath();
  ctx.fillStyle=grad; ctx.fill();
  ctx.beginPath(); ctx.moveTo(xOf(0),yOf(demandCurve[0]));
  for(let i=1;i<=STEPS;i++) ctx.lineTo(xOf(i),yOf(demandCurve[i]));
  ctx.strokeStyle='#f59e0b99'; ctx.lineWidth=1.5; ctx.stroke();
  // Cursor
  const cx=((h-MIN_H)/(MAX_H-MIN_H))*W;
  ctx.beginPath(); ctx.moveTo(cx,0); ctx.lineTo(cx,H);
  ctx.strokeStyle='#00e5ff'; ctx.lineWidth=1.5; ctx.setLineDash([3,3]); ctx.stroke(); ctx.setLineDash([]);
  const ci=Math.round(((h-MIN_H)/(MAX_H-MIN_H))*STEPS);
  ctx.beginPath(); ctx.arc(cx,yOf(demandCurve[Math.min(ci,STEPS)]),4,0,Math.PI*2);
  ctx.fillStyle='#00e5ff'; ctx.fill();
}

// ═══════════════════════════════════════════════
// RENDER
// ═══════════════════════════════════════════════
function render(hour) {
  const {scores,activeEvents}=computeScores(hour);
  const dead=hour>=19.8&&hour<=21.2;
  document.getElementById('tl-dead').style.display=dead?'inline':'none';
  updateCircles();
  drawSparkline(hour);
  // Sidebar
  const sorted=Object.entries(scores).sort((a,b)=>b[1]-a[1]);
  const top=sorted[0];
  const tz=ZONES.find(z=>z.id===top[0]);
  document.getElementById('tl-hint').textContent=
    dead?'— dead zone, take a break':`Top: ${tz?.icon||''} ${tz?.name||top[0]} (${top[1].toFixed(1)})`;
  const zList=document.getElementById('zone-list');
  if (zList && !karykMode) {
    zList.innerHTML=sorted
      .filter(([zid])=>{ const z=ZONES.find(x=>x.id===zid); return z&&z.type!=='karyk'; })
      .map(([zid,score])=>{
        const z=ZONES.find(x=>x.id===zid); if(!z) return '';
        const c=demandColor(score,z.type);
        const sub=(activeEvents[zid]||[])[0]?.name||'';
        return `<div class="zone-item" onclick="(function(){if(document.body.classList.contains('list-view'))toggleMapView();setTimeout(()=>{map.setView([${z.lat},${z.lng}],'${zid}'==='airport'?14:15);'${zid}'==='airport'?showAirportSchedule():showZonePopup('${zid}');},150);})()">
          <div class="zone-dot" style="background:${c.fill}"></div>
          <div style="flex:1;min-width:0">
            <div class="zone-name">${z.icon} ${z.name}</div>
            ${sub?`<div class="zone-sub">${sub}</div>`:''}
          </div>
          <div style="text-align:right">
            <div class="zone-score" style="color:${c.fill};font-size:16px;font-weight:800">${score.toFixed(1)}</div>
            <div style="font-size:11px;color:${c.fill}">${c.label}</div>
          </div>
        </div>`;
      }).join('');
  }
  const kList=document.getElementById('karyk-list');
  if (kList && karykMode) {
    const ranked=ZONES
      .filter(z=>z.type!=='hospital')
      .map(z=>({z,ks:computeKarykScore(z.id,scores),ev:(activeEvents[z.id]||[])[0]?.name||''}))
      .filter(({ks})=>ks>=1.0)
      .sort((a,b)=>b.ks-a.ks).slice(0,20);
    kList.innerHTML=ranked.map(({z,ks,ev},i)=>{
      const c=karykColor(ks);
      const reason=ev||(z.type==='karyk'?'Quiet district':z.type==='residential_lux'?'Upscale district':'');
      return `<div class="karyk-item" onclick="(function(){if(document.body.classList.contains('list-view'))toggleMapView();setTimeout(function(){map.invalidateSize();map.setView([${z.lat},${z.lng}],15);showZonePopup('${z.id}');},200);})()">
        <div class="karyk-rank" style="color:${c.fill}">#${i+1}</div>
        <div class="karyk-dot" style="background:${c.fill}"></div>
        <div style="flex:1;min-width:0">
          <div class="karyk-name">${z.icon} ${z.name.split('(')[0].trim()}</div>
          <div class="karyk-sub">${c.label}${reason?' · '+reason:''}</div>
        </div>
        <div style="text-align:right">
          <div class="karyk-score" style="color:${c.fill}">К:${ks.toFixed(1)}</div>
          <div style="font-size:14px;color:#5a3a10">↑${scores[z.id]?.toFixed(1)||'0.0'}</div>
        </div>
      </div>`;
    }).join('');
  }
}

// ═══════════════════════════════════════════════
// GPS
// ═══════════════════════════════════════════════
function deg2rad(d){return d*Math.PI/180;}
function haversine(lat1,lng1,lat2,lng2){
  const R=6371000,dLat=deg2rad(lat2-lat1),dLng=deg2rad(lng2-lng1);
  const a=Math.sin(dLat/2)**2+Math.cos(deg2rad(lat1))*Math.cos(deg2rad(lat2))*Math.sin(dLng/2)**2;
  return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}
function bearing(lat1,lng1,lat2,lng2){
  const dLng=deg2rad(lng2-lng1);
  const y=Math.sin(dLng)*Math.cos(deg2rad(lat2));
  const x=Math.cos(deg2rad(lat1))*Math.sin(deg2rad(lat2))-Math.sin(deg2rad(lat1))*Math.cos(deg2rad(lat2))*Math.cos(dLng);
  return (Math.atan2(y,x)*180/Math.PI+360)%360;
}
const ARROWS=['⬆️','↗️','➡️','↘️','⬇️','↙️','⬅️','↖️'];
const DIRS  =['N','NE','E','SE','S','SW','W','NW'];

if(window.DeviceOrientationEvent){
  window.addEventListener('deviceorientationabsolute',e=>{deviceHeading=e.alpha;},true);
  window.addEventListener('deviceorientation',e=>{if(e.webkitCompassHeading)deviceHeading=e.webkitCompassHeading;},true);
}

function updateDirectionHint(scores) {
  if(userLat===null||dirHintSuppressed) return;
  let best=null,bestW=Infinity;
  ZONES.forEach(z=>{
    const s=scores[z.id]||0; if(s<1.6) return;
    const d=haversine(userLat,userLng,z.lat,z.lng);
    const w=d/(s*s);
    if(w<bestW){bestW=w;best=z;}
  });
  const panel=document.getElementById('direction-hint');
  if(!best){panel.style.display='none';return;}
  if(best.id===dirHintZid&&panel.style.display!=='none') return;
  dirHintZid=best.id;
  const {scores:sc}=computeScores(currentHour);
  const bs=sc[best.id]||0;
  const dist=haversine(userLat,userLng,best.lat,best.lng);
  const bear=bearing(userLat,userLng,best.lat,best.lng);
  let relBear=bear;
  if(deviceHeading!==null) relBear=(bear-deviceHeading+360)%360;
  const c=demandColor(bs,best.type);
  const distTxt=dist<1000?`${Math.round(dist)} m`:`${(dist/1000).toFixed(1)} km`;
  document.getElementById('dh-arrow').textContent=ARROWS[Math.round(relBear/45)%8];
  document.getElementById('dh-name').textContent=`${best.icon} ${best.name}`;
  document.getElementById('dh-addr').textContent=`${DIRS[Math.round(bear/45)%8]} · ${distTxt}`;
  document.getElementById('dh-score').textContent=bs.toFixed(1);
  document.getElementById('dh-score').style.color=c.fill;
  panel.style.display='block';
  panel.style.borderTopColor=c.fill;
  if(window._dirLine) map.removeLayer(window._dirLine);
  window._dirLine=L.polyline([[userLat,userLng],[best.lat,best.lng]],{color:c.fill,weight:2,dashArray:'6,4',opacity:0.9}).addTo(map);
}

function startGPS(){
  const btn=document.getElementById('gps-btn');
  btn.classList.add('active');
  if(!navigator.geolocation){return;}
  if(watchId) return;
  document.getElementById('direction-hint').style.display='block';
  document.getElementById('dh-name').textContent='🛰 Waiting for GPS…';
  document.getElementById('dh-arrow').textContent='📡';
  watchId=navigator.geolocation.watchPosition(pos=>{
    userLat=pos.coords.latitude; userLng=pos.coords.longitude;
    if(!userMarker){
      const icon=L.divIcon({className:'',
        html:`<div style="position:relative;width:24px;height:24px">
          <div style="position:absolute;inset:0;border-radius:50%;background:rgba(0,229,255,.2);animation:pulse-ring 3s ease-out infinite"></div>
          <div style="position:absolute;inset:5px;border-radius:50%;background:#00e5ff;border:2px solid #fff;box-shadow:0 0 8px #00e5ff"></div>
        </div>`,iconSize:[24,24],iconAnchor:[12,12]});
      userMarker=L.marker([userLat,userLng],{icon,zIndexOffset:1000}).addTo(map);
      map.setView([userLat,userLng],14);
    } else {
      userMarker.setLatLng([userLat,userLng]);
    }
    // Update airport badge to show GPS is active
    document.getElementById('gps-btn').title=`📍 ${userLat.toFixed(4)}, ${userLng.toFixed(4)}`;
    const {scores}=computeScores(currentHour);
    updateDirectionHint(scores);
  },()=>{btn.classList.remove('active');},{enableHighAccuracy:true,maximumAge:5000,timeout:15000});
}

document.getElementById('gps-btn').addEventListener('click',()=>{
  if(watchId){
    navigator.geolocation.clearWatch(watchId); watchId=null;
    document.getElementById('gps-btn').classList.remove('active');
    if(userMarker){map.removeLayer(userMarker);userMarker=null;}
    if(window._dirLine){map.removeLayer(window._dirLine);window._dirLine=null;}
    document.getElementById('direction-hint').style.display='none';
    userLat=null; userLng=null;
  } else { startGPS(); }
});
document.getElementById('direction-hint').querySelector('.dh-close').addEventListener('click',()=>{
  dirHintSuppressed=true;
  document.getElementById('direction-hint').style.display='none';
});

// ═══════════════════════════════════════════════
// FULLSCREEN
// ═══════════════════════════════════════════════
let isFullscreen=false;
document.getElementById('fs-btn').addEventListener('click',()=>{
  isFullscreen=!isFullscreen;
  document.body.classList.toggle('map-fullscreen',isFullscreen);
  document.getElementById('fs-btn').textContent=isFullscreen?'✕':'⛶';
  setTimeout(()=>{map.invalidateSize();drawSparkline(currentHour);},200);
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&isFullscreen)document.getElementById('fs-btn').click();});

// ═══════════════════════════════════════════════
// КАРЪК MODE
// ═══════════════════════════════════════════════
const karykBtn=document.getElementById('karyk-btn');
karykBtn.addEventListener('click',()=>{
  karykMode=!karykMode;
  karykBtn.classList.toggle('active',karykMode);
  document.body.classList.toggle('karyk-active',karykMode);
  document.getElementById('karyk-banner').style.display=karykMode?'block':'none';
  if(karykMode){
    const {scores}=computeScores(currentHour);
    const gems=ZONES.filter(z=>z.type==='karyk'||z.type==='residential_lux'||z.type==='residential')
      .map(z=>({z,ks:computeKarykScore(z.id,scores)})).sort((a,b)=>b.ks-a.ks);
    if(gems[0]){
      const c=karykColor(gems[0].ks);
      document.getElementById('karyk-hint').innerHTML=
        `🥉 Go to <span style="color:${c.fill}">${gems[0].z.icon} ${gems[0].z.name.split('(')[0].trim()}</span> (К:${gems[0].ks.toFixed(1)})`;
    }
  }
  render(currentHour);
});

// ═══════════════════════════════════════════════
// TICKER
// ═══════════════════════════════════════════════
function buildTicker(){
  const zMap={}; ZONES.forEach(z=>{zMap[z.id]=z;});
  const items=EVENTS.filter(dayMatches).sort((a,b)=>a.endHour-b.endHour).map(ev=>{
    const z=zMap[ev.zone]; if(!z) return '';
    return `<span class="tick-item"><span class="ev-time">${fmtHour(ev.endHour)}</span> ${ev.name} <span class="ev-loc">@ ${z.name.split('(')[0].trim()}</span> <span style="color:#0f2040"> ·· </span></span>`;
  }).filter(Boolean);
  const el=document.getElementById('ticker');
  el.innerHTML=items.join('')+items.join('');
  el.style.animation='none'; el.offsetHeight; el.style.animation='';
}

// ═══════════════════════════════════════════════
// FLIGHT-CACHE.JSON
// ═══════════════════════════════════════════════
function injectAirportEvents(){
  const keep=EVENTS.filter(e=>!e._fromFlight);
  for(let h=0;h<24;h++){
    const c=flightHours[h]; if(!c) continue;
    keep.push({zone:'airport',name:`✈ ${c} flights ~${String(h).padStart(2,'0')}:00`,
      endHour:h+0.25,boost:Math.min(3.8,c*0.42),repeat:'daily',_fromFlight:true});
  }
  EVENTS.length=0; keep.forEach(e=>EVENTS.push(e));
}

function applyFallbackAirport(){
  airportStatus='fallback';
  [[5,3],[6,8],[7,10],[8,9],[9,8],[10,9],[11,10],[12,8],[13,9],[14,8],[15,10],[16,11],
   [17,10],[18,9],[19,8],[20,7],[21,6],[22,4],[23,2]].forEach(([h,c])=>{flightHours[h]=c;});
  injectAirportEvents();
}

function updateAirportBadge(){
  const b=document.getElementById('airport-badge');
  if(airportStatus==='live')        {b.textContent='✈ LIVE';     b.style.color='#22c55e';}
  else if(airportStatus==='fallback'){b.textContent='✈ FORECAST';b.style.color='#f59e0b';}
  else                              {b.textContent='✈ OFFLINE';  b.style.color='#ef4444';}
}

function loadFlights(){
  fetch('flight-cache.json?v='+Date.now())
    .then(r=>{if(!r.ok)throw 0;return r.json();})
    .then(data=>{
      const fl=data.data||[]; if(!fl.length) throw 0;
      flightHours=Array(24).fill(0); flightDetails=[];
      fl.forEach(f=>{
        if(!f.arrival?.scheduled) return;
        const t=new Date(f.arrival.estimated||f.arrival.scheduled);
        const dep=(f.departure?.airport||f.departure?.country_name||'').toLowerCase();
        const nonSchengen=dep.match(/tur|istanbul|sabiha|ankar|israel|ben.gurion|dubai|abu.dhabi|egypt|cairo|morocco|casablanca|london|heathrow|gatwick|stansted|luton|manchester|birmingham|usa|jfk|lax|china|beijing|shanghai|russia|moscow|georgia|tbilisi|armenia|yerevan|jordan|amman|serbia|belgrade|ukraine|kyiv|north.mac/);
        // Exit window: first passenger at +15/25 min, last at +25/35 min
        const exitFirst = nonSchengen ? 25 : 15;
        const exitLast  = nonSchengen ? 35 : 25;
        const tFirst = new Date(t.getTime() + exitFirst*60000);
        const tLast  = new Date(t.getTime() + exitLast*60000);
        const hFirst = (tFirst.getUTCHours()+3)%24;
        const hLast  = (tLast.getUTCHours()+3)%24;
        const mFirst = tFirst.getUTCMinutes();
        const mLast  = tLast.getUTCMinutes();
        // Spread passengers across exit window (3 slots: start, mid, end)
        const hMid = (new Date(t.getTime()+(exitFirst+exitLast)/2*60000).getUTCHours()+3)%24;
        flightHours[hFirst] = (flightHours[hFirst]||0) + 0.3;
        flightHours[hMid]   = (flightHours[hMid]||0)   + 0.5;
        flightHours[hLast]  = (flightHours[hLast]||0)  + 0.2;
        // Store for popup
        const fn = (f.flight?.iata||'??');
        const depAirport = f.departure?.airport||dep;
        flightDetails.push({
          fn, depAirport, nonSchengen:!!nonSchengen,
          landH:(t.getUTCHours()+3)%24, landM:t.getUTCMinutes(),
          exitFromH:hFirst, exitFromM:mFirst,
          exitToH:hLast,   exitToM:mLast
        });
      });
      console.log('[SOF] flightDetails populated:', flightDetails.length, 'flights');
      airportStatus='live';
      injectAirportEvents(); updateAirportBadge();
      buildCurve(); buildTicker(); render(currentHour);
    })
    .catch(e=>{
      window.__flErr = (e && (e.stack||e.message)) ? String(e.stack||e.message).slice(0,160) : ('code '+String(e));
      console.error('[SOF] flights failed:', e);
      applyFallbackAirport(); updateAirportBadge();
      buildCurve(); buildTicker(); render(currentHour);
    });
}

// ═══════════════════════════════════════════════
// WEATHER
// ═══════════════════════════════════════════════
let OWM_KEY = '';

async function loadConfig(){
  try {
    const r = await fetch('config.json');
    const d = await r.json();
    OWM_KEY = d.owm_key || '';
  } catch(e) {}
}

async function loadWeather(){
  const bar=document.getElementById('weather-bar');
  if(!OWM_KEY){
    bar.style.display='flex';
    document.getElementById('wb-desc').textContent='Add OWM key in config.json';
    return;
  }
  try{
    const r=await fetch(`https://api.openweathermap.org/data/2.5/weather?lat=47.3769&lon=8.5417&units=metric&lang=bg&appid=${OWM_KEY}`);
    const d=await r.json();
    if(d.cod!==200) throw 0;
    const w=d.weather[0], temp=Math.round(d.main.temp), wind=d.wind?.speed||0;
    const icons={'Rain':'🌧','Drizzle':'🌦','Thunderstorm':'⛈','Snow':'❄️','Fog':'🌫','Mist':'🌫'};
    const wIcon=icons[w.main]||'☀️';
    const boost=w.main==='Rain'?2.0:w.main==='Thunderstorm'?2.8:w.main==='Snow'?1.8:w.main==='Drizzle'?1.2:wind>10?0.5:0;
    weatherBoost=boost;
    bar.style.display='flex';
    document.getElementById('wb-icon').textContent=wIcon;
    document.getElementById('wb-temp').textContent=`${temp}°C`;
    document.getElementById('wb-desc').textContent=w.description;
    document.getElementById('wb-boost').textContent=boost>0?`+${boost.toFixed(1)} demand 🌧`:'';
    if(boost>0){bar.style.borderBottomColor='#00e5ff'; buildCurve(); render(currentHour);}
  }catch(e){console.warn('Weather error',e);}
}

// ═══════════════════════════════════════════════
// SLIDER + AUTO TIME
// ═══════════════════════════════════════════════
const slider=document.getElementById('time-slider');
slider.addEventListener('input',()=>{
  autoTime=false; clearTimeout(slider._t);
  slider._t=setTimeout(()=>{autoTime=true;},10*60000);
  currentHour=parseFloat(slider.value);
  const td=document.getElementById('time-display');
  td.textContent=fmtHour(currentHour);
  // Показва дали е реален час или симулация
  const realH=new Date().getHours()+new Date().getMinutes()/60;
  const isSim=Math.abs(currentHour-realH)>0.4;
  td.style.color = isSim ? '#f59e0b' : 'var(--cyan)';
  td.title = isSim ? '⏱ Simulation — not real time' : '';
  render(currentHour);
  // Обновява панелите ако са отворени
  if(bakshishOpen) buildBakshishPanel();
  if(next90Open) buildNext90();
  checkEventAlerts();
});

function syncTime(){
  if(!autoTime) return;
  const h=new Date().getHours()+new Date().getMinutes()/60;
  const sn=Math.round(h*2)/2;
  if(Math.abs(sn-currentHour)>=0.25){
    currentHour=sn; slider.value=sn;
    document.getElementById('time-display').textContent=fmtHour(sn);
    render(sn);
  }
}
setInterval(syncTime,60000);

// ═══════════════════════════════════════════════
// EVENT ALERT — 15-30 min преди голям event
// ═══════════════════════════════════════════════
function checkEventAlerts(){
  // Event alerts използват реалния час (не slider) - за реални предупреждения
  const realH=new Date().getHours()+new Date().getMinutes()/60;
  // Но ако slider е близо до реалния час (±30мин), показваме и preview
  const h=Math.abs(currentHour-realH)<0.5 ? realH : currentHour;
  const upcoming=EVENTS.filter(ev=>dayMatches(ev)&&!ev._fromFlight).filter(ev=>{
    const diff=ev.endHour-h;
    return diff>=0.25&&diff<=0.5&&ev.boost>=2.0&&!alertedEvents.has(ev.name+ev.endHour);
  }).sort((a,b)=>a.endHour-b.endHour);
  const panel=document.getElementById('event-alert');
  if(!upcoming.length){panel.style.display='none';return;}
  const ev=upcoming[0], z=ZONES.find(x=>x.id===ev.zone);
  if(!z) return;
  const min=Math.round((ev.endHour-h)*60);
  document.getElementById('ea-icon').textContent=z.icon;
  document.getElementById('ea-title').textContent=`${ev.name} — in ${min} min!`;
  document.getElementById('ea-sub').textContent=`${z.name.split('(')[0].trim()} · ${fmtHour(ev.endHour)}`;
  document.getElementById('ea-dist').textContent=userLat?`📏 ${(haversine(userLat,userLng,z.lat,z.lng)/1000).toFixed(1)} km`:'';
  document.getElementById('ea-waze').onclick=()=>window.open(`https://waze.com/ul?q=${encodeURIComponent(z.wazeName||z.name)}&navigate=yes`,'_blank');
  panel.style.display='block';
}
setInterval(checkEventAlerts,60000);
document.getElementById('event-alert').querySelector('.ea-close').addEventListener('click',()=>{
  const h=currentHour;
  EVENTS.filter(ev=>dayMatches(ev)&&!ev._fromFlight).filter(ev=>{
    const diff=ev.endHour-h; return diff>=0.25&&diff<=0.5&&ev.boost>=2.0;
  }).forEach(ev=>alertedEvents.add(ev.name+ev.endHour));
  document.getElementById('event-alert').style.display='none';
});

// ═══════════════════════════════════════════════
// 🎩 TIP RADAR
// Смени и бакшиш score по тип клиент/зона/час

// ═══════════════════════════════════════════════
// BUS SCHEDULE
// ═══════════════════════════════════════════════
let busSchedule = null;

async function loadBuses(){
  try{
    const r = await fetch('bus-schedule.json');
    if(!r.ok) return;
    busSchedule = await r.json();
    renderBusPanel();
    addBusZones();
  }catch(e){ console.warn('Bus schedule:', e.message); }
}

function getNextBuses(routeId, count=5){
  if(!busSchedule) return [];
  const route = busSchedule.routes.find(r => r.id === routeId);
  if(!route) return [];
  const now = new Date();
  const nowMin = now.getHours()*60 + now.getMinutes();
  const results = [];
  for(const dep of route.departures){
    const [h,m] = dep.split(':').map(Number);
    const depMin = h*60+m;
    const diff = depMin - nowMin;
    if(diff >= -10){ // include buses that left up to 10min ago (may still be picking up)
      const arrMin = depMin + route.duration_min;
      results.push({
        dep, depMin,
        arr: `${Math.floor(arrMin/60).toString().padStart(2,'0')}:${(arrMin%60).toString().padStart(2,'0')}`,
        diffMin: diff,
        route
      });
    }
    if(results.length >= count) break;
  }
  return results;
}

// Всички пристигащи на ЦАС от всички маршрути, сортирани по час на пристигане
let liveArrivals = null;

async function loadLiveArrivals(){
  try{
    const r = await fetch('bus-arrivals.json?v='+Date.now());
    if(!r.ok) return;
    const d = await r.json();
    // валидни само ако са свежи (<100 min)
    if(d.updated && (Date.now()-new Date(d.updated).getTime()) < 100*60000){
      liveArrivals = d;
    }
  }catch(e){ /* няма live файл — оставаме на разписание */ }
}

function getLiveArrivals(count){
  if(!liveArrivals) return [];
  const now = new Date();
  const nowMin = now.getHours()*60 + now.getMinutes();
  const out = [];
  for(const a of (liveArrivals.arrivals||[])){
    const [h,m] = a.time.split(':').map(Number);
    if(isNaN(h)||isNaN(m)) continue;
    let delta = h*60+m - nowMin;
    if(delta < -20) continue;
    out.push({origin:a.from, operator:a.operator, arrTime:a.time, until:delta, live:true});
  }
  return out.slice(0, count||10);
}

function getSofiaArrivals(count){ return []; 
  const data = busSchedule;
  if(!data) return [];
  const now = new Date();
  const nowMin = now.getHours()*60 + now.getMinutes();
  const fmt2 = mm => String(Math.floor((mm%1440)/60)).padStart(2,'0')+':'+String(mm%60).padStart(2,'0');
  const out = [];
  for(const route of (data.routes||[])){
    if(!route.to || !route.to.includes('Zürich HB')) continue;
    const dur = route.duration_min || 120;
    for(const dep of route.departures){
      const [h,m] = dep.split(':').map(Number);
      const depMin = h*60+m;
      const arrAbs = depMin + dur;
      let delta = arrAbs - nowMin;
      if(delta < -15) delta += 1440; // след полунощ / утрешен
      if(delta <= 360){ // от -15 min до +6 часа
        out.push({dep, depMin, route, nowMin, arrMin: nowMin+delta, arrTime: fmt2(arrAbs)});
      }
    }
  }
  out.sort((a,b)=>a.arrMin-b.arrMin);
  return out.slice(0, count||10);
}

function renderBusPanel(){
  // Find or create bus panel in sidebar
  let panel = document.getElementById('bus-panel');
  if(!panel){
    const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar') || document.querySelector('.panel-list');
    if(!sidebar) return;
    panel = document.createElement('div');
    panel.id = 'bus-panel';
    panel.style.cssText = 'background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px;margin:8px 0;';
    sidebar.appendChild(panel);
  }

  const live = getLiveArrivals(6);
  const arrivals = getSofiaArrivals(live.length ? 4 : 8);

  let html = '<div style="font-size:14px;font-weight:800;color:var(--cyan);margin-bottom:8px">🚌 Arrivals at HB</div>';

  if(live.length){
    html += '<div style="font-size:11px;font-weight:800;color:#ef4444;margin-bottom:4px">🔴 LIVE — centralnaavtogara.bg</div>';
    for(const b of live){
      const urgency = b.until <= 15 ? 'color:#ef4444;font-weight:800' : 'color:var(--text)';
      html += `<div style="display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-bottom:1px solid var(--border);font-size:13px">
        <span>🚌 ${b.origin} <span style="color:var(--muted);font-size:11px">${b.operator||''}</span></span>
        <span style="${urgency};white-space:nowrap">${b.arrTime}${b.until>=0?' · in '+b.until+' min':''}</span>
      </div>`;
    }
    html += '<div style="font-size:11px;font-weight:800;color:var(--muted);margin:8px 0 4px">📋 Scheduled</div>';
  }

  if(arrivals.length){
    for(const b of arrivals){
      const until = b.arrMin - b.nowMin;
      const urgency = until <= 0 ? 'color:#ef4444;font-weight:800' : until < 40 ? 'color:#f59e0b;font-weight:800' : 'color:var(--text)';
      const origin = (b.route.name||'').replace(' → Zürich','');
      const label = until <= 0 ? `arrived ~${b.arrTime}` :
                    until < 90 ? `~${b.arrTime} · in ${until} min` :
                    `~${b.arrTime}`;
      html += `<div style="display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-bottom:1px solid var(--border);font-size:13px">
        <span>🚌 ${origin} <span style="color:var(--muted);font-size:11px">${b.dep}${b.route.approx?' ≈':''}</span></span>
        <span style="${urgency};white-space:nowrap">${label}</span>
      </div>`;
    }
  } else {
    html += '<div style="color:var(--muted);font-size:12px">No arrivals in the next 6 hours</div>';
  }

  html += '<div style="margin-top:8px;font-size:11px;color:var(--muted)">≈ schedule model per operator</div>';
  panel.innerHTML = html;

  // Update every minute
  setTimeout(renderBusPanel, 60000);
}

function addBusZones(){
  var M = (typeof map!=='undefined' && map && typeof map.addLayer==='function') ? map : null;
  if(!busSchedule || !M) return;
  // Add Expo Center bus stop as zone marker
  const expoStop = {lat:42.6543, lng:23.4012, name:'🚌 Bus terminal'};
  const icon = L.divIcon({
    className:'',
    html:`<div style="background:#0284c7;color:#fff;border-radius:6px;padding:3px 7px;font-size:12px;font-weight:800;white-space:nowrap;box-shadow:0 2px 6px #0004">🚌 Expo</div>`,
    iconAnchor:[25,15]
  });
  L.marker([expoStop.lat, expoStop.lng], {icon})
    .addTo(M)
    .bindPopup(`<b style="color:#0284c7">🚌 Expo Center</b><br><small>Inbound A1: Bern · Basel corridor</small>`);
  // Коридорни входове — къде влизат междуградските автобуси в София
  const corridors = [
    {lat:42.7208, lng:23.4085, short:'🚌 A1', pop:'<b style="color:#0284c7">🚌 North corridor</b><br><small>Inbound A4: Winterthur · St. Gallen</small>'},
    {lat:42.6520, lng:23.2800, short:'🚌 A3', pop:'<b style="color:#0284c7">🚌 West corridor</b><br><small>Inbound A3: Chur · Zug</small>'},
  ];
  corridors.forEach(c=>{
    const ci = L.divIcon({className:'',
      html:`<div style="background:#0284c7;color:#fff;border-radius:6px;padding:3px 7px;font-size:12px;font-weight:800;white-space:nowrap;box-shadow:0 2px 6px #0004">${c.short}</div>`,
      iconAnchor:[25,15]});
    L.marker([c.lat, c.lng], {icon:ci}).addTo(M).bindPopup(c.pop);
  });
}

// ═══════════════════════════════════════════════

const SHIFTS = {
  morning:   { name:"🌅 Morning shift (08–11)",    hours:[8,11],
    tip:"Business travellers, airport transfers, medical appointments. Upscale districts head out.",
    clientType:"business / tourist / patient" },
  midday:    { name:"☀️ Midday shift (11–16)",       hours:[11,16],
    tip:"Tourists strolling, business lunches, post-appointments. Hotel clients with luggage. Corporate cards.",
    clientType:"tourist / business lunch" },
  afternoon: { name:"🌆 Afternoon shift (16–20)",  hours:[16,20],
    tip:"Offices let out. Theatre and opera after 19h. Doubles in rain.",
    clientType:"office worker / theatre-goer" },
  evening:   { name:"🌙 Evening shift (20–02)",     hours:[20,26],
    tip:"After dinner. After concerts — emotional peak. 5* hotels at night — corporate.",
    clientType:"restaurant guest / night" },
  night:     { name:"🌃 Night shift (02–08)",       hours:[2,8],
    tip:"Last club guests. Airport — early flights. Hotel arrivals.",
    clientType:"night guest / early flight" },
};

function getCurrentShift(h) {
  if (h >= 8  && h < 11) return 'morning';
  if (h >= 11 && h < 16) return 'midday';
  if (h >= 16 && h < 20) return 'afternoon';
  if (h >= 20 || h <  2) return 'evening';
  return 'night';
}

// Бакшиш фактори по тип зона за всяка смяна
const BAKSHISH_WEIGHTS = {
  morning: {
    airport:3.5, hotel:3.0, residential_lux:2.8, hospital:2.2,
    office:1.5, transit:2.0, mall:1.0, university:0.8,
    theatre:0.5, cinema:0.5, nightlife:0.2, karyk:1.8,
  },
  midday: {
    airport:2.8, hotel:3.2, restaurant:2.5, mall:1.8,
    hospital:1.8, office:1.2, transit:1.5, residential_lux:1.5,
    university:1.0, theatre:0.8, nightlife:0.5, karyk:1.2,
  },
  afternoon: {
    office:3.0, theatre:3.5, airport:2.5, hotel:2.0,
    mall:2.0, residential_lux:2.2, transit:1.8,
    hospital:1.5, university:1.5, nightlife:1.0, karyk:2.0,
  },
  evening: {
    theatre:4.0, nightlife:3.5, hotel:3.5, airport:2.8,
    restaurant:3.8, residential_lux:2.5, mall:1.5,
    transit:1.5, hospital:1.0, office:0.5, karyk:2.5,
  },
  night: {
    nightlife:4.5, airport:4.0, hotel:3.5, transit:2.0,
    residential_lux:2.0, theatre:0.5, mall:0.2,
    hospital:1.5, office:0.2, karyk:1.5,
  },
};

// Причини защо дадена зона е добра за бакшиш
const BAKSHISH_REASONS = {
  airport:         "✈️ Foreigners with luggage — airport transfers",
  hotel:           "🏨 Business guests — corporate cards",
  residential_lux: "💎 Upscale districts — premium clients",
  hospital:        "🏥 Hospital clients — steady flow",
  theatre:         "🎭 After the show — emotional peak",
  nightlife:       "🍷 Restaurants and nightlife",
  office:          "💼 Office workers after hours",
  mall:            "🛍 Shoppers with bags",
  transit:         "🚌 Arrivals with luggage — need a taxi",
  university:      "🎓 High volume — compensates in numbers",
  karyk:           "🥉 Quiet district — no competition",
};

// Дъжд мултипликатор
function rainMultiplier() {
  if (weatherBoost >= 2.0) return 1.6; // дъжд
  if (weatherBoost >= 1.0) return 1.3; // ситен дъжд
  return 1.0;
}

function computeBakshishScore(zid, scores, shiftKey) {
  const z = ZONES.find(x=>x.id===zid); if(!z) return 0;
  const demand  = scores[zid] || 0;
  const weights = BAKSHISH_WEIGHTS[shiftKey] || {};
  const w = weights[z.type] || 0.5;
  const rain = rainMultiplier();
  // Score = demand × тип_тежест × дъжд_бонус
  return Math.min(5, demand * w * rain * 0.6);
}

function bakshishColor(bs) {
  if (bs >= 4.0) return '#ffd700'; // злато
  if (bs >= 3.0) return '#d4af37'; // тъмно злато
  if (bs >= 2.0) return '#c8a000'; // amber
  if (bs >= 1.0) return '#8a7000'; // тъмен amber
  return '#3a3000';
}

let bakshishOpen = false;

document.getElementById('bakshish-btn')?.addEventListener('click', () => {
  bakshishOpen = !bakshishOpen;
  document.getElementById('bakshish-btn').classList.toggle('active', bakshishOpen);
  const panel = document.getElementById('bakshish-panel');
  if (bakshishOpen) { buildBakshishPanel(); panel.style.display = 'block'; }
  else panel.style.display = 'none';
});

window.closeBakshish = function() {
  bakshishOpen = false;
  document.getElementById('bakshish-btn')?.classList.remove('active');
  document.getElementById('bakshish-panel').style.display = 'none';
};

function buildBakshishPanel() {
  const h = currentHour; // следва slider-а, не реалния часовник
  const shiftKey = getCurrentShift(h);
  const shift = SHIFTS[shiftKey];
  const {scores} = computeScores(currentHour);
  const rain = rainMultiplier();

  // Shift banner
  document.getElementById('bp-shift-label').textContent = shift.clientType;
  document.getElementById('bp-shift-name').textContent  = shift.name;
  let tip = shift.tip;
  if (rain > 1.0) tip = `🌧 RAIN BONUS ×${rain.toFixed(1)}! ` + tip;
  document.getElementById('bp-shift-tip').textContent = tip;

  // Rank all zones by bakshish score
  const ranked = ZONES
    .filter(z => z.type !== 'traffic')
    .map(z => ({
      z,
      bs: computeBakshishScore(z.id, scores, shiftKey),
      demand: scores[z.id] || 0,
    }))
    .filter(({bs}) => bs >= 0.5)
    .sort((a,b) => b.bs - a.bs)
    .slice(0, 15);

  const list = document.getElementById('bakshish-list');
  if (!ranked.length) {
    list.innerHTML = '<div style="padding:14px;color:#6a5000;font-family:Share Tech Mono,monospace">No active tip zones right now</div>';
    return;
  }

  list.innerHTML = ranked.map(({z, bs, demand}, i) => {
    const color = bakshishColor(bs);
    const reason = BAKSHISH_REASONS[z.type] || '🚖 Potential client';
    const rainTxt = rain > 1.0 ? ` 🌧×${rain.toFixed(1)}` : '';
    const stars = '⭐'.repeat(Math.min(5, Math.round(bs)));
    return `<div class="bp-item" onclick="(function(){closeBakshish();if(document.body.classList.contains('list-view'))toggleMapView();setTimeout(function(){map.invalidateSize();map.setView([${z.lat},${z.lng}],'${z.id}'==='airport'?14:15);'${z.id}'==='airport'?showAirportSchedule():showZonePopup('${z.id}');},200);})()">
      <div class="bp-rank">#${i+1}</div>
      <div class="bp-dot" style="background:${color};box-shadow:0 0 5px ${color}66"></div>
      <div class="bp-info">
        <div class="bp-name">${z.icon} ${z.name.split('(')[0].trim()}</div>
        <div class="bp-why">${reason}${rainTxt}</div>
        <div style="font-size:14px;color:#5a4000;margin-top:1px">${stars}</div>
      </div>
      <div class="bp-score-wrap">
        <div class="bp-score" style="color:${color}">${bs.toFixed(1)}</div>
        <div class="bp-multiplier">demand ${demand.toFixed(1)}</div>
      </div>
    </div>`;
  }).join('') + '<div style="padding:12px 12px 16px;text-align:center"><button onclick="closeBakshish()" style="background:#d4af37;color:#0d0e00;border:none;border-radius:8px;padding:10px 32px;font-weight:800;font-size:14px;cursor:pointer">✕ Close</button></div>';
}

// Rebuild bakshish panel when time changes (via setInterval, not render override)
setInterval(()=>{ if(bakshishOpen) buildBakshishPanel(); }, 60000);


const nowH=new Date().getHours()+new Date().getMinutes()/60;
currentHour=Math.min(24,Math.max(6,Math.round(nowH*2)/2));
slider.value=currentHour;
document.getElementById('time-display').textContent=fmtHour(currentHour);

applyFallbackAirport(); // зарежда веднага с fallback
buildCurve();
buildCircles();
buildTicker();
render(currentHour);
loadFlights(); loadBuses(); loadLiveArrivals(); setInterval(loadLiveArrivals, 10*60000);
loadConfig().then(()=>{ loadWeather(); setInterval(loadWeather,10*60000); });
checkEventAlerts();
geocodeZones();     // async — прецизира координатите от OSM

setTimeout(()=>{drawSparkline(currentHour); map.invalidateSize();},300);
window.addEventListener('resize',()=>{drawSparkline(currentHour); map.invalidateSize();});

}); // end DOMContentLoaded


function toggleMapView(){
  const listView = document.body.classList.toggle('list-view');
  const btn = document.getElementById('toggle-map-btn');
  if(btn) btn.textContent = listView ? '🗺️ Map' : '📋 List';
  if(!listView && window.map) setTimeout(()=>map.invalidateSize(), 100);
}

// ── i18n: EN default, Züridütsch (GSW) toggle ──
const GSW=[["ZÜRICH TAXI DEMAND","ZÜRI TAXI NOOCHFROOG"],["Live map · GPS navigation","Live Charte · GPS Navigation"],
["Zones by priority","Zone nach Priorität"],["NEXT 90 MINUTES","NÄCHSTI 90 MINUTE"],["TIP RADAR","TRINKGÄLD-RADAR"],
["Tip radar","Trinkgäld-Radar"],["Passenger exits — ZRH","Passagier-Usgäng — ZRH"],
["No live flight data — forecast mode","Kei Live-Flugdate — Prognose-Modus"],["Non-Schengen","Nöd-Schengen"],
["✈ FORECAST","✈ PROGNOSE"],["✈ OFFLINE","✈ OFFLINE"],["Morning shift","Morgeschicht"],["Midday shift","Mittagsschicht"],
["Afternoon shift","Nomittagsschicht"],["Evening shift","Aabigschicht"],["Night shift","Nachtschicht"],
["PEAK","SPITZE"],["High ▲","Höch ▲"],["Medium","Mittel"],["Low","Schwach"],["Good","Guet"],["Quiet district","Rueigs Quartier"],
["Quiet","Rueig"],["Avoid","Vermiide"],["▲ Excellent","▲ Uszeichnet"],["JAMMED NOW","STAU JETZT"],["CLEAR RIGHT NOW","FREI JETZT"],
["✕ Close","✕ Zue"],["🧭 Navigate","🧭 Navigiere"],["📋 List","📋 Liste"],["🗺️ Map","🗺️ Charte"],["📋 Scheduled","📋 Nach Fahrplan"],
["flights","Flüüg"],[" · in "," · i "],[" min"," Min"],["Last trains","Letschti Züüg"],["Bars closing","Beize gönd zue"],
["Clubs closing","Clubs gönd zue"],["Banks/offices — out","Banke/Büros — Fyraabig"],["Loading flights…","Flüüg am lade…"],
["No arrivals in the next 6 hours","Kei Aakünft i de nächschte 6 Stund"],["UPCOMING / NOW","CHUNNT / JETZT"],
["Baseline demand","Grundnoochfroog"],["Waiting for GPS…","Warte uf GPS…"],["Install ZUR Radar","ZUR Radar installiere"],
["Install ↓","Installiere ↓"],["Not now","Spöter"],["Works offline · Quick access","Funktioniert offline · Schnällzuegriff"],
["Top:","Top:"],["Next:","Nöchscht:"]].sort((a,b)=>b[0].length-a[0].length);
let uiLang=localStorage.getItem('zur_lang')||'en';
function gswWalk(n){
  if(n.nodeType===3){let t=n.nodeValue,c=false;
    for(const[k,v]of GSW){if(t.includes(k)){t=t.split(k).join(v);c=true;}}
    if(c)n.nodeValue=t;}
  else if(n.nodeType===1&&n.tagName!=='SCRIPT'&&n.tagName!=='STYLE'){for(const ch of n.childNodes)gswWalk(ch);}
}
if(uiLang==='gsw')setInterval(()=>gswWalk(document.body),1000);
(function(){
  const b=document.createElement('button');
  b.textContent=uiLang==='gsw'?'EN':'GSW';
  b.style.cssText='position:fixed;top:10px;right:10px;z-index:9999;font:700 11px monospace;padding:5px 9px;border:1px solid #888;border-radius:6px;background:#111;color:#f0b429;cursor:pointer';
  b.onclick=()=>{localStorage.setItem('zur_lang',uiLang==='gsw'?'en':'gsw');location.reload();};
  document.body.appendChild(b);
})();
