const reveals=[...document.querySelectorAll('.reveal')];
const revealObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('visible');revealObserver.unobserve(entry.target)}}),{threshold:.12});
reveals.forEach(el=>revealObserver.observe(el));

const glow=document.getElementById('cursorGlow');
let targetX=innerWidth/2,targetY=innerHeight/2,gx=targetX,gy=targetY;
window.addEventListener('pointermove',e=>{targetX=e.clientX;targetY=e.clientY});
function moveGlow(){gx+=(targetX-gx)*.09;gy+=(targetY-gy)*.09;if(glow){glow.style.left=gx+'px';glow.style.top=gy+'px'}requestAnimationFrame(moveGlow)}
moveGlow();

if(matchMedia('(pointer:fine)').matches){
  document.querySelectorAll('.tilt-card').forEach(card=>{card.addEventListener('mousemove',e=>{const r=card.getBoundingClientRect();const x=(e.clientX-r.left)/r.width-.5;const y=(e.clientY-r.top)/r.height-.5;card.style.transform=`rotateY(${x*5}deg) rotateX(${-y*5}deg) translateY(-4px)`});card.addEventListener('mouseleave',()=>card.style.transform='')});
  document.querySelectorAll('.magnetic').forEach(btn=>{btn.addEventListener('mousemove',e=>{const r=btn.getBoundingClientRect();btn.style.transform=`translate(${(e.clientX-r.left-r.width/2)*.08}px,${(e.clientY-r.top-r.height/2)*.1}px)`});btn.addEventListener('mouseleave',()=>btn.style.transform='')});
  const cursor=document.createElement('div');cursor.className='comet-cursor';document.body.appendChild(cursor);let cx=innerWidth/2,cy=innerHeight/2,tx=cx,ty=cy,lastSpark=0;const interactive='a,button,input,[role="button"],.tilt-card';window.addEventListener('pointermove',e=>{tx=e.clientX;ty=e.clientY;cursor.classList.toggle('hover',!!e.target.closest(interactive));const now=performance.now();if(now-lastSpark>34){lastSpark=now;const spark=document.createElement('i');spark.className='cursor-spark';spark.style.left=(e.clientX-5+Math.random()*10)+'px';spark.style.top=(e.clientY-5+Math.random()*10)+'px';spark.style.setProperty('--dx',(-12-Math.random()*22)+'px');spark.style.setProperty('--dy',(-5+Math.random()*10)+'px');document.body.appendChild(spark);setTimeout(()=>spark.remove(),600)}});window.addEventListener('pointerdown',e=>{const burst=document.createElement('i');burst.className='cursor-burst';burst.style.left=e.clientX+'px';burst.style.top=e.clientY+'px';document.body.appendChild(burst);setTimeout(()=>burst.remove(),500)});function moveCursor(){cx+=(tx-cx)*.38;cy+=(ty-cy)*.38;cursor.style.left=cx+'px';cursor.style.top=cy+'px';requestAnimationFrame(moveCursor)}moveCursor();
}

const player=document.getElementById('musicPlayer'),toggle=document.getElementById('musicToggle'),heroMusic=document.getElementById('heroMusic'),status=document.getElementById('musicStatus'),volume=document.getElementById('volume');let audioCtx,master,musicPlaying=false,ambientTimer;
function makeOsc(freq,type,gainValue,detune=0){const osc=audioCtx.createOscillator(),gain=audioCtx.createGain(),filter=audioCtx.createBiquadFilter();osc.type=type;osc.frequency.value=freq;osc.detune.value=detune;filter.type='lowpass';filter.frequency.value=900;gain.gain.value=gainValue;osc.connect(filter);filter.connect(gain);gain.connect(master);osc.start()}
function softChime(freq,delay=0){const when=audioCtx.currentTime+delay,osc=audioCtx.createOscillator(),g=audioCtx.createGain();osc.type='sine';osc.frequency.setValueAtTime(freq,when);g.gain.setValueAtTime(.0001,when);g.gain.linearRampToValueAtTime(.026,when+.05);g.gain.exponentialRampToValueAtTime(.0001,when+3.8);osc.connect(g);g.connect(master);osc.start(when);osc.stop(when+4)}
function buildAmbient(){audioCtx=new(window.AudioContext||window.webkitAudioContext)();master=audioCtx.createGain();master.gain.value=Number(volume.value)*.16;master.connect(audioCtx.destination);[[73.42,'sine',.022,-5],[110,'triangle',.014,4],[146.83,'sine',.012,-3],[164.81,'sine',.011,3],[220,'triangle',.006,0]].forEach(n=>makeOsc(...n));const sequence=[293.66,329.63,440,369.99,329.63,246.94];let step=0;ambientTimer=setInterval(()=>{if(musicPlaying){softChime(sequence[step%sequence.length]);step++}},4300)}
async function setPlaying(next){if(!audioCtx)buildAmbient();if(next){await audioCtx.resume();musicPlaying=true;if(toggle?.querySelector('span'))toggle.querySelector('span').textContent='❚❚';if(heroMusic)heroMusic.textContent='❚❚';if(status)status.textContent='Original ambient mix playing';player?.classList.add('playing')}else{await audioCtx.suspend();musicPlaying=false;if(toggle?.querySelector('span'))toggle.querySelector('span').textContent='▶';if(heroMusic)heroMusic.textContent='♫';if(status)status.textContent='Tap to play ambience';player?.classList.remove('playing')}}
if(toggle)toggle.addEventListener('click',()=>setPlaying(!musicPlaying));if(heroMusic)heroMusic.addEventListener('click',()=>setPlaying(!musicPlaying));if(volume)volume.addEventListener('input',()=>{if(master)master.gain.value=Number(volume.value)*.16});

