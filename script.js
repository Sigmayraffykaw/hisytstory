const reveals=[...document.querySelectorAll('.reveal')];
const revealObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('visible');revealObserver.unobserve(entry.target)}}),{threshold:.12});
reveals.forEach(el=>revealObserver.observe(el));

// Animated star field
const canvas=document.getElementById('starfield');
if(canvas){
  const c=canvas.getContext('2d');
  let stars=[];
  function resizeStars(){
    const dpr=Math.min(window.devicePixelRatio||1,2);
    canvas.width=innerWidth*dpr;canvas.height=innerHeight*dpr;
    canvas.style.width=innerWidth+'px';canvas.style.height=innerHeight+'px';
    c.setTransform(dpr,0,0,dpr,0,0);
    const count=Math.min(220,Math.floor(innerWidth*innerHeight/7500));
    stars=Array.from({length:count},()=>({x:Math.random()*innerWidth,y:Math.random()*innerHeight,r:Math.random()*1.3+.2,a:Math.random()*.7+.18,s:Math.random()*.018+.004,p:Math.random()*Math.PI*2}));
  }
  function drawStars(t){
    c.clearRect(0,0,innerWidth,innerHeight);
    for(const s of stars){const alpha=s.a*(.65+.35*Math.sin(t*s.s+s.p));c.beginPath();c.arc(s.x,s.y,s.r,0,Math.PI*2);c.fillStyle=`rgba(151,211,255,${alpha})`;c.fill()}
    requestAnimationFrame(drawStars);
  }
  resizeStars();window.addEventListener('resize',resizeStars);requestAnimationFrame(drawStars);
}

const glow=document.getElementById('cursorGlow');
let targetX=innerWidth/2,targetY=innerHeight/2,gx=targetX,gy=targetY;
window.addEventListener('pointermove',e=>{targetX=e.clientX;targetY=e.clientY});
function moveGlow(){gx+=(targetX-gx)*.09;gy+=(targetY-gy)*.09;if(glow){glow.style.left=gx+'px';glow.style.top=gy+'px'}requestAnimationFrame(moveGlow)}
moveGlow();

if(matchMedia('(pointer:fine)').matches){
  document.querySelectorAll('.tilt-card').forEach(card=>{
    card.addEventListener('mousemove',e=>{const r=card.getBoundingClientRect();const x=(e.clientX-r.left)/r.width-.5;const y=(e.clientY-r.top)/r.height-.5;card.style.transform=`rotateY(${x*5}deg) rotateX(${-y*5}deg) translateY(-4px)`});
    card.addEventListener('mouseleave',()=>card.style.transform='');
  });
  document.querySelectorAll('.magnetic').forEach(btn=>{
    btn.addEventListener('mousemove',e=>{const r=btn.getBoundingClientRect();btn.style.transform=`translate(${(e.clientX-r.left-r.width/2)*.08}px,${(e.clientY-r.top-r.height/2)*.1}px)`});
    btn.addEventListener('mouseleave',()=>btn.style.transform='');
  });

  // Original icy-blue comet cursor matching the falling-star background.
  const cursor=document.createElement('div');
  cursor.className='comet-cursor';
  document.body.appendChild(cursor);
  let cx=innerWidth/2,cy=innerHeight/2,tx=cx,ty=cy,lastSpark=0;
  const interactive='a,button,input,[role="button"],.tilt-card';

  window.addEventListener('pointermove',e=>{
    tx=e.clientX;ty=e.clientY;
    cursor.classList.toggle('hover',!!e.target.closest(interactive));
    const now=performance.now();
    if(now-lastSpark>34){
      lastSpark=now;
      const spark=document.createElement('i');
      spark.className='cursor-spark';
      spark.style.left=(e.clientX-5+Math.random()*10)+'px';
      spark.style.top=(e.clientY-5+Math.random()*10)+'px';
      spark.style.setProperty('--dx',(-12-Math.random()*22)+'px');
      spark.style.setProperty('--dy',(-5+Math.random()*10)+'px');
      document.body.appendChild(spark);
      setTimeout(()=>spark.remove(),600);
    }
  });
  window.addEventListener('pointerdown',e=>{
    const burst=document.createElement('i');burst.className='cursor-burst';burst.style.left=e.clientX+'px';burst.style.top=e.clientY+'px';document.body.appendChild(burst);setTimeout(()=>burst.remove(),500)
  });
  function moveCursor(){cx+=(tx-cx)*.38;cy+=(ty-cy)*.38;cursor.style.left=cx+'px';cursor.style.top=cy+'px';const angle=Math.atan2(ty-cy,tx-cx)*180/Math.PI;cursor.style.rotate=(angle||0)+'deg';requestAnimationFrame(moveCursor)}
  moveCursor();
}

