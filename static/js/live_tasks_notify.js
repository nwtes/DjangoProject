function makeToast(id,title,group,url){
    const existing = document.getElementById('live-task-toast-'+id);
    if(existing) return;
    const container = document.createElement('div');
    container.id = 'live-task-toast-'+id;
    container.className = 'help-toast';
    container.style.display = 'block';
    const inner = document.createElement('div');
    inner.className = 'help-toast-content';
    const titleEl = document.createElement('div');
    titleEl.innerHTML = '<strong>'+title+'</strong>';
    const meta = document.createElement('div');
    meta.style.color='var(--muted)';
    meta.style.marginTop='6px';
    meta.textContent = 'Group: '+group;
    const actions = document.createElement('div');
    actions.style.marginTop='8px';
    actions.style.textAlign='right';
    const link = document.createElement('a');
    link.className='btn btn-accent';
    link.href = url;
    link.textContent = 'Open';
    const close = document.createElement('button');
    close.className='btn btn-ghost';
    close.textContent = 'Dismiss';
    close.addEventListener('click', ()=>{ container.classList.remove('show'); setTimeout(()=>container.remove(),260); });
    actions.appendChild(link);
    actions.appendChild(close);
    inner.appendChild(titleEl);
    inner.appendChild(meta);
    inner.appendChild(actions);
    container.appendChild(inner);
    document.body.appendChild(container);
    requestAnimationFrame(()=>container.classList.add('show'));
}

function fetchLiveTasks(){
    fetch('/tasks/live/available/').then(r=>r.json()).then(data=>{
        if(!data.tasks || !data.tasks.length) return;
        data.tasks.forEach(t=>{
            makeToast(t.id,t.title,t.group,'/tasks/task/'+t.id);
        })
    }).catch(()=>{});
}

if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',()=>{ fetchLiveTasks(); setInterval(fetchLiveTasks,60000); });
}else{ fetchLiveTasks(); setInterval(fetchLiveTasks,60000); }

