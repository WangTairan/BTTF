from __future__ import annotations

import json
from html import escape
from pathlib import Path


def write_degradation_report(
    root: Path,
    records: list[dict[str, object]],
    title: str = "Source Interference Explorer",
    language: str = "java",
) -> None:
    samples = []
    for record in records:
        code = (root / str(record["local_path"])).read_text(encoding="utf-8")
        samples.append({**record, "code": code})
    payload = json.dumps(samples, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace("&", "\\u0026")
    (root / "obfuscation-report.html").write_text(
        _document(payload, title, language), encoding="utf-8"
    )


def _document(payload: str, title: str, language: str = "java") -> str:
    safe_title = escape(title)
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title}</title>
<style>
:root{{--bg:#f4f6fa;--panel:#fff;--text:#182033;--muted:#66728a;--line:#d8deea;--accent:#5b4bdb;--code:#f7f8fb;--shadow:0 8px 28px #1f2a4414}}
@media(prefers-color-scheme:dark){{:root{{--bg:#111522;--panel:#191f2e;--text:#eef2fa;--muted:#aab4c8;--line:#30394d;--accent:#a99cff;--code:#101520;--shadow:0 8px 28px #0005}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 system-ui,sans-serif}}main{{max-width:1500px;margin:auto;padding:22px}}h1{{font-size:26px;font-weight:600;margin:0 0 14px}}
.metrics{{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:14px}}.metric,.panel,.stage{{background:var(--panel);border:1px solid var(--line);border-radius:11px;box-shadow:var(--shadow)}}.metric{{padding:8px 12px}}.metric strong{{font-size:18px;margin-right:5px}}
.workspace{{display:grid;grid-template-columns:300px minmax(0,1fr);gap:18px;align-items:start}}.controls{{padding:13px;position:sticky;top:12px}}label{{display:grid;gap:4px;color:var(--muted);font-size:12px;margin-bottom:9px}}select,input{{width:100%;min-height:34px;padding:6px 8px;color:var(--text);background:var(--panel);border:1px solid var(--line);border-radius:7px;font:inherit}}#class-list{{height:430px;font-family:ui-monospace,monospace}}.meta{{color:var(--muted);font-size:12px;overflow-wrap:anywhere}}#status{{margin-bottom:8px}}
.timeline{{display:grid;gap:16px;position:relative}}.timeline:before{{content:"";position:absolute;left:20px;top:20px;bottom:20px;width:2px;background:var(--line)}}.stage{{position:relative;overflow:hidden;margin-left:42px}}.stage:before{{content:"";position:absolute;left:-29px;top:21px;width:13px;height:13px;border-radius:50%;background:var(--accent);border:4px solid var(--bg)}}.stage-head{{padding:11px 14px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:15px;align-items:flex-start}}.stage-title{{display:flex;gap:9px;align-items:center}}.stage-title h2{{font-size:16px;margin:0}}.pill{{background:var(--accent);color:white;border-radius:999px;padding:2px 8px;font-size:12px;font-weight:700}}.description{{color:var(--muted);font-size:12px;margin-top:3px}}.stats{{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end}}.stat{{border:1px solid var(--line);border-radius:999px;padding:2px 7px;color:var(--muted);font-size:11px;white-space:nowrap}}
.codewrap{{max-height:520px;overflow:auto;background:var(--code)}}pre{{margin:0;padding:15px;min-width:max-content}}code{{font:12.5px/1.52 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}.kw{{color:#7c3aed;font-weight:600}}.str{{color:#a33a18}}.num{{color:#ad3977}}.comment{{color:#718096;font-style:italic}}.empty{{padding:50px;text-align:center;color:var(--muted)}}
@media(max-width:850px){{.workspace{{grid-template-columns:1fr}}.controls{{position:static}}.timeline:before,.stage:before{{display:none}}.stage{{margin-left:0}}.stage-head{{display:block}}.stats{{justify-content:flex-start;margin-top:8px}}}}
</style></head><body><main><h1>{safe_title}</h1>
<div class="metrics"><div class="metric"><strong id="base-count">0</strong>classes</div><div class="metric"><strong id="variant-count">0</strong>versions</div><div class="metric"><strong id="level-count">0</strong><span id="axis-label">stages</span></div><div class="metric"><strong id="mode">—</strong>mode</div></div>
<div class="workspace"><aside class="panel controls"><label>Source<select id="source"><option value="all">All</option></select></label><label>Search<input id="search" type="search" placeholder="Class or path"></label><div class="meta" id="status"></div><select id="class-list" size="18"></select><div class="meta" id="selection-meta"></div></aside><section id="empty" class="panel empty">Select a class.</section><section id="timeline" class="timeline" hidden></section></div>
<script id="dataset" type="application/json">{payload}</script><script>
(()=>{{const rows=JSON.parse(document.getElementById('dataset').textContent),$=id=>document.getElementById(id);const groups=new Map;for(const r of rows){{if(!groups.has(r.base_sample_id))groups.set(r.base_sample_id,[]);groups.get(r.base_sample_id).push(r)}}for(const v of groups.values())v.sort((a,b)=>a.order-b.order);let visible=[...groups.keys()],selected=visible[0];
const esc=s=>s.replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}})[c]);const language={json.dumps(language)};const javaWords='abstract boolean break byte case catch char class continue default do double else enum extends final finally float for if implements import instanceof int interface long native new package private protected public record return short static strictfp super switch synchronized this throw throws transient try void volatile while true false null';const pythonWords='and as assert async await break class continue def del elif else except False finally for from global if import in is lambda None nonlocal not or pass raise return True try while with yield';const kws=new Set((language==='python'?pythonWords:javaWords).split(' '));
function hi(s){{let out='',i=0;while(i<s.length){{if((language==='python'&&s[i]==='#')||(language!=='python'&&s.startsWith('//',i))){{let j=s.indexOf(String.fromCharCode(10),i);if(j<0)j=s.length;out+=`<span class="comment">${{esc(s.slice(i,j))}}</span>`;i=j;continue}}if(language!=='python'&&s.startsWith('/*',i)){{let j=s.indexOf('*/',i+2);j=j<0?s.length:j+2;out+=`<span class="comment">${{esc(s.slice(i,j))}}</span>`;i=j;continue}}if(s[i]==='"'||s[i]==="'"){{const q=s[i];let j=i+1;while(j<s.length){{if(s.charCodeAt(j)===92)j+=2;else if(s[j++]===q)break}}out+=`<span class="str">${{esc(s.slice(i,j))}}</span>`;i=j;continue}}if(/\\d/.test(s[i])){{let j=i+1;while(/[\\w._]/.test(s[j]||''))j++;out+=`<span class="num">${{esc(s.slice(i,j))}}</span>`;i=j;continue}}if(/[A-Za-z_$]/.test(s[i])){{let j=i+1;while(/[\\w$]/.test(s[j]||''))j++;const w=s.slice(i,j);out+=kws.has(w)?`<span class="kw">${{w}}</span>`:esc(w);i=j;continue}}out+=esc(s[i++])}}return out}}
const label=s=>s.replaceAll('_',' ');function ownStats(r){{if(!r.order)return[];return Object.entries(r.transformation_stats).filter(([k,v])=>(v>0||k.endsWith('_template_index'))&&!k.endsWith('_available')).map(([k,v])=>`${{label(k)}}: ${{v.toLocaleString()}}`)}}
function filter(){{const src=$('source').value,q=$('search').value.toLowerCase();visible=[...groups].filter(([,v])=>{{const b=v[0];return(src==='all'||b.source===src)&&(!q||`${{b.unit_name}} ${{b.source_path}}`.toLowerCase().includes(q))}}).map(([k])=>k);const list=$('class-list');list.replaceChildren();for(const id of visible){{const b=groups.get(id)[0],o=document.createElement('option');o.value=id;o.textContent=`${{b.source_name}} · ${{b.unit_name}}`;list.append(o)}}$('status').textContent=`${{visible.length}} matching classes`;if(visible.length){{selected=visible.includes(selected)?selected:visible[0];list.value=selected;render()}}else{{$('timeline').hidden=true;$('empty').hidden=false;$('selection-meta').textContent=''}}}}
function render(){{const variants=groups.get(selected),orig=variants[0],host=$('timeline');host.replaceChildren();for(const r of variants){{const card=document.createElement('article');card.className='stage';const stats=ownStats(r),pill=r.display_label;card.innerHTML=`<div class="stage-head"><div><div class="stage-title"><span class="pill">${{esc(pill)}}</span><h2>${{esc(r.stage.replaceAll('-',' '))}}</h2></div><div class="description">${{esc(r.description||'')}}</div></div><div class="stats"><span class="stat">${{r.line_count}} lines</span>${{stats.map(s=>`<span class="stat">${{esc(s)}}</span>`).join('')}}</div></div><div class="codewrap"><pre><code>${{hi(r.code)}}</code></pre></div>`;host.append(card)}}$('selection-meta').textContent=`${{orig.source_path}}`;$('empty').hidden=true;host.hidden=false}}
for(const [value,label] of new Map(rows.map(r=>[r.source,r.source_name])).entries()){{const o=document.createElement('option');o.value=value;o.textContent=label;$('source').append(o)}}$('base-count').textContent=groups.size;$('variant-count').textContent=rows.length;$('level-count').textContent=new Set(rows.filter(r=>r.order>0).map(r=>r.stage)).size;$('axis-label').textContent='interferences';$('mode').textContent='independent-interference';$('source').oninput=filter;$('search').oninput=filter;$('class-list').onchange=e=>{{selected=e.target.value;render()}};filter()}})();
</script></main></body></html>"""
    return document
