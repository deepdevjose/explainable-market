'use strict';
const $=s=>document.querySelector(s);
const t=window.emTranslate;
const csrf=$('meta[name="csrf-token"]').content;
let toastTimer;
function toast(text){const el=$('#toast');el.textContent=t(text);el.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.hidden=true,6000)}
async function api(path,method='GET',body){
  const r=await fetch(path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},...(body?{body:JSON.stringify(body)}:{})});
  let data;try{data=await r.json()}catch{throw Error(t('No se pudo leer la respuesta. Recarga la página.'))}
  if(!r.ok)throw Error(t((typeof data.error==='string'?data.error:data.error?.message)||'No se pudo completar la solicitud.'));return data;
}
let storedTheme;try{storedTheme=localStorage.getItem('em-theme')}catch{}
function setTheme(theme){document.documentElement.dataset.theme=theme;document.querySelectorAll('.theme-toggle').forEach(b=>b.setAttribute('aria-label',theme==='dark'?t('Usar tema claro'):t('Usar tema oscuro')))}
setTheme(storedTheme||'light');
window.emI18nReady.then(()=>setTheme(storedTheme||'light'));
document.querySelectorAll('.theme-toggle').forEach(b=>b.addEventListener('click',()=>{const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';setTheme(theme);try{localStorage.setItem('em-theme',theme)}catch{}}));
const menu=$('.mobile-menu');
const mobileQuery=window.matchMedia('(max-width:760px)');
function syncSidebar(){const sidebar=$('#sidebar');if(!sidebar)return;sidebar.inert=mobileQuery.matches&&!sidebar.classList.contains('open');if(menu)menu.setAttribute('aria-expanded',String(sidebar.classList.contains('open')))}
if(menu){syncSidebar();mobileQuery.addEventListener('change',syncSidebar);menu.addEventListener('click',()=>{$('#sidebar').classList.toggle('open');syncSidebar()});document.addEventListener('click',e=>{if(!e.target.closest('#sidebar,.mobile-menu')){$('#sidebar').classList.remove('open');syncSidebar()}})}
const filter=$('#symbol-filter');if(filter)filter.addEventListener('input',()=>{let count=0;document.querySelectorAll('[data-filter]').forEach(tr=>{const show=tr.dataset.filter.toLowerCase().includes(filter.value.toLowerCase());tr.hidden=!show;count+=show?1:0});$('#no-symbols').hidden=count>0});
const pass=$('#password-toggle');if(pass)pass.addEventListener('click',()=>{const field=$('#password');const show=field.type==='password';field.type=show?'text':'password';pass.textContent=show?t('Ocultar'):t('Ver');pass.setAttribute('aria-label',show?t('Ocultar contraseña'):t('Mostrar contraseña'))});
let polling=false;
async function pollSync(reload=true){
 if(polling)return;polling=true;
 let indicator=$('#sync-indicator');if(!indicator){indicator=document.createElement('div');indicator.id='sync-indicator';indicator.className='sync-indicator';indicator.setAttribute('role','status');indicator.textContent=t('Consultando fuentes externas…');document.body.append(indicator)}
 let attempts=0;
 const poll=async()=>{try{const data=await api('/api/status');if(!data.active.length){indicator.remove();polling=false;if(reload){if($('#chat-panel').hidden)location.reload();else toast(t('Los datos se actualizaron. Recarga cuando termines la conversación.'))}return}if(++attempts<50)setTimeout(poll,2000);else{indicator.textContent=t('La consulta está tardando. Vuelve a actualizar en unos minutos.');polling=false}}catch{indicator.remove();polling=false;toast(t('Se perdió la conexión al consultar el estado.'))}};setTimeout(poll,1800);
}
if($('#sync-indicator'))pollSync();
document.querySelectorAll('.refresh-button').forEach(b=>b.addEventListener('click',async()=>{b.disabled=true;try{const data=await api('/api/refresh','POST',{ticker:b.dataset.ticker});toast(data.message);if(data.active.length)pollSync();else b.disabled=false}catch(e){toast(e.message);b.disabled=false}}));
document.querySelectorAll('.analyze-button').forEach(b=>b.addEventListener('click',async()=>{const previous=b.textContent;b.disabled=true;b.textContent=t('Analizando con DeepSeek…');try{const data=await api('/api/analyze/'+encodeURIComponent(b.dataset.ticker),'POST',{});if(data.analyzed)location.reload();else toast(t('No hay titulares nuevos por analizar.'))}catch(e){toast(e.message)}finally{b.disabled=false;b.textContent=previous}}));
// All model and upstream content is rendered as text, never HTML.
let loadedChat=false,chatBusy=false,chatLoadPromise=null;
const panel=$('#chat-panel'),toggle=$('#chat-toggle'),input=$('#chat-input'),messages=$('#chat-messages');
function appendMessage(role,text,extra=''){const el=document.createElement('div');el.className='chat-message '+role+(extra?' '+extra:'');el.textContent=text;messages.append(el);messages.scrollTop=messages.scrollHeight;return el}
async function openChat(){
 panel.hidden=false;toggle.setAttribute('aria-expanded','true');toggle.setAttribute('aria-label',t('Cerrar asistente del mercado'));input.focus();
 if(!loadedChat){loadedChat=true;chatLoadPromise=(async()=>{try{const data=await api('/api/chat');if(data.messages.length){messages.replaceChildren();data.messages.forEach(m=>appendMessage(m.role,m.content))}}catch(e){toast(e.message);loadedChat=false}finally{chatLoadPromise=null}})()}
 if(chatLoadPromise)await chatLoadPromise;
}
function closeChat(){panel.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label',t('Abrir asistente del mercado'));toggle.focus()}
toggle.addEventListener('click',()=>panel.hidden?openChat():closeChat());$('#chat-close').addEventListener('click',closeChat);
document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(!panel.hidden)closeChat();if($('#sidebar')){$('#sidebar').classList.remove('open');syncSidebar()}}});
document.querySelectorAll('.open-chat').forEach(b=>b.addEventListener('click',openChat));
async function sendQuestion(question){
 if(chatBusy||!question.trim())return;chatBusy=true;await openChat();const send=$('.chat-send');send.disabled=true;input.disabled=true;$('#chat-reset').disabled=true;
 const welcome=$('.chat-welcome');if(welcome)welcome.remove();appendMessage('user',question);input.value='';const pending=appendMessage('assistant',t('Leyendo el contexto…'),'pending');
 try{const data=await api('/api/chat','POST',{message:question,page:document.body.dataset.page,ticker:document.body.dataset.ticker});pending.remove();const answer=appendMessage('assistant',data.answer);for(const source of data.sources||[]){const link=document.createElement('a');try{const url=new URL(source.url);if(url.protocol!=='https:')continue;link.href=url.href}catch{continue}link.target='_blank';link.rel='noopener noreferrer';link.textContent='['+source.id+'] '+source.source+' · '+source.ticker+' ↗';answer.append(link)}messages.scrollTop=messages.scrollHeight}catch(e){pending.remove();appendMessage('assistant',e.message,'error');input.value=question}finally{chatBusy=false;send.disabled=false;input.disabled=false;$('#chat-reset').disabled=false;input.focus()}
}
$('#chat-form').addEventListener('submit',e=>{e.preventDefault();sendQuestion(input.value.trim())});
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();sendQuestion(input.value.trim())}});
document.querySelectorAll('[data-question]').forEach(b=>b.addEventListener('click',()=>sendQuestion(b.dataset.question)));
$('#chat-reset').addEventListener('click',async()=>{if(chatBusy)return;try{await api('/api/chat','DELETE');messages.replaceChildren();appendMessage('assistant',t('Conversación borrada. ¿Qué te gustaría entender?'))}catch(e){toast(e.message)}});
// Read persisted observations only. Never synthesize a price or promote history to live.
function formatMarketPrice(raw){
 if(!/^-?\d+(\.\d+)?$/.test(raw))return raw;
 const [whole,fraction='']=raw.split('.');
 const spanish=document.documentElement.lang==='es';
 const grouped=whole.replace(/\B(?=(\d{3})+(?!\d))/g,spanish?'.':',');
 return grouped+(spanish?',':'.')+fraction.replace(/0+$/,'').padEnd(2,'0');
}
const marketNodes=[...document.querySelectorAll('[data-market-symbol]')].filter(n=>n.dataset.marketSymbol);
const marketStatuses={LIVE:'En vivo',DELAYED:'Con retraso',HISTORICAL:'Histórico',STALE:'Desactualizado',DEMO:'Demostración',UNAVAILABLE:'No disponible'};
async function pollMarkets(){
 if(document.hidden)return;
 await Promise.all(marketNodes.map(async node=>{
  try{
   const response=await fetch('/api/v1/market/'+encodeURIComponent(node.dataset.marketSymbol),{credentials:'same-origin',signal:AbortSignal.timeout(5000)});
   if(!response.ok)throw Error(t('No se pudo consultar el estado.'));
   const {data}=await response.json(),o=data.observation;
   const trace=node.querySelector('[data-live-trace]');
   if(trace&&data.status==='LIVE'&&o?.price&&o.event_time!==node.dataset.traceTime){
    node.dataset.traceTime=o.event_time;
    const samples=node.liveSamples||(node.liveSamples=[]);
    samples.push(Number(o.price));if(samples.length>60)samples.shift();
    if(samples.length>1){
     const low=Math.min(...samples),high=Math.max(...samples),range=high-low||1;
     trace.querySelector('polyline').setAttribute('points',samples.map((v,i)=>`${5+i*590/(samples.length-1)},${95-(v-low)*90/range}`).join(' '));
     node.querySelector('[data-live-wait]').hidden=true;
    }
   }
   const values={price:o?.price||'—',provider:o?.provider||t('Sin observaciones'),event_time:o?.event_time||t('Sin fecha disponible'),received_at:o?.received_at||t('Sin fecha disponible'),quality_flags:o?.quality_flags?.join(', ')||t('Sin incidencias registradas'),status:t(marketStatuses[data.status]||'No disponible')};
   for(const [field,value] of Object.entries(values)){const el=node.querySelector('[data-field="'+field+'"]');if(el){
     if(field==='price'){
      const old=el.dataset.rawPrice||el.textContent.trim();
      if(old!==value&&Number.isFinite(Number(old))&&Number.isFinite(Number(value))){
       el.classList.remove('price-rise','price-fall');void el.offsetWidth;
       el.classList.add(Number(value)>Number(old)?'price-rise':'price-fall');
       el.dataset.direction=Number(value)>Number(old)?'↑':'↓';
      }
      el.dataset.rawPrice=value;
     }
     el.textContent=field==='price'?formatMarketPrice(value):value;if(field==='price')el.title=value;if(field==='status')el.className='badge '+(data.status==='LIVE'?'positive':'neutral')}}
   const error=node.querySelector('[data-poll-error]');if(error)error.textContent='';
  }catch{
   const status=node.querySelector('[data-field="status"]');if(status){status.textContent=t('Estado sin verificar');status.className='badge neutral'}
   const error=node.querySelector('[data-poll-error]');if(error)error.textContent=t('Sin conexión al servidor. Se conserva la última observación visible con su fecha.');
  }
 }));
}
if(marketNodes.length){const tick=async()=>{await pollMarkets();setTimeout(tick,5000)};window.emI18nReady.then(tick);document.addEventListener('visibilitychange',()=>{if(!document.hidden)pollMarkets()})}
