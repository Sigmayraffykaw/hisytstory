const reveals=[...document.querySelectorAll('.reveal')];
const revealObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('visible');revealObserver.unobserve(entry.target)}}),{threshold:.12});
reveals.forEach(el=>revealObserver.observe(el));

const glow=document.getElementById('cursorGlow');
let targetX=innerWidth/2,targetY=innerHeight/2,gx=targetX,gy=targetY;
window.addEventListener('pointermove',e=>{targetX=e.clientX;targetY=e.clientY});
function moveGlow(){gx+=(targetX-gx)*.09;gy+=(targetY-gy)*.09;if(glow){glow.style.left=gx+'px';glow.style.top=gy+'px'}requestAnimationFrame(moveGlow)}moveGlow();

if(matchMedia('(pointer:fine)').matches){
  document.querySelectorAll('.tilt-card').forEach(card=>{card.addEventListener('mousemove',e=>{const r=card.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;card.style.transform=`rotateY(${x*5}deg) rotateX(${-y*5}deg) translateY(-4px)`});card.addEventListener('mouseleave',()=>card.style.transform='')});
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

// MIAMIDIAN AI 3.0 — richer local support assistant with memory, actions and recommendation logic.
const aiChat=document.getElementById('aiChat'),aiMessages=document.getElementById('aiMessages'),aiForm=document.getElementById('aiForm'),aiInput=document.getElementById('aiInput');
const openers=[document.getElementById('supportOpen'),document.getElementById('supportCardOpen')].filter(Boolean),closeAI=document.getElementById('supportClose');
const botState={lastTopic:'general',lastGame:null,messageCount:0,name:null};

function openAI(){aiChat?.classList.add('open');aiChat?.setAttribute('aria-hidden','false');setTimeout(()=>aiInput?.focus(),120)}
function closeAIFn(){aiChat?.classList.remove('open');aiChat?.setAttribute('aria-hidden','true')}
openers.forEach(b=>b.addEventListener('click',openAI));closeAI?.addEventListener('click',closeAIFn);

function addMsg(text,type,opts={}){const d=document.createElement('div');d.className=`ai-msg ${type}`;if(opts.html)d.innerHTML=text;else d.textContent=text;if(opts.actions){const row=document.createElement('div');row.className='ai-actions';opts.actions.forEach(a=>{const el=document.createElement(a.href?'a':'button');if(a.href){el.href=a.href;el.target=a.target||'_self';el.rel='noreferrer'}else{el.type='button';el.addEventListener('click',a.onClick)}el.textContent=a.label;row.appendChild(el)});d.appendChild(row)}aiMessages.appendChild(d);aiMessages.scrollTop=aiMessages.scrollHeight;return d}
function addTyping(){const d=addMsg('Miamidian is thinking…','bot');d.classList.add('typing');return d}
function clean(s){return s.toLowerCase().replace(/[^a-z0-9\s']/g,' ').replace(/\s+/g,' ').trim()}
function words(s){return new Set(clean(s).split(' ').filter(Boolean))}
function score(q,terms){const s=clean(q),ws=words(q);let n=0;for(const t of terms){if(t.includes(' ')){if(s.includes(t))n+=3}else if(ws.has(t))n+=2;else if(s.includes(t))n+=1}return n}
function scrollToId(id){document.getElementById(id)?.scrollIntoView({behavior:'smooth',block:'start'});closeAIFn()}

const intents={
  join:['join','invite','discord','server link','get in','enter server'],rules:['rule','rules','guideline','allowed','not allowed','punishment'],sfw:['sfw','nsfw','safe','clean'],roles:['role','roles','rank','ping role'],vc:['vc','voice','voice chat','call','mic'],games:['game','games','steam','library','play'],staff:['staff','mod','moderator','admin','report','appeal','ban','help'],music:['music','song','audio','volume','soundtrack'],site:['website','site','page','what is this','features'],team:['team','who runs','who made','owner'],apply:['apply','application','staff application','become mod'],reviews:['review','reviews','feedback'],hello:['hello','hey','hi','yo','sup']
};
function detectTopic(q){let best=['general',0];for(const [topic,terms] of Object.entries(intents)){const s=score(q,terms);if(s>best[1])best=[topic,s]}return best[1]>=2?best[0]:null}

const gameData=[
  {name:'Counter-Strike 2',keys:['cs2','counter strike','fps','competitive','ranked','tactical'],why:'best for competitive tactical FPS and ranked team play'},
  {name:'Apex Legends',keys:['apex','battle royale','movement','squad','fast'],why:'best for fast movement, squads, and battle royale'},
  {name:'Rust',keys:['rust','survival','base','craft','raid'],why:'best for survival, base building, and long sessions'},
  {name:"Garry's Mod",keys:['garry','gmod','sandbox','creative','funny','custom'],why:'best for sandbox chaos, custom modes, and messing around'},
  {name:'Unturned',keys:['unturned','free','survival','zombie'],why:'a good free survival pick'},
  {name:'Brawlhalla',keys:['brawlhalla','fighting','fighter','platform'],why:'best for quick platform-fighting matches'},
  {name:'Dota 2',keys:['dota','moba','strategy','hero'],why:'best for deep team strategy'},
  {name:'Team Fortress 2',keys:['tf2','team fortress','class','casual fps'],why:'best for class-based casual FPS fun'}
];
function recommendGame(q){const s=clean(q);let ranked=gameData.map(g=>({g,score:g.keys.reduce((n,k)=>n+(s.includes(k)?2:0),0)})).sort((a,b)=>b.score-a.score);const pick=ranked[0].score?ranked[0].g:gameData[Math.floor(Math.random()*gameData.length)];botState.lastGame=pick.name;return pick}

function answerFor(q){const s=clean(q),topic=detectTopic(q);if(topic)botState.lastTopic=topic;
  const actions={discord:[{label:'Join Discord ↗',href:'https://discord.gg/WPEwDUtGfC',target:'_blank'}],games:[{label:'Open Games',onClick:()=>scrollToId('games')}],team:[{label:'View Team',onClick:()=>scrollToId('team')}],apply:[{label:'Go to Apply',onClick:()=>scrollToId('apply')}],reviews:[{label:'See Reviews',onClick:()=>scrollToId('reviews')}]} ;
  if(/my name is [a-z0-9_ -]{2,20}/i.test(q)){botState.name=q.match(/my name is ([a-z0-9_ -]{2,20})/i)[1].trim();return{text:`Got it — I’ll remember you as ${botState.name} while this page stays open.`}}
  if(/what('?s| is) my name/i.test(q))return{text:botState.name?`You told me your name is ${botState.name}.`:'You haven’t told me your name yet.'};
  if(/recommend|what should i play|best game|pick a game/.test(s)){const g=recommendGame(q);return{text:`I’d pick ${g.name} — ${g.why}.`,actions:actions.games}}
  if(/another one|another game|different game/.test(s)){let pool=gameData.filter(g=>g.name!==botState.lastGame);const g=pool[Math.floor(Math.random()*pool.length)];botState.lastGame=g.name;return{text:`Try ${g.name} next — ${g.why}.`,actions:actions.games}}
  if(/where am i|what section/.test(s)){let nearest=tracked[0];for(const item of tracked){if(item.el.offsetTop<=scrollY+180)nearest=item}return{text:`You’re around the ${nearest?.a?.textContent||'Main'} section right now.`}}
  if(/thanks|thank you|ty|cheers/.test(s))return{text:`Anytime${botState.name?`, ${botState.name}`:''} 💙`};
  if(/who are you|your name/.test(s))return{text:'I’m Miamidian AI, the on-site assistant for Sir. Miamidian’s City. I can help you navigate the site and answer common server questions.'};
  if(topic==='join')return{text:'Use the invite below to join Sir. Miamidian’s City. Once you’re in, grab your roles and jump into chat.',actions:actions.discord};
  if(topic==='rules')return{text:'Main idea: keep it friendly, clean, respectful, and drama-free. The server is strictly SFW, and staff can step in when needed.'};
  if(topic==='sfw')return{text:'Yes — the server is strictly SFW. NSFW content is not allowed.'};
  if(topic==='roles')return{text:'Roles are handled inside Discord. Join first, then use the server’s role channels to pick the ones you want.',actions:actions.discord};
  if(topic==='vc')return{text:'Yep. The server has gaming and voice chats. Join Discord and check for active VCs or start one with friends.',actions:actions.discord};
  if(topic==='games')return{text:'The Games section has the current Steam library. You can browse titles, filter them, and open each game on Steam.',actions:actions.games};
  if(topic==='staff')return{text:'For reports, moderation, bans, appeals, or anything account-specific, a real staff member in Discord is the right place.',actions:actions.discord};
  if(topic==='music')return{text:`The site soundtrack is “Midnight in Miamidian.” Use the music button to ${musicPlaying?'pause':'play'} it, and the slider controls volume.`};
  if(topic==='site')return{text:'This site is the hub for Sir. Miamidian’s City: community info, team, applications, reviews, Steam games, music, and support.'};
  if(topic==='team')return{text:'You can check the Team section for the people behind the city.',actions:actions.team};
  if(topic==='apply')return{text:'Applications are in the Apply section whenever opportunities are open.',actions:actions.apply};
  if(topic==='reviews')return{text:'Community feedback lives in the Reviews section.',actions:actions.reviews};
  if(topic==='hello')return{text:`Hey${botState.name?` ${botState.name}`:''} 👋 Ask me about joining, rules, roles, VCs, games, staff, music, or where something is on the site.`};
  if(/where|how|what about|and that|what then/.test(s)&&botState.lastTopic!=='general')return answerFor(botState.lastTopic);
  return{text:'I’m not sure about that one yet. I’m best at server info and navigating this site. Try asking “how do I join?”, “recommend me a game”, “where are applications?”, or “I need staff help”.'};
}

function askBot(q){botState.messageCount++;addMsg(q,'user');aiInput.value='';const typing=addTyping();const delay=Math.min(1050,340+q.length*9);setTimeout(()=>{typing.remove();const out=answerFor(q);addMsg(out.text,'bot',{actions:out.actions})},delay)}
aiForm?.addEventListener('submit',e=>{e.preventDefault();const q=aiInput.value.trim();if(q)askBot(q)});

if(aiForm&&aiMessages&&!document.getElementById('aiQuick')){
  const quick=document.createElement('div');quick.id='aiQuick';quick.className='ai-quick';
  ['Join server','Recommend a game','Show me applications','I need staff help'].forEach(label=>{const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',()=>askBot(label));quick.appendChild(b)});aiForm.parentNode.insertBefore(quick,aiForm);
  const css=document.createElement('style');css.textContent=`.ai-quick{display:flex;gap:7px;flex-wrap:wrap;padding:0 12px 10px}.ai-quick button{border:1px solid rgba(100,190,255,.28);background:rgba(17,82,145,.22);color:#bfe2ff;padding:8px 10px;border-radius:999px;font-size:10px;font-weight:800;cursor:pointer}.ai-quick button:hover{background:rgba(25,117,204,.38);color:#fff}.ai-msg.typing{opacity:.65;font-style:italic}.ai-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:9px}.ai-actions a,.ai-actions button{display:inline-flex;align-items:center;text-decoration:none;border:1px solid rgba(104,191,255,.34);background:rgba(18,114,203,.28);color:#dff2ff;padding:7px 10px;border-radius:999px;font-size:10px;font-weight:800;cursor:pointer}.ai-actions a:hover,.ai-actions button:hover{background:rgba(25,135,231,.5);color:#fff}`;document.head.appendChild(css);
}

// Steam library filters
const steamFilterButtons=[...document.querySelectorAll('.steam-filters button')],steamCards=[...document.querySelectorAll('.steam-card')];
steamFilterButtons.forEach(btn=>btn.addEventListener('click',()=>{const filter=btn.textContent.trim().toLowerCase();steamFilterButtons.forEach(b=>b.classList.remove('active'));btn.classList.add('active');steamCards.forEach(card=>{const searchable=(card.querySelector('.steam-card-body')?.textContent||'').toLowerCase();card.style.display=filter==='all'||searchable.includes(filter)?'':'none'})}));
