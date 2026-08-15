import json,re,urllib.request

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36'

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9'})
    with urllib.request.urlopen(req,timeout=25) as r:
        return r.read().decode('utf-8','ignore')

def compact_to_int(s):
    s=s.replace(',','').strip().upper()
    m=re.search(r'([0-9]+(?:\.[0-9]+)?)([KMB]?)',s)
    if not m:return None
    n=float(m.group(1)); mult={'':1,'K':1000,'M':1000000,'B':1000000000}[m.group(2)]
    return int(n*mult)

out={}

# YouTube
try:
    y=get('https://socialblade.com/youtube/handle/hisytstory')
    for p in [r'subscribers\s*</div>\s*<div[^>]*>\s*([0-9.,]+[KMB]?)', r'His Story@hisytstory.*?subscribers\s*([0-9.,]+[KMB]?)']:
        m=re.search(p,y,re.I|re.S)
        if m:
            v=compact_to_int(m.group(1))
            if v and v>100000: out['youtube']=v; break
except Exception as e:
    print('youtube',e)

# TikTok: use the profile metric directly and reject tiny false matches.
try:
    t=get('https://urlebird.com/es/user/hisytstory/')
    patterns=[
        r'([0-9]+(?:\.[0-9]+)?[KMB])\s*(?:seguidores|followers)',
        r'(?:seguidores|followers)[^0-9]{0,120}([0-9]+(?:\.[0-9]+)?[KMB])'
    ]
    for p in patterns:
        for m in re.finditer(p,t,re.I|re.S):
            v=compact_to_int(m.group(1))
            if v and 100000 <= v <= 1000000000:
                out['tiktok']=v
                break
        if 'tiktok' in out: break
except Exception as e:
    print('tiktok',e)

# Discord
try:
    d=json.loads(get('https://discord.com/api/v10/invites/hisytstory?with_counts=true'))
    if isinstance(d.get('approximate_member_count'),int):
        out['discord']=d['approximate_member_count']
except Exception as e:
    print('discord',e)

try:
    with open('stats.json','r',encoding='utf-8') as f: old=json.load(f)
except Exception:
    old={}
for k in ('youtube','tiktok','discord'):
    if k not in out and isinstance(old.get(k),int): out[k]=old[k]

with open('stats.json','w',encoding='utf-8') as f:
    json.dump(out,f,separators=(',',':'))
print(out)
