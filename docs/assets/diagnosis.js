"use strict";
const $ = id => document.getElementById(id);
let result = null, selected = null;
let originalDiagnosis = null;
const esc = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number = value => value === null ? 'Unavailable' : String(Number(Number(value).toFixed(3)));
const signed = value => (value >= 0 ? '+' : '−') + number(Math.abs(value));
function status(message, error=false) { $('status').textContent=message; $('status').className=error?'error':''; $('status').hidden=!message; }

// Lightweight syntax coloring runs only on escaped text; source is never executed.
function syntaxTokens(source) {
  const pattern = /(?:\/\/[^\n]*|\/\*[\s\S]*?\*\/|#[^\n]*)|(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|\b(?:class|static|public|private|protected|int|long|double|boolean|String|return|if|else|for|while|switch|case|new|void|def|import|from|as|None|True|False|try|except|with|in|and|or|not|lambda)\b|\b\d+(?:\.\d+)?\b/g;
  const tokens=[]; let match;
  while ((match=pattern.exec(source))) {
    const value=match[0];
    const type=/^(\/\/|\/\*|#)/.test(value)?'comment':/^["']/.test(value)?'str':/^\d/.test(value)?'num':'kw';
    tokens.push({start:match.index,end:match.index+value.length,type});
  }
  return tokens;
}
function renderCode(target='code', highlight=true) {
  if (!result) return;
  if (result.source_visible === false) {
    const node=$(target); if(!node)return;
    delete node.dataset.copySource;
    node.dataset.noCodeCopy = 'true';
    node.classList.remove('diagnostic-code');
    const frame=node.closest('.copy-code-frame');
    if(frame){frame.before(node);frame.remove();}
    const link=document.createElement('a');link.href=result.source_url;link.textContent='Official dataset source';
    node.replaceChildren(link);
    return;
  }
  const source=result.source, positions=[0];
  delete $(target).dataset.noCodeCopy;
  $(target).classList.add('diagnostic-code');
  $(target).classList.remove('source-reference');
  $(target).dataset.copySource = source;
  for(const character of source)positions.push(positions[positions.length-1]+character.length);
  const regions=(highlight?selected?.regions||[]:[]).map(region=>({...region,start:positions[region.start],end:positions[region.end]})), tokens=syntaxTokens(source);
  let offset=0;
  $(target).innerHTML=source.split('\n').map((line,index)=>{
    const start=offset,end=offset+line.length;offset=end+1;
    const cuts=new Set([start,end]);
    [...regions,...tokens].forEach(r=>{if(r.start<end&&r.end>start){cuts.add(Math.max(start,r.start));cuts.add(Math.min(end,r.end));}});
    const points=[...cuts].sort((a,b)=>a-b);let html='';
    for(let i=0;i<points.length-1;i++){
      const a=points[i],b=points[i+1];const token=tokens.find(t=>t.start<=a&&t.end>=b);
      const highlight=regions.some(r=>r.start<=a&&r.end>=b);
      html+=`<span class="${token?.type||''} ${highlight?'highlight':''}">${esc(source.slice(a,b))}</span>`;
    }
    return `<div class="code-line" id="${target}-line-${index+1}"><span class="line-number">${index+1}</span><span class="line-text">${html||' '}</span></div>`;
  }).join('');
}
function choose(feature) {
  selected=feature;
  document.querySelectorAll('.diagnosis-feature').forEach(button=>button.classList.toggle('active',button.dataset.key===feature.key));
  $('selected-name').textContent=feature.name;
  $('description').textContent=feature.description;
  renderCode();
}

function render(data) {
  result=data;
  const features=[...data.features].sort((a,b)=>Math.abs(b.contribution)-Math.abs(a.contribution));
  $('features').replaceChildren();
  features.forEach(feature=>{
    const button=document.createElement('button');button.className='diagnosis-feature';
    button.dataset.key=feature.key;
    button.innerHTML=`<span>${esc(feature.name)}<small>Measured value: ${number(feature.value)}${feature.imputed?' · imputed':''}</small></span><strong class="${feature.contribution<0?'penalty':'benefit'}">${signed(feature.contribution)}</strong>`;
    button.onclick=()=>choose(feature);$('features').append(button);
  });
  $('equation').className='score-equation';
  $('equation').textContent=`Intercept ${number(data.intercept)} + feature contributions = ${number(data.unbounded_score)}${data.output_clipped?' → bounded score '+number(data.score):''}.`;
  renderCode('plain-code', false);
  choose(features.find(f=>!f.imputed)||features[0]);
}
async function initializeDiagnosis(){
 const panel=$('mode-bttf');
 try{
  const response=await fetch(panel.dataset.diagnosisUrl || ('/api/diagnosis?dataset='+encodeURIComponent(panel.dataset.dataset)+'&index='+panel.dataset.index));
  const data=await response.json();if(!response.ok)throw Error(data.error);
  originalDiagnosis = data;
  render(window.BTTFSourceImport ? await window.BTTFSourceImport.hydrate(data) : data);status('');
 }catch(error){status(error.message,true);}
}
initializeDiagnosis();
document.addEventListener('bttf-source-change', async event => {
  if (!originalDiagnosis || event.detail.dataset !== originalDiagnosis.dataset) return;
  render(await window.BTTFSourceImport.hydrate(originalDiagnosis));
});
