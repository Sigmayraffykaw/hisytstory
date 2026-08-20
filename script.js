const reveals=document.querySelectorAll('.reveal');
const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting)entry.target.classList.add('visible')}),{threshold:.12});
reveals.forEach(el=>observer.observe(el));

const player=document.getElementById('musicPlayer');
const toggle=document.getElementById('musicToggle');
const status=document.getElementById('musicStatus');
const volume=document.getElementById('volume');
let ctx,master,nodes=[],playing=false;

function buildAmbient(){
  ctx=new (window.AudioContext||window.webkitAudioContext)();
  master=ctx.createGain();
  master.gain.value=Number(volume.value)*0.18;
  master.connect(ctx.destination);

  const notes=[110,164.81,220,261.63];
  notes.forEach((freq,i)=>{
    const osc=ctx.createOscillator();
    const gain=ctx.createGain();
    const filter=ctx.createBiquadFilter();
    osc.type=i%2?'sine':'triangle';
    osc.frequency.value=freq;
    gain.gain.value=.035/(i+1);
    filter.type='lowpass';
    filter.frequency.value=700+i*120;
    osc.connect(filter);filter.connect(gain);gain.connect(master);osc.start();
    nodes.push(osc);
  });

  const lfo=ctx.createOscillator();
  const lfoGain=ctx.createGain();
  lfo.frequency.value=.08;lfoGain.gain.value=.015;
  lfo.connect(lfoGain);lfoGain.connect(master.gain);lfo.start();nodes.push(lfo);
}

async function setPlaying(next){
  if(!ctx)buildAmbient();
  if(next){await ctx.resume();playing=true;toggle.textContent='❚❚';status.textContent='ambient playing';player.classList.add('playing')}
  else{await ctx.suspend();playing=false;toggle.textContent='▶';status.textContent='music off';player.classList.remove('playing')}
}

toggle.addEventListener('click',()=>setPlaying(!playing));
volume.addEventListener('input',()=>{if(master)master.gain.value=Number(volume.value)*0.18});

window.addEventListener('mousemove',e=>{
  const glow=document.querySelector('.sky-glow');
  if(glow){glow.style.transform=`translate(${(e.clientX/window.innerWidth-.5)*18}px,${(e.clientY/window.innerHeight-.5)*18}px)`}
});
