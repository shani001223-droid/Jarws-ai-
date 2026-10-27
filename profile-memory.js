'use strict';
(()=>{
const $=id=>document.getElementById(id),api=window.HoshiProfile;let packet=null;
const message=text=>$('status').textContent=text;
function render(aiIds=[]){
  $('entries').replaceChildren();
  packet.entries.forEach(entry=>{
    const article=document.createElement('article'),title=document.createElement('strong'),note=document.createElement('small'),p=document.createElement('p');
    title.textContent=entry.id+' · '+entry.category;note.textContent=' — '+entry.status+(entry.sensitive?' · PRIVATE / AI EXCLUDED':'');p.textContent=entry.text;
    article.append(title,note,p);
    if(!entry.sensitive){const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.dataset.entry=entry.id;check.checked=aiIds.includes(entry.id);label.append(check,document.createTextNode(' Include this entry in AI context (optional)'));article.append(label);}
    $('entries').append(article);
  });$('save').disabled=false;
}
$('file').onchange=async()=>{try{const file=$('file').files[0];if(!file)return;if(file.size>150000)throw new Error('File too large. Maximum 150 KB.');packet=api.validate(JSON.parse(await file.text()));$('share').checked=false;render();message(packet.entries.length+' entries ready to review. Not saved yet.');}catch(error){packet=null;$('save').disabled=true;$('entries').replaceChildren();message(error.message||'Could not read file.');}};
$('save').onclick=()=>{try{if(!packet)return;const aiIds=Array.from(document.querySelectorAll('input[data-entry]:checked')).map(el=>el.dataset.entry);localStorage.setItem(api.KEY,JSON.stringify({packet,shareWithAI:$('share').checked,aiIds}));$('export').disabled=false;message(packet.entries.length+' entries saved on this browser/device. Sensitive entries excluded from AI context.');}catch(_){message('Save failed. Browser storage may be blocked or full.');}};
$('delete').onclick=()=>{try{localStorage.removeItem(api.KEY);packet=null;$('entries').replaceChildren();$('save').disabled=true;$('export').disabled=true;$('share').checked=false;message('Saved profile deleted from this device.');}catch(_){message('Delete failed. Check browser storage settings.');}};
$('export').onclick=()=>{try{const saved=JSON.parse(localStorage.getItem(api.KEY)||'null');if(!saved)return;const blob=new Blob([JSON.stringify(api.validate(saved.packet),null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Hoshi_Private_Memory.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(_){message('Export failed.');}};
try{const saved=JSON.parse(localStorage.getItem(api.KEY)||'null');if(saved){packet=api.validate(saved.packet);$('share').checked=saved.shareWithAI===true;render(Array.isArray(saved.aiIds)?saved.aiIds:[]);$('export').disabled=false;message(packet.entries.length+' saved entries loaded from this device.');}}catch(_){message('Saved profile could not be read. You can import a fresh file.');}
})();
