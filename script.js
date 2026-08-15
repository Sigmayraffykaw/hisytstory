const $=id=>document.getElementById(id);
function animateNumber(el,value){const from=Number((el.textContent||'').replace(/[^0-9]/g,''))||0;const start=performance.now(),duration=900;function frame(now){const p=Math.min((now-start)/duration,1);const eased=1-Math.pow(1-p,3);el.textContent=Math.round(from+(value-from)*eased).toLocaleString();if(p<1)requestAnimationFrame(frame)}requestAnimationFrame(frame)}
async function updateStats(){try{const r=await fetch('./stats.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('stats unavailable');const d=await r.json();if(Number.isFinite(d.youtube)){animateNumber($('youtube-count'),d.youtube);$('youtube-status').textContent='@hisytstory · auto-updated'}if(Number.isFinite(d.tiktok)){animateNumber($('tiktok-count'),d.tiktok);$('tiktok-status').textContent='@hisytstory · auto-updated'}if(Number.isFinite(d.discord)){animateNumber($('discord-count'),d.discord);$('discord-status').textContent='discord.gg/hisytstory · auto-updated'}}catch(e){console.error(e)}}

function applyStaffAvatars(){
  const avatars={
    'His Story':'76c815df-a63e-48b0-800c-aa51e82d3df8.png',
    'shadeL':'6168f702-8f6b-47a6-ba1f-8c9b055a191d.png',
    'Violet.':'3fe8d988-4002-465f-bc53-73164c4e42a7.png',
    'Ria/Riri':'a_d27463cc6eac52ffd3fd51b330864810.png',
    'YZY mono':'ff214f60-6ecc-4d63-ad11-667e1e76539c.png',
    'FOXY102051 / PUSO | @For Help ᰔᩚ':'fb4df6ad-d053-4440-a3de-8e6226941287.png',
    'Skyler | @ For Help':'3f0de4ae-1954-4cea-8cc7-59c0753df5d7.png',
    'G o o g l e':'aa94fd35-8e36-4d7c-bf0d-3813b48a6964.png',
    'Sir. MIAMIDIAN':'f7fd4849-8882-40cd-84ba-8ab3d9bb0c2a.png',
    'Wesley S':'68a9e37e-a93f-43d3-bf13-fa3431f78982.png',
    'tam🕷':'df0e6f33-ff1a-4059-9a05-d529ad81d746.png',
    'ⁿⁱᵏᵒᵒ | ping 4 help':'5b364cde-3cf4-4aa6-a648-aa419dcb2d84.png',
    'zdery | @ For Help':'323ed662-5fdc-4595-bbff-17156c75c6fd.png',
    'ᴋɪʟᴢᴀʀ':'6fe7a31e-3a69-4d52-a65b-fb0d63b5fe3b.png',
    'dwz_84':'aad7266a-9d99-4959-a404-7ae5473c959d.png',
    'kyoto':'2fabe43c-06d8-4494-946f-6f2836ee2e9f.png',
    '𝓽𝓸𝓪𝓼𝓽':'3646f968-9a87-4b73-a143-26683a23a7d9.png',
    'Rhombicosidodecahedron':'eef67e7b-7fbf-4452-8f8e-9e73dbe606b4.png'
  };

  const staffSection=[...document.querySelectorAll('section')].find(s=>s.querySelector('h2')?.textContent.trim()==='Meet the Staff');
  if(!staffSection)return;

  if(![...staffSection.querySelectorAll('b')].some(b=>b.textContent.trim()==='His Story')){
    const firstGroup=staffSection.querySelector('.staff-group');
    const owner=document.createElement('div');
    owner.className='staff-group';
    owner.innerHTML='<h3>Owner</h3><div class="grid staff"><article><div class="avatar"></div><b>His Story</b><small>Owner</small></article></div>';
    staffSection.insertBefore(owner,firstGroup);
  }

  staffSection.querySelectorAll('.staff article').forEach(card=>{
    const name=card.querySelector('b')?.textContent.trim();
    const avatar=card.querySelector('.avatar');
    if(!name||!avatar||!avatars[name])return;
    avatar.textContent='';
    avatar.style.backgroundImage=`url('${avatars[name]}')`;
    avatar.style.backgroundSize='cover';
    avatar.style.backgroundPosition='center';
    avatar.style.flex='0 0 56px';
    avatar.style.width='56px';
    avatar.style.height='56px';
  });
}

applyStaffAvatars();
updateStats();
setInterval(updateStats,60000);