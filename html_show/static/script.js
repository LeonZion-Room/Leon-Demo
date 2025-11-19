function toggle(el){
  el.classList.toggle('open');
  var next = el.nextElementSibling;
  if(next){
    if(next.style.display==='none' || next.style.display===''){
      next.style.display='block';
    }else{
      next.style.display='none';
    }
  }
}

function copyValue(id){
  var el = document.getElementById(id);
  if(!el) return;
  var text = el.value || el.textContent || '';
  if(!text) return;
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text);
  }else{
    var ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta); ta.select();
    try{ document.execCommand('copy'); }catch(e){}
    document.body.removeChild(ta);
  }
}

function setupSelection(){
  var files = document.querySelectorAll('.file');
  var details = document.getElementById('details');
  var rawInput = document.getElementById('raw-link');
  var rawOpen = document.getElementById('raw-open');
  var viewInput = document.getElementById('view-link');
  var viewOpen = document.getElementById('view-open');

  files.forEach(function(f){
    f.addEventListener('click', function(){
      var name = f.getAttribute('data-name');
      var rel = f.getAttribute('data-relpath');
      var raw = f.getAttribute('data-raw');
      var view = f.getAttribute('data-view');

      details.innerHTML = '<div><strong>' + name + '</strong></div>' +
        '<div style="color:#666;margin-top:4px">相对路径：' + rel + '</div>';

      rawInput.value = raw || '';
      rawOpen.href = raw || '#';

      if(view){
        viewInput.value = view;
        viewOpen.href = view;
        viewInput.parentElement.style.display = 'flex';
      }else{
        viewInput.value = '';
        viewOpen.removeAttribute('href');
        viewInput.parentElement.style.display = 'none';
      }

      files.forEach(function(x){ x.classList.remove('selected'); });
      f.classList.add('selected');
    });
  });
}

document.addEventListener('DOMContentLoaded', setupSelection);