const player=document.getElementById('musicPlayer');
const toggle=document.getElementById('musicToggle');
const status=document.getElementById('musicStatus');
const volume=document.getElementById('volume');
let audioCtx,master,musicPlaying=false,ambientTimer;
function makeOsc(freq,type,gainValue,detune=0){const osc=audioCtx.createOscillator();const gain=audioCtx.createGain();const filter=audioCtx.createBiquadFilter();osc.type=type;osc.frequency.value=freq;osc.detune.value=detune;filter.type='lowpass';filter.frequency.value=900;filter.Q.value=.6;gain.gain.value=gainValue;osc.connect(filter);filter.connect(gain);gain.connect(master);osc.start();return{osc,gain,filter}}
function softChime(freq,delay=0){const when=audioCtx.currentTime+delay;const osc=audioCtx.createOscillator();const g=audioCtx.createGain();const filter=audioCtx.createBiquadFilter();osc.type='sine';osc.frequency.setValueAtTime(freq,when);filter.type='lowpass';filter.frequency.value=1800;g.gain.setValueAtTime(0,when);g.gain.linearRampToValueAtTime(.026,when+.05);g.gain.exponentialRampToValueAtTime(.0001,when+3.8);osc.connect(filter);filter.connect(g);g.connect(master);osc.start(when);osc.stop(when+4)}
function buildAmbient(){audioCtx=new(window.AudioContext||window.webkitAudioContext)();master=audioCtx.createGain();master.gain.value=Number(volume.value)*.16;master.connect(audioCtx.destination);[[73.42,'sine',.022,-5],[110,'triangle',.014,4],[146.83,'sine',.012,-3],[164.81,'sine',.011,3],[220,'triangle',.006,0]].forEach(n=>makeOsc(...n));const lfo=audioCtx.createOscillator(),lfoGain=audioCtx.createGain();lfo.frequency.value=.055;lfoGain.gain.value=.008;lfo.connect(lfoGain);lfoGain.connect(master.gain);lfo.start();const sequence=[293.66,329.63,440,369.99,329.63,246.94];let step=0;ambientTimer=setInterval(()=>{if(musicPlaying){softChime(sequence[step%sequence.length]);if(step%3===0)softChime(sequence[(step+2)%sequence.length]/2,.6);step++}},4300)}
async function setPlaying(next){if(!audioCtx)buildAmbient();if(next){await audioCtx.resume();musicPlaying=true;const s=toggle?.querySelector('span');if(s)s.textContent='❚❚';if(status)status.textContent='Original ambient mix playing';player?.classList.add('playing')}else{await audioCtx.suspend();musicPlaying=false;const s=toggle?.querySelector('span');if(s)s.textContent='▶';if(status)status.textContent='Tap to play original ambience';player?.classList.remove('playing')}}
if(toggle)toggle.addEventListener('click',()=>setPlaying(!musicPlaying));
if(volume)volume.addEventListener('input',()=>{if(master)master.gain.value=Number(volume.value)*.16});

const city=document.querySelector('.city-stage');
const planet=document.querySelector('.planet');
window.addEventListener('scroll',()=>{const y=scrollY;if(city&&y<innerHeight*1.25)city.style.transform=`translateY(${y*.025}px)`;if(planet&&y<innerHeight*1.25)planet.style.transform=`translateY(${y*.045}px)`},{passive:true});
