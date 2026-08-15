const $=id=>document.getElementById(id);

function animateNumber(el,value){
  const from=Number((el.textContent||'').replace(/[^0-9]/g,''))||0;
  const start=performance.now(),duration=900;
  function frame(now){
    const p=Math.min((now-start)/duration,1);
    const eased=1-Math.pow(1-p,3);
    el.textContent=Math.round(from+(value-from)*eased).toLocaleString();
    if(p<1)requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

async function updateDiscord(){
  try{
    const r=await fetch('https://discord.com/api/v10/invites/hisytstory?with_counts=true');
    if(!r.ok)throw new Error('Discord request failed');
    const d=await r.json();
    if(typeof d.approximate_member_count==='number'){
      animateNumber($('discord-count'),d.approximate_member_count);
      $('discord-status').textContent='Live · refreshes automatically';
    }
  }catch(e){
    $('discord-status').textContent='Count temporarily unavailable';
  }
}

// YouTube and TikTok need a server-side/API data source. These hooks are ready
// so their values can be enabled without redesigning the page.
async function updateExternalStats(){
  try{
    const r=await fetch('./stats.json',{cache:'no-store'});
    if(!r.ok)return;
    const d=await r.json();
    if(Number.isFinite(d.youtube)){
      animateNumber($('youtube-count'),d.youtube);
      $('youtube-status').textContent='@hisytstory · auto-updated';
    }
    if(Number.isFinite(d.tiktok)){
      animateNumber($('tiktok-count'),d.tiktok);
      $('tiktok-status').textContent='@hisytstory · auto-updated';
    }
  }catch(e){}
}

updateDiscord();
updateExternalStats();
setInterval(updateDiscord,60000);
setInterval(updateExternalStats,60000);