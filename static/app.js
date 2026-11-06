'use strict';
const $=s=>document.querySelector(s);
const csrf=$('meta[name="csrf-token"]').content;
let toastTimer;
function toast(text){const el=$('#toast');el.textContent=text;el.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.hidden=true,6000)}
async function api(path,method='GET',body){
  const r=await fetch(path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},...(body?{body:JSON.stringify(body)}:{})});
  let data;try{data=await r.json()}catch{throw Error('No se pudo leer la respuesta. Recarga la página.')}
  if(!r.ok)throw Error(data.error||'No se pudo completar la solicitud.');return data;
}
let storedTheme;try{storedTheme=localStorage.getItem('em-theme')}catch{}
function setTheme(theme){document.documentElement.dataset.theme=theme;document.querySelectorAll('.theme-toggle').forEach(b=>b.setAttribute('aria-label',theme==='dark'?'Usar tema claro':'Usar tema oscuro'))}
setTheme(storedTheme||'light');
document.querySelectorAll('.theme-toggle').forEach(b=>b.addEventListener('click',()=>{const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';setTheme(theme);try{localStorage.setItem('em-theme',theme)}catch{}}));
const menu=$('.mobile-menu');
const mobileQuery=window.matchMedia('(max-width:760px)');
function syncSidebar(){const sidebar=$('#sidebar');if(!sidebar)return;sidebar.inert=mobileQuery.matches&&!sidebar.classList.contains('open');if(menu)menu.setAttribute('aria-expanded',String(sidebar.classList.contains('open')))}
if(menu){syncSidebar();mobileQuery.addEventListener('change',syncSidebar);menu.addEventListener('click',()=>{$('#sidebar').classList.toggle('open');syncSidebar()});document.addEventListener('click',e=>{if(!e.target.closest('#sidebar,.mobile-menu')){$('#sidebar').classList.remove('open');syncSidebar()}})}
const filter=$('#symbol-filter');if(filter)filter.addEventListener('input',()=>{let count=0;document.querySelectorAll('[data-filter]').forEach(tr=>{const show=tr.dataset.filter.toLowerCase().includes(filter.value.toLowerCase());tr.hidden=!show;count+=show?1:0});$('#no-symbols').hidden=count>0});
const pass=$('#password-toggle');if(pass)pass.addEventListener('click',()=>{const field=$('#password');const show=field.type==='password';field.type=show?'text':'password';pass.textContent=show?'Ocultar':'Ver';pass.setAttribute('aria-label',show?'Ocultar contraseña':'Mostrar contraseña')});
let polling=false;
async function pollSync(reload=true){
 if(polling)return;polling=true;
 let indicator=$('#sync-indicator');if(!indicator){indicator=document.createElement('div');indicator.id='sync-indicator';indicator.className='sync-indicator';indicator.setAttribute('role','status');indicator.textContent='Consultando fuentes externas…';document.body.append(indicator)}
 let attempts=0;
 const poll=async()=>{try{const data=await api('/api/status');if(!data.active.length){indicator.remove();polling=false;if(reload){if($('#chat-panel').hidden)location.reload();else toast('Los datos se actualizaron. Recarga cuando termines la conversación.')}return}if(++attempts<50)setTimeout(poll,2000);else{indicator.textContent='La consulta está tardando. Vuelve a actualizar en unos minutos.';polling=false}}catch{indicator.remove();polling=false;toast('Se perdió la conexión al consultar el estado.')}};setTimeout(poll,1800);
}
if($('#sync-indicator'))pollSync();
document.querySelectorAll('.refresh-button').forEach(b=>b.addEventListener('click',async()=>{b.disabled=true;try{const data=await api('/api/refresh','POST',{ticker:b.dataset.ticker});toast(data.message);if(data.active.length)pollSync();else b.disabled=false}catch(e){toast(e.message);b.disabled=false}}));
document.querySelectorAll('.analyze-button').forEach(b=>b.addEventListener('click',async()=>{const previous=b.textContent;b.disabled=true;b.textContent='Analizando con DeepSeek…';try{const data=await api('/api/analyze/'+encodeURIComponent(b.dataset.ticker),'POST',{});if(data.analyzed)location.reload();else toast('No hay titulares nuevos por analizar.')}catch(e){toast(e.message)}finally{b.disabled=false;b.textContent=previous}}));
// All model and upstream content is rendered as text, never HTML.
let loadedChat=false,chatBusy=false,chatLoadPromise=null;
const panel=$('#chat-panel'),toggle=$('#chat-toggle'),input=$('#chat-input'),messages=$('#chat-messages');
function appendMessage(role,text,extra=''){const el=document.createElement('div');el.className='chat-message '+role+(extra?' '+extra:'');el.textContent=text;messages.append(el);messages.scrollTop=messages.scrollHeight;return el}
async function openChat(){
 panel.hidden=false;toggle.setAttribute('aria-expanded','true');toggle.setAttribute('aria-label','Cerrar asistente del mercado');input.focus();
 if(!loadedChat){loadedChat=true;chatLoadPromise=(async()=>{try{const data=await api('/api/chat');if(data.messages.length){messages.replaceChildren();data.messages.forEach(m=>appendMessage(m.role,m.content))}}catch(e){toast(e.message);loadedChat=false}finally{chatLoadPromise=null}})()}
 if(chatLoadPromise)await chatLoadPromise;
}
function closeChat(){panel.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','Abrir asistente del mercado');toggle.focus()}
toggle.addEventListener('click',()=>panel.hidden?openChat():closeChat());$('#chat-close').addEventListener('click',closeChat);
document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(!panel.hidden)closeChat();if($('#sidebar')){$('#sidebar').classList.remove('open');syncSidebar()}}});
document.querySelectorAll('.open-chat').forEach(b=>b.addEventListener('click',openChat));
async function sendQuestion(question){
 if(chatBusy||!question.trim())return;chatBusy=true;await openChat();const send=$('.chat-send');send.disabled=true;input.disabled=true;$('#chat-reset').disabled=true;
 const welcome=$('.chat-welcome');if(welcome)welcome.remove();appendMessage('user',question);input.value='';const pending=appendMessage('assistant','Leyendo el contexto…','pending');
 try{const data=await api('/api/chat','POST',{message:question,page:document.body.dataset.page,ticker:document.body.dataset.ticker});pending.remove();const answer=appendMessage('assistant',data.answer);for(const source of data.sources||[]){const link=document.createElement('a');try{const url=new URL(source.url);if(url.protocol!=='https:')continue;link.href=url.href}catch{continue}link.target='_blank';link.rel='noopener noreferrer';link.textContent='['+source.id+'] '+source.source+' · '+source.ticker+' ↗';answer.append(link)}messages.scrollTop=messages.scrollHeight}catch(e){pending.remove();appendMessage('assistant',e.message,'error');input.value=question}finally{chatBusy=false;send.disabled=false;input.disabled=false;$('#chat-reset').disabled=false;input.focus()}
}
$('#chat-form').addEventListener('submit',e=>{e.preventDefault();sendQuestion(input.value.trim())});
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();sendQuestion(input.value.trim())}});
document.querySelectorAll('[data-question]').forEach(b=>b.addEventListener('click',()=>sendQuestion(b.dataset.question)));
$('#chat-reset').addEventListener('click',async()=>{if(chatBusy)return;try{await api('/api/chat','DELETE');messages.replaceChildren();appendMessage('assistant','Conversación borrada. ¿Qué te gustaría entender?')}catch(e){toast(e.message)}});
