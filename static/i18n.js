'use strict';
window.emMessages={};
window.emTranslate=text=>window.emMessages[text]||text;
window.emI18nReady=fetch('/api/v1/translations',{credentials:'same-origin'}).then(r=>{if(!r.ok)throw Error('catalog');return r.json()}).then(data=>{window.emMessages=data}).catch(()=>{});
const languageSelect=document.querySelector('#language-select');
if(languageSelect)languageSelect.addEventListener('change',()=>{const url=new URL(location.href);url.searchParams.set('lang',languageSelect.value);location.assign(url)});