const menuToggle=document.getElementById('menuToggle'),navLinks=document.getElementById('navLinks');if(menuToggle&&navLinks)menuToggle.addEventListener('click',()=>navLinks.classList.toggle('open'));
const navAnchors=[...document.querySelectorAll('.nav-links a[href^="#"]')],tracked=navAnchors.map(a=>({a,el:document.querySelector(a.getAttribute('href'))})).filter(x=>x.el);function updateActiveNav(){const marker=scrollY+110;let current=tracked[0];for(const item of tracked){if(item.el.offsetTop<=marker)current=item}navAnchors.forEach(a=>a.classList.remove('active'));if(current)current.a.classList.add('active')}window.addEventListener('scroll',updateActiveNav,{passive:true});updateActiveNav();navAnchors.forEach(a=>a.addEventListener('click',()=>{navAnchors.forEach(x=>x.classList.remove('active'));a.classList.add('active');navLinks?.classList.remove('open')}));

// MIAMIDIAN SUPPORT BOT 2.0 — smarter local assistant with context, quick prompts and typing feedback.
const aiChat=document.getElementById('aiChat'),aiMessages=document.getElementById('aiMessages'),aiForm=document.getElementById('aiForm'),aiInput=document.getElementById('aiInput');
const openers=[document.getElementById('supportOpen'),document.getElementById('supportCardOpen')].filter(Boolean),closeAI=document.getElementById('supportClose');
let lastTopic='general',messageCount=0;

function openAI(){aiChat?.classList.add('open');aiChat?.setAttribute('aria-hidden','false');setTimeout(()=>aiInput?.focus(),120)}
function closeAIFn(){aiChat?.classList.remove('open');aiChat?.setAttribute('aria-hidden','true')}
openers.forEach(b=>b.addEventListener('click',openAI));closeAI?.addEventListener('click',closeAIFn);

function addMsg(text,type,html=false){const d=document.createElement('div');d.className=`ai-msg ${type}`;if(html)d.innerHTML=text;else d.textContent=text;aiMessages.appendChild(d);aiMessages.scrollTop=aiMessages.scrollHeight;return d}
function addTyping(){const d=addMsg('Miamidian is typing…','bot');d.classList.add('typing');return d}
function clean(s){return s.toLowerCase().replace(/[^a-z0-9\s]/g,' ').replace(/\s+/g,' ').trim()}
function has(s,words){return words.some(w=>s.includes(w))}

const answers={
  join:'You can join the city here: discord.gg/WPEwDUtGfC. After joining, grab your roles and say hey in chat.',
  rules:'The server is strictly SFW and friendly. Keep content clean, respect everyone, avoid spam and drama, and follow staff directions.',
  roles:'Roles are handled inside Discord. Join the server, then check the role channels to choose what fits you.',
  vc:'Yep — we have gaming and voice chats. Join the Discord and check the active VCs or start one with friends.',
  games:'Scroll to the Steam Games section at the bottom. You can browse the game cards and open each one on Steam.',
  staff:'For reports, moderation issues, bans, or something that needs a real person, contact the staff team inside Discord.',
  music:'Use the music button on the page to toggle Midnight in Miamidian. The volume slider controls it.',
  site:'This is the official Miamidian City site. You can explore the community, games, support bot, music, and Discord invite here.',
  sfw:'Yes — Sir. Miamidian’s City is strictly SFW. NSFW content is not allowed.',
  hello:'Hey 👋 Welcome to Miamidian. I can help with joining, rules, roles, games, VCs, music, and staff support.'
};

