// Zürich Taxi Radar — анимиран пейзаж в лентата за времето
// Портирано от BAK (небе, звезди, луна, облаци, дъжд, сняг, птици,
// самолет, мъгла, светкавица). Без такси и без пътя за нея — по избор.
// Собствен, независим извор на данни (Open-Meteo, без ключ), координати Цюрих.
// Не пипа текста в лентата (°C/описание) — той си идва от съществуващия OWM код.
(function(){
  var cv, ctx, W = 0, H = 0, t = 0, raf = null;
  var state = { rain:0, snow:0, cloud:0.3, wind:0.2, night:false, rainAt:null };

  function mount(){
    var bar = document.getElementById('weather-bar');
    if(!bar){ setTimeout(mount, 500); return; }
    if(document.getElementById('wx-canvas')) return;
    bar.style.position = 'relative';
    cv = document.createElement('canvas');
    cv.id = 'wx-canvas';
    cv.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:0;opacity:.85';
    bar.insertBefore(cv, bar.firstChild);
    Array.prototype.forEach.call(bar.children, function(c){
      if(c !== cv){ c.style.position = 'relative'; c.style.zIndex = '1'; }
    });
    ctx = cv.getContext('2d');
    resize();
    window.addEventListener('resize', resize);
    pullWeather();
    setInterval(pullWeather, 15 * 60 * 1000);
    loop();
  }

  function resize(){
    if(!cv) return;
    var r = cv.getBoundingClientRect();
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = Math.max(200, r.width); H = Math.max(30, r.height);
    cv.width = W * dpr; cv.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function pullWeather(){
    var url = 'https://api.open-meteo.com/v1/forecast?latitude=47.3769&longitude=8.5417'
            + '&current=temperature_2m,precipitation,cloud_cover,wind_speed_10m,is_day,weather_code'
            + '&hourly=precipitation_probability,precipitation,snowfall&forecast_days=2&timezone=Europe%2FZurich';
    fetch(url).then(function(r){ return r.json(); }).then(function(d){
      var c = d.current || {};
      state.night = c.is_day === 0;
      state.cloud = Math.min(1, (c.cloud_cover || 0) / 100);
      state.wind  = Math.min(1, (c.wind_speed_10m || 0) / 40);
      state.rain  = (c.precipitation || 0) > 0 ? Math.min(1, c.precipitation / 3) : 0;
      var code = c.weather_code || 0;
      state.code  = code;
      // WMO кодове → какво реално рисуваме
      state.fog   = (code === 45 || code === 48) ? 1 : 0;
      state.snow  = ((code >= 71 && code <= 77) || (code >= 85 && code <= 86)) ? 0.8 : 0;
      state.storm = (code >= 95) ? 1 : 0;
      var drizzle = (code >= 51 && code <= 57);
      var rainy   = (code >= 61 && code <= 67) || (code >= 80 && code <= 82);
      if(state.snow > 0) state.rain = 0;
      else if(state.storm) state.rain = 1;
      else if(rainy)   state.rain = Math.max(state.rain, code >= 65 ? 1 : 0.6);
      else if(drizzle) state.rain = Math.max(state.rain, 0.3);
      // облачността от кода надделява, ако сензорът мълчи
      if(code === 0) state.cloud = Math.min(state.cloud, 0.05);
      else if(code === 1) state.cloud = Math.max(state.cloud, 0.25);
      else if(code === 2) state.cloud = Math.max(state.cloud, 0.55);
      else if(code === 3) state.cloud = Math.max(state.cloud, 0.9);

      // кога се очаква дъжд
      state.rainAt = null;
      state.rainHorizon = 12;                     // гледаме само смяната напред
      try{
        var times = d.hourly.time, prob = d.hourly.precipitation_probability, mm = d.hourly.precipitation;
        var now = Date.now(), limit = now + state.rainHorizon * 3600000;
        for(var i = 0; i < times.length; i++){
          var ts = new Date(times[i]).getTime();
          if(ts < now) continue;
          if(ts > limit) break;                   // отвъд 12ч не ни засяга
          if((prob[i] >= 50) || (mm[i] > 0.15)){
            var inH = Math.round((ts - now) / 3600000);
            state.rainAt = { time: times[i].slice(11,16), prob: prob[i], inH: inH };
            break;
          }
        }
      }catch(e){}
    }).catch(function(){});
  }

  // Фаза на луната спрямо референтно новолуние (6 ян 2000, 18:14 UTC).
  // Алгоритъмът на Conway грешеше с до 3 дни — тази сметка е точна до часове.
  var MOON_REF = Date.UTC(2000, 0, 6, 18, 14);
  var MOON_SYN = 29.530588853 * 86400000;      // синодичен месец
  function moonPhase(d){
    var x = (((d || new Date()).getTime() - MOON_REF) % MOON_SYN) / MOON_SYN;
    return x < 0 ? x + 1 : x;                  // 0 новолуние … .5 пълнолуние … 1
  }

  // ── частици ──
  var drops = [], flakes = [], stars = [], clouds = [];
  function seed(){
    drops = []; flakes = []; stars = []; clouds = [];
    for(var i=0;i<70;i++) drops.push({x:Math.random()*W, y:Math.random()*H, v:2+Math.random()*2.5});
    for(var j=0;j<40;j++) flakes.push({x:Math.random()*W, y:Math.random()*H, v:.3+Math.random()*.6, r:1+Math.random()*1.5, p:Math.random()*6});
    for(var k=0;k<40;k++) stars.push({x:Math.random()*W, y:Math.random()*H*.6, r:Math.random()*1.1, tw:Math.random()*6});
    for(var m=0;m<5;m++) clouds.push({x:Math.random()*W, y:3+Math.random()*(H*.4), s:.5+Math.random()*.8, v:.08+Math.random()*.12});
  }

  var plane = { x: -40, y: 8, active:false, next: 400 };

  function loop(){
    if(!ctx){ return; }
    if(!drops.length || drops[0].x > W) seed();
    t++;
    ctx.clearRect(0,0,W,H);

    // небе
    var g = ctx.createLinearGradient(0,0,0,H);
    if(state.night){ g.addColorStop(0,'rgba(8,16,34,.55)'); g.addColorStop(1,'rgba(14,26,48,.30)'); }
    else { g.addColorStop(0,'rgba(150,205,255,.30)'); g.addColorStop(1,'rgba(220,240,255,.12)'); }
    ctx.fillStyle = g; ctx.fillRect(0,0,W,H);

    // звезди нощем — колкото по-малко облаци, толкова по-ярки;
    // при разкъсана облачност надничат между тях
    if(state.night && state.cloud < 0.92){
      var starVis = 1 - state.cloud * 0.85;
      stars.forEach(function(s){
        var a = (.55 + .4*Math.sin((t + s.tw*30)/40)) * starVis;
        if(a <= 0.06) return;
        ctx.fillStyle = 'rgba(255,255,255,' + a.toFixed(2) + ')';
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 6.28); ctx.fill();
        if(s.r > .9 && a > .5){          // лек блясък на по-едрите
          ctx.strokeStyle = 'rgba(255,255,255,' + (a*.4).toFixed(2) + ')';
          ctx.lineWidth = .6;
          ctx.beginPath();
          ctx.moveTo(s.x - s.r*2.4, s.y); ctx.lineTo(s.x + s.r*2.4, s.y);
          ctx.moveTo(s.x, s.y - s.r*2.4); ctx.lineTo(s.x, s.y + s.r*2.4);
          ctx.stroke();
        }
      });
    }

    // луна с реална фаза (само нощем)
    var cx = W*.045, cy = H*.26, R = Math.min(8, H*.20);
    if(state.night){
      var ph = moonPhase();
      var illum  = (1 - Math.cos(2 * Math.PI * ph)) / 2;   // 0 нова … 1 пълна
      var waxing = ph < 0.5;
      var sgn    = waxing ? 1 : -1;                        // осветената страна
      var f      = 2 * illum - 1;                          // -1 сърп … +1 пълна

      // тъмният диск
      ctx.fillStyle = 'rgba(26,34,54,.6)';
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.28); ctx.fill();

      // Осветената част: външен ръб + терминатор.
      // Терминаторът е елипса с полуос f·R — точно, за всяка фаза.
      ctx.fillStyle = 'rgba(238,243,252,.96)';
      ctx.beginPath();
      var ma, mx, my, mfirst = true;
      for(ma = -Math.PI/2; ma <= Math.PI/2 + 0.01; ma += 0.12){
        mx = sgn * R * Math.cos(ma); my = R * Math.sin(ma);
        if(mfirst){ ctx.moveTo(cx + mx, cy + my); mfirst = false; }
        else ctx.lineTo(cx + mx, cy + my);
      }
      for(ma = Math.PI/2; ma >= -Math.PI/2 - 0.01; ma -= 0.12){
        mx = sgn * f * R * Math.cos(ma); my = R * Math.sin(ma);
        ctx.lineTo(cx + mx, cy + my);
      }
      ctx.closePath();
      ctx.fill();

      // мек ореол
      ctx.strokeStyle = 'rgba(226,232,240,.20)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(cx, cy, R + 2.5, 0, 6.28); ctx.stroke();
    }
    // Денем не рисуваме слънце: емоджито ☀️ в самата лента вече е там
    // и двете заедно изглеждат като две слънца.

    // хълмове
    ctx.fillStyle = state.night ? 'rgba(18,42,32,.55)' : 'rgba(74,140,90,.35)';
    ctx.beginPath(); ctx.moveTo(0,H);
    for(var x=0;x<=W;x+=8) ctx.lineTo(x, H - 6 - 5*Math.sin(x/60) - 3*Math.sin(x/23));
    ctx.lineTo(W,H); ctx.closePath(); ctx.fill();
    if(state.snow > 0){
      ctx.fillStyle = 'rgba(255,255,255,.5)';
      ctx.beginPath(); ctx.moveTo(0,H);
      for(var x2=0;x2<=W;x2+=8) ctx.lineTo(x2, H - 8 - 5*Math.sin(x2/60) - 3*Math.sin(x2/23));
      ctx.lineTo(W,H); ctx.closePath(); ctx.fill();
    }

    // облаци
    if(state.cloud > .12){
      clouds.forEach(function(c){
        c.x += c.v * (1 + state.wind*3);
        if(c.x > W + 40) c.x = -40;
        var a = .18 + state.cloud * .5;
        ctx.fillStyle = state.night ? 'rgba(148,163,184,' + (a*.7).toFixed(2) + ')'
                                    : 'rgba(255,255,255,' + a.toFixed(2) + ')';
        var s = c.s * Math.min(1, H/34);
        ctx.beginPath();
        ctx.arc(c.x, c.y, 6*s, 0, 6.28);
        ctx.arc(c.x + 7*s, c.y + 1*s, 8*s, 0, 6.28);
        ctx.arc(c.x + 15*s, c.y, 5.5*s, 0, 6.28);
        ctx.fill();
      });
    }

    // вятър
    if(state.wind > .35){
      ctx.strokeStyle = state.night ? 'rgba(203,213,225,.22)' : 'rgba(255,255,255,.45)';
      ctx.lineWidth = 1;
      for(var w=0;w<3;w++){
        var wy = H*.3 + w*6, off = (t*(1.5+state.wind*3) + w*70) % (W+90) - 45;
        ctx.beginPath(); ctx.moveTo(off, wy); ctx.lineTo(off+18, wy); ctx.stroke();
      }
    }

    // дъжд
    if(state.rain > 0){
      ctx.strokeStyle = 'rgba(120,190,255,.65)'; ctx.lineWidth = 1;
      drops.forEach(function(d){
        d.y += d.v * (1 + state.rain);
        d.x += state.wind * 1.6;
        if(d.y > H){ d.y = -4; d.x = Math.random()*W; }
        ctx.beginPath(); ctx.moveTo(d.x, d.y); ctx.lineTo(d.x - state.wind*2, d.y + 4); ctx.stroke();
      });
    }

    // сняг
    if(state.snow > 0){
      ctx.fillStyle = 'rgba(255,255,255,.85)';
      flakes.forEach(function(f){
        f.y += f.v; f.x += Math.sin((t + f.p*30)/40) * .5 + state.wind;
        if(f.y > H){ f.y = -3; f.x = Math.random()*W; }
        ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, 6.28); ctx.fill();
      });
    }

    // ── птици денем ──
    if(!state.night && state.rain === 0 && state.snow === 0){
      ctx.strokeStyle = state.cloud > .6 ? 'rgba(70,80,95,.5)' : 'rgba(50,60,75,.55)';
      ctx.lineWidth = 1.1;
      for(var bi = 0; bi < 3; bi++){
        var bx = ((t * 0.35) + bi * 130) % (W + 120) - 60;
        var byv = H * 0.22 + Math.sin((t + bi * 60) / 55) * 3 + bi * 5;
        var wing = 2.6 + Math.sin((t + bi * 40) / 9) * 1.8;   // махане с крила
        ctx.beginPath();
        ctx.moveTo(bx - 4, byv);
        ctx.quadraticCurveTo(bx - 2, byv - wing, bx, byv);
        ctx.quadraticCurveTo(bx + 2, byv - wing, bx + 4, byv);
        ctx.stroke();
      }
    }

    // ── самолет от време на време ──
    if(!plane.active && t > plane.next){ plane.active = true; plane.x = -30; plane.y = H*0.16 + Math.random()*H*0.1; }
    if(plane.active){
      plane.x += 0.55;
      ctx.save();
      ctx.globalAlpha = state.night ? .85 : .7;
      // следа
      var tg = ctx.createLinearGradient(plane.x - 34, 0, plane.x, 0);
      tg.addColorStop(0, 'rgba(255,255,255,0)');
      tg.addColorStop(1, state.night ? 'rgba(200,220,255,.5)' : 'rgba(255,255,255,.75)');
      ctx.strokeStyle = tg; ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.moveTo(plane.x - 34, plane.y); ctx.lineTo(plane.x, plane.y); ctx.stroke();
      // корпус
      ctx.fillStyle = state.night ? 'rgba(226,232,240,.95)' : 'rgba(70,84,105,.9)';
      ctx.beginPath();
      ctx.moveTo(plane.x + 5, plane.y);
      ctx.lineTo(plane.x - 3, plane.y - 1.6);
      ctx.lineTo(plane.x - 3, plane.y + 1.6);
      ctx.closePath(); ctx.fill();
      ctx.fillRect(plane.x - 1.5, plane.y - 3.2, 1.4, 6.4);   // крила
      // мигаща светлина нощем
      if(state.night && (t % 40) < 8){
        ctx.fillStyle = 'rgba(255,80,70,.95)';
        ctx.beginPath(); ctx.arc(plane.x - 3, plane.y, 1.1, 0, 6.28); ctx.fill();
      }
      ctx.restore();
      if(plane.x > W + 40){ plane.active = false; plane.next = t + 1400 + Math.random()*1600; }
    }

    // мъгла
    if(state.fog > 0){
      for(var fg=0; fg<3; fg++){
        var fy = H*0.45 + fg*7;
        var fo = (t*0.25 + fg*90) % (W+160) - 80;
        var fgrad = ctx.createLinearGradient(fo, 0, fo+160, 0);
        fgrad.addColorStop(0,'rgba(226,232,240,0)');
        fgrad.addColorStop(.5,'rgba(226,232,240,' + (state.night?.22:.42) + ')');
        fgrad.addColorStop(1,'rgba(226,232,240,0)');
        ctx.fillStyle = fgrad;
        ctx.fillRect(fo, fy, 160, 5);
      }
    }

    // светкавица при буря
    if(state.storm && Math.random() < 0.012){
      ctx.fillStyle = 'rgba(255,255,255,.55)';
      ctx.fillRect(0,0,W,H);
      var lx = W*0.35 + Math.random()*W*0.3;
      ctx.strokeStyle = 'rgba(255,255,210,.95)'; ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.moveTo(lx, 2);
      ctx.lineTo(lx-4, H*.45); ctx.lineTo(lx+3, H*.5); ctx.lineTo(lx-2, H-8);
      ctx.stroke();
    }

    // 30 кадъра стигат за този пейзаж и спестяват половината работа
    raf = requestAnimationFrame(function(){
      setTimeout(loop, 33);
    });
  }

  document.addEventListener('visibilitychange', function(){
    if(document.hidden){ if(raf) cancelAnimationFrame(raf); raf = null; }
    else if(!raf) loop();
  });

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
