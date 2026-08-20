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

// Featured city banner using the uploaded artwork.
const ticker=document.querySelector('.ticker');
if(ticker){
  const banner=document.createElement('section');
  banner.className='miamidian-banner';
  banner.innerHTML=`<div class="banner-shell"><div class="banner-copy"><span>FEATURED SIGNAL / 001</span><h2>WELCOME TO<br><em>MIAMIDIAN.</em></h2><p>Late-night energy. Blue lights. One very questionable smile.</p><a href="https://discord.gg/WPEwDUtGfC" target="_blank" rel="noreferrer">ENTER THE CITY ↗</a></div><div class="banner-art"><div class="banner-halo"></div><img src="e2ee8997-70c9-4e8d-96fa-a958f03dcc21.png" alt="Sir. Miamidian City banner mascot"></div></div>`;
  ticker.insertAdjacentElement('afterend',banner);

  const bannerStyle=document.createElement('style');
  bannerStyle.textContent=`
    .miamidian-banner{max-width:1240px;margin:0 auto;padding:72px 28px 20px;position:relative}
    .banner-shell{position:relative;min-height:380px;overflow:hidden;border:1px solid rgba(83,178,255,.42);border-radius:30px;background:linear-gradient(120deg,rgba(2,10,24,.95),rgba(6,40,78,.78));box-shadow:0 35px 100px rgba(0,0,0,.62),0 0 70px rgba(26,147,255,.18),inset 0 0 80px rgba(26,147,255,.08);display:grid;grid-template-columns:1.15fr .85fr;align-items:center}
    .banner-shell:before{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,255,255,.035),transparent 32%);pointer-events:none}
    .banner-copy{position:relative;z-index:3;padding:54px 58px}
    .banner-copy>span{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.18em;color:#73c8ff}
    .banner-copy h2{font-size:clamp(45px,6vw,78px);line-height:.86;letter-spacing:-.065em;margin:18px 0 22px}
    .banner-copy h2 em{font-style:normal;color:#8fd4ff;text-shadow:0 0 45px rgba(45,160,255,.55)}
    .banner-copy p{max-width:510px;color:#a9bfd3;line-height:1.7;margin:0 0 26px}
    .banner-copy a{display:inline-flex;text-decoration:none;font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;color:#eaf7ff;border:1px solid rgba(111,200,255,.5);background:rgba(18,108,190,.28);padding:13px 16px;border-radius:999px;box-shadow:0 0 28px rgba(34,155,255,.2);transition:.22s}
    .banner-copy a:hover{transform:translateY(-2px);background:rgba(27,130,221,.45);box-shadow:0 0 38px rgba(65,176,255,.34)}
    .banner-art{position:relative;height:100%;min-height:380px;display:grid;place-items:center;overflow:hidden}
    .banner-art:before{content:'';position:absolute;inset:0;background:radial-gradient(circle at 55% 50%,rgba(40,174,255,.35),transparent 58%)}
    .banner-halo{position:absolute;width:330px;height:330px;border:1px solid rgba(127,211,255,.35);border-radius:50%;box-shadow:0 0 80px rgba(26,157,255,.25),inset 0 0 50px rgba(79,183,255,.12);animation:bannerPulse 4.5s ease-in-out infinite}
    .banner-art img{position:relative;z-index:2;width:min(360px,78%);filter:drop-shadow(0 28px 38px rgba(0,0,0,.48)) drop-shadow(0 0 28px rgba(34,164,255,.28));animation:bannerFloat 4.2s ease-in-out infinite;user-select:none}
    @keyframes bannerFloat{50%{transform:translateY(-12px) rotate(-1.5deg)}}
    @keyframes bannerPulse{50%{transform:scale(1.05);opacity:.72}}
    @media(max-width:800px){.miamidian-banner{padding:45px 18px 0}.banner-shell{grid-template-columns:1fr}.banner-copy{padding:38px 28px 16px}.banner-art{min-height:300px}.banner-art img{width:min(290px,72%)}.banner-halo{width:260px;height:260px}}
    @media(prefers-reduced-motion:reduce){.banner-art img,.banner-halo{animation:none}}
  `;
  document.head.appendChild(bannerStyle);
}