function detectTopic(q){const s=clean(q);
  if(has(s,['join','invite','discord link','server link','how do i get in']))return'join';
  if(has(s,['rule','rules','allowed','not allowed','ban rule','guideline']))return'rules';
  if(has(s,['nsfw','sfw','safe']))return'sfw';
  if(has(s,['role','roles','rank']))return'roles';
  if(has(s,['vc','voice','call','voice chat']))return'vc';
  if(has(s,['game','games','steam','counter strike','cs2','dota','brawlhalla','apex','rust','unturned','garry']))return'games';
  if(has(s,['staff','mod','admin','report','ban','appeal','help me','moderator']))return'staff';
  if(has(s,['music','song','audio','volume','midnight']))return'music';
  if(has(s,['website','site','page','what is this']))return'site';
  if(has(s,['hello','hey','hi ','hi','yo','sup']))return'hello';
  return null;
}

function replyFor(q){const s=clean(q),topic=detectTopic(q);if(topic){lastTopic=topic;return answers[topic]}
  if(has(s,['where','how','what'])&&lastTopic!=='general')return `About ${lastTopic}: ${answers[lastTopic]}`;
  if(has(s,['thanks','thank you','ty']))return 'Anytime 💙';
  if(has(s,['who are you','your name']))return 'I’m Miamidian AI — the site support assistant for Sir. Miamidian’s City.';
  if(has(s,['who made','owner','owns']))return 'This site is for Sir. Miamidian’s City. For owner or staff details, check the Discord team information.';
  if(has(s,['free','cost','price']))return 'Joining the Discord is free. Steam game prices depend on Steam and can change.';
  if(has(s,['best game','recommend','recommendation']))return 'For fast multiplayer, try Counter-Strike 2 or Apex Legends. For sandbox chaos, Garry’s Mod or Rust is a better fit.';
  return 'I’m not fully sure what you mean yet. Try asking about **joining**, **rules**, **roles**, **games**, **VCs**, **music**, or **staff support**.';
}

function askBot(q){messageCount++;addMsg(q,'user');aiInput.value='';const typing=addTyping();const delay=Math.min(850,300+q.length*8);setTimeout(()=>{typing.remove();addMsg(replyFor(q),'bot')},delay)}
aiForm?.addEventListener('submit',e=>{e.preventDefault();const q=aiInput.value.trim();if(q)askBot(q)});

// Quick question buttons
if(aiForm&&aiMessages&&!document.getElementById('aiQuick')){
  const quick=document.createElement('div');quick.id='aiQuick';quick.className='ai-quick';
  ['How do I join?','What are the rules?','What games are here?','I need staff help'].forEach(label=>{const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',()=>askBot(label));quick.appendChild(b)});
  aiForm.parentNode.insertBefore(quick,aiForm);
  const css=document.createElement('style');css.textContent=`.ai-quick{display:flex;gap:7px;flex-wrap:wrap;padding:0 12px 10px}.ai-quick button{border:1px solid rgba(100,190,255,.28);background:rgba(17,82,145,.22);color:#bfe2ff;padding:8px 10px;border-radius:999px;font-size:10px;font-weight:800}.ai-quick button:hover{background:rgba(25,117,204,.38);color:#fff}.ai-msg.typing{opacity:.65;font-style:italic}.ai-msg bot strong{color:#fff}`;document.head.appendChild(css);
}

// Steam library filters
const steamFilterButtons=[...document.querySelectorAll('.steam-filters button')];
const steamCards=[...document.querySelectorAll('.steam-card')];
steamFilterButtons.forEach(btn=>btn.addEventListener('click',()=>{const filter=btn.textContent.trim().toLowerCase();steamFilterButtons.forEach(b=>b.classList.remove('active'));btn.classList.add('active');steamCards.forEach(card=>{const searchable=(card.querySelector('.steam-card-body')?.textContent||'').toLowerCase();card.style.display=filter==='all'||searchable.includes(filter)?'':'none'})}));
