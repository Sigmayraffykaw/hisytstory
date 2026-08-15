import json,re,urllib.request

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36'

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9'})
    with urllib.request.urlopen(req,timeout=20) as r:
        return r.read().decode('utf-8','ignore')

def parse_compact(s):
    s=s.replace(',','').strip().upper()
    m=re.match(r'([0-9]+(?:\.[0-9]+)?)([KMB]?)',s)
    if not m:return None
    n=float(m.group(1)); mult={'':1,'K':1_000,'M':1_000_000,'B':1_000_000_000}[m.group(2)]
    return int(n*mult)

out={}

try:
    y=get('https://www.youtube.com/@hisytstory')
    pats=[r'"subscriberCountText":\{"simpleText":"([^"]+) subscribers"',r'([0-9.,]+[KMB]?) subscribers']
    for p in pats:
        m=re.search(p,y,re.I)
        if m:
            v=parse_compact(m.group(1))
            if v is not None: out['youtube']=v; break
except Exception as e:
    print('youtube:',e)

try:
    t=get('https://www.tiktok.com/@hisytstory')
    pats=[r'"followerCount":(\d+)',r'"followerCount":"(\d+)"']
    for p in pats:
        m=re.search(p,t)
        if m:
            out['tiktok']=int(m.group(1)); break
except Exception as e:
    print('tiktok:',e)

try:
    with open('stats.json','r',encoding='utf-8') as f: old=json.load(f)
except Exception:
    old={}
for k in ('youtube','tiktok'):
    if k not in out and isinstance(old.get(k),int): out[k]=old[k]

with open('stats.json','w',encoding='utf-8') as f:
    json.dump(out,f,separators=(',',':'))
print(out)
