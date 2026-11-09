from pathlib import Path
import json,subprocess
from html.parser import HTMLParser
R=Path(__file__).resolve().parents[1]
class Count(HTMLParser):
    def __init__(self):super().__init__();self.count={}
    def handle_starttag(self,tag,attrs):self.count[tag]=self.count.get(tag,0)+1
rows=[]
for name in ['README.md','README.en.md']:
    req=R/'.cache'/('render_'+name+'.json')
    req.write_text(json.dumps({'text':(R/name).read_text(encoding='utf-8'),'mode':'gfm','context':'Shuluun/lcstop-method-evaluation'}),encoding='utf-8')
    output=subprocess.check_output(['gh','api','markdown','--method','POST','--input',str(req)],cwd=R)
    html=output.decode('utf-8')
    c=Count();c.feed(html)
    (R/'.cache'/(name+'.html')).write_text(html,encoding='utf-8')
    rows.append({'file':name,'github_gfm_render':'PASS','table_count':c.count.get('table',0),'image_count':c.count.get('img',0),'h1_count':c.count.get('h1',0),'html_bytes':len(output)})
ok=all(x['table_count']==3 and x['image_count']==2 and x['h1_count']==1 for x in rows)
v={'status':'PASS' if ok else 'FAIL','scope':'GitHub GFM rendering, structural checks; not visual screenshot or scientific validation','readmes':rows}
(R/'public_release_v1/render_check.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
print(json.dumps(v,indent=2))
if not ok:raise SystemExit(1)