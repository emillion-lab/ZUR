// Zürich Taxi Radar — превключвател ден/нощ
// Портирано и опростено от BAK: логиката на приложението не се променя,
// само облеклото. Автоматично избира по час, ако човекът не е избрал ръчно.
(function(){
  var KEY = 'zur_theme';                 // 'day' | 'night' | 'auto'

  function autoTheme(){
    var h = new Date().getHours();
    return (h >= 7 && h < 19) ? 'day' : 'night';
  }
  function resolve(){
    var saved = null;
    try{ saved = localStorage.getItem(KEY); }catch(e){}
    if(saved === 'day' || saved === 'night') return saved;
    return autoTheme();
  }
  function apply(t){
    document.body.classList.toggle('theme-night', t === 'night');
    document.body.classList.toggle('theme-day',   t === 'day');
    var b = document.getElementById('theme-btn');
    if(b){
      b.textContent = t === 'night' ? '◐' : '◑';
      b.title = t === 'night' ? 'Дневна тема' : 'Нощна тема';
    }
    var meta = document.querySelector('meta[name="theme-color"]');
    if(meta) meta.setAttribute('content', t === 'night' ? '#0a0e1a' : '#0284c7');
  }

  function mount(){
    var b = document.getElementById('theme-btn');
    if(!b) return;   // бутонът се очаква вече да е в index.html
    b.addEventListener('click', function(){
      var next = document.body.classList.contains('theme-night') ? 'day' : 'night';
      try{ localStorage.setItem(KEY, next); }catch(e){}
      apply(next);
    });
    apply(resolve());
    // ако е на автоматичен режим — сверява се на всеки половин час
    setInterval(function(){
      var saved = null;
      try{ saved = localStorage.getItem(KEY); }catch(e){}
      if(saved !== 'day' && saved !== 'night') apply(autoTheme());
    }, 30 * 60000);
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
