const token = localStorage.getItem('token');
async function api(path, opts={}){
  const headers = opts.headers || {};
  if(token) headers['Authorization']='Token '+token;
  headers['Content-Type']='application/json';
  const res = await fetch(path, {...opts, headers});
  return res.json();
}
if(!token && location.pathname === '/'){ location.href = '/login/'; }
const chatEl = document.getElementById('chat');
const msgEl = document.getElementById('message');
const form = document.getElementById('inputForm');
const historyList = document.getElementById('historyList');
const logoutBtn = document.getElementById('logoutBtn');
async function loadHistory(){
  const data = await api('/api/history/');
  if(data.messages){
    historyList.innerHTML='';
    const msgs = data.messages.reverse();
    const convs = {};
    msgs.forEach(m=>{
      const key = new Date(m.created_at).toDateString();
      convs[key] = convs[key]||[]; convs[key].push(m);
    });
    for(const k of Object.keys(convs).reverse()){
      const d = document.createElement('div'); d.className='item'; d.textContent=k+' — '+convs[k].length+' messages'; d.onclick=()=>{ renderMessages(convs[k]); }; historyList.appendChild(d);
    }
  } else if(data.detail){ localStorage.removeItem('token'); location.href = '/login/'; }
}
function renderMessages(msgs){
  chatEl.innerHTML='';
  msgs.sort((a,b)=> new Date(a.created_at) - new Date(b.created_at));
  msgs.forEach(m=>{ const d = document.createElement('div'); d.className='msg '+(m.sender==='user'?'user':'bot'); d.textContent = m.text; chatEl.appendChild(d); });
  chatEl.scrollTop = chatEl.scrollHeight;
}
form.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const text = msgEl.value.trim(); if(!text) return;
  const userBubble = document.createElement('div'); userBubble.className='msg user'; userBubble.textContent = text; chatEl.appendChild(userBubble); chatEl.scrollTop = chatEl.scrollHeight;
  msgEl.value='';
  const res = await api('/api/chat/', {method:'POST', body: JSON.stringify({message:text})});
  const botText = res.reply || (res.error ? 'Error: '+res.error : 'No reply');
  const botBubble = document.createElement('div'); botBubble.className='msg bot'; botBubble.textContent = botText; chatEl.appendChild(botBubble); chatEl.scrollTop = chatEl.scrollHeight;
  await loadHistory();
});
(async ()=>{ await loadHistory(); })();
logoutBtn && (logoutBtn.onclick = ()=>{ localStorage.removeItem('token'); location.href='/login/'; });
