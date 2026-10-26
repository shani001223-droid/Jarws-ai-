import {initCore} from './hoshi-core.mjs';
const core=document.getElementById('hoshiEnergy'), orb=document.getElementById('orb'), shell=document.getElementById('nightroom');
initCore(core,document.getElementById('core-canvas'));
function sync(){core.dataset.state=shell.classList.contains('speaking')?'speaking':/LISTENING|MICROPHONE/.test(document.getElementById('status').textContent)&&!/STOPPED|ERROR|FAILED|UNSUPPORTED|REQUIRED/.test(document.getElementById('status').textContent)?'listening':'idle';}
new MutationObserver(sync).observe(shell,{attributes:true,attributeFilter:['class']});
new MutationObserver(sync).observe(document.getElementById('status'),{childList:true,subtree:true,characterData:true});sync();
