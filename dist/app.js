import { filterArticles, sortArticles } from './filter.js';
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let articles=[],status={},view='today',limit=20;
const labels={A:'高度相关 · 重点阅读',B:'中度相关 · 值得关注',C:'低相关 · 归档'};
function render(){
 const f={period:$('#period').value,journal:$('#journal').value,topic:$('#topic').value,grade:$('#grade').value,pending:$('#pending').checked,search:$('#search').value,start:$('#start').value,end:$('#end').value};
 const list=sortArticles(filterArticles(articles,f));
 $('#customDates').hidden=f.period!=='custom';
 $('#topCount').textContent=list.filter(x=>x.grade==='A').length;
 $('#resultCount').textContent=`${list.length} 篇`;
 $('#cards').innerHTML=list.length?list.slice(0,limit).map(p=>`<article class="paper"><div class="paper-meta"><span class="journal-name">${esc(p.journal)}</span><span>${esc(p.date)}${p.datePrecision!=='day'?' · 日期精度：'+esc(p.datePrecision):''}</span><span class="grade ${esc(p.grade)}">${esc(p.grade)} · ${labels[p.grade]}</span></div><details><summary><h2>${esc(p.title)}</h2><span class="read">展开摘要与详情 ↗</span></summary><div class="detail"><h4>英文摘要</h4><p class="abstract">${p.abstract?esc(p.abstract):'数据源未提供摘要。仅依据标题筛选，待确认。'}</p><h4>推荐理由 · 规则证据</h4><p>${esc(p.reason)}</p><div class="metadata">DOI: ${esc(p.doi||'未提供')}<br>元数据来源：${esc(p.sources.join(' / '))}</div><a class="external" href="${esc(p.url)}" target="_blank" rel="noopener noreferrer">访问原文网页 ↗</a></div></details><div class="paper-bottom"><div class="tags">${p.topics.map(t=>`<span>${esc(t.slice(2))}</span>`).join('')||'<span>未命中目标主题</span>'}${p.pending?'<span class="pending">待确认</span>':''}</div>${p.abstract?'':'<small class="muted">摘要缺失</small>'}</div></article>`).join(''):'<div class="empty"><h3>当前筛选下没有文献</h3><p>可选择全部历史、全部等级，或调整检索词。请同时查看运行状态，确认数据源是否抓取成功。</p></div>';
 $('#more').hidden=list.length<=limit;
}
function renderStatus(){
 $('#statusPanel').innerHTML=`<h2>抓取与来源状态</h2><p>最近尝试：${esc(status.attemptAt)}<br>最近一次全部期刊双来源成功抓取：${esc(status.lastSuccess||'尚无完整成功记录')}<br>检索窗口：${esc(status.window?.start)} — ${esc(status.window?.end)}</p><div class="status-note">${status.fetchOk?'本次抓取完整成功。':'本次抓取存在失败；失败不能解释为没有新论文。'} 发布结果请以 GitHub Actions 的部署任务为准。此数据文件不声明网站部署成功。</div><div class="status-grid">${(status.journals||[]).map(j=>`<article class="status-card"><h3>${esc(j.name)} <span class="${j.ok?'ok':'bad'}">${j.ok?'完整成功':'不完整'}</span></h3><p>历史 ${j.total} 篇 · 摘要缺失 ${j.missingAbstract} 篇<br>双来源交集 ${j.bothSources} 篇<br>最近完整成功：${esc(j.lastSuccess||'暂无')}</p>${j.sources.map(s=>`<p class="source-line"><b>${esc(s.source)}</b> ${s.ok?'✓ '+s.count+' 条':'失败：'+esc(s.error)}<br><small>${esc(s.query||'')}${s.unsupportedIssns?.length?'<br>Crossref 未提供该 ISSN 的独立接口：'+esc(s.unsupportedIssns.join(', '))+'；已查询其他注册 ISSN。':''}</small></p>`).join('')}</article>`).join('')}</div><details><summary>查看 ISSN 核验记录</summary><pre>${esc(JSON.stringify(status.verification,null,2))}</pre></details>`;
}
for(const b of document.querySelectorAll('[data-view]')) b.addEventListener('click',()=>{
 view=b.dataset.view;document.querySelectorAll('.nav').forEach(n=>n.classList.toggle('active',n===b));$('#library').hidden=view==='status';$('#statusPanel').hidden=view!=='status';
 $('#heading').textContent={today:'今日科研动态',history:'历史文献库',status:'数据与运行状态'}[view];
 $('#subtitle').textContent=view==='today'?'让新的线索，进入你的研究视野。':view==='history'?'保存发现，也保留发现的来路。':'区分没有新论文与抓取失败。';
 if(view!=='status'){$('#period').value=view==='history'?'all':'30';limit=20;render();}
});
$('#filters').addEventListener('submit',e=>e.preventDefault());
$('#filters').addEventListener('input',()=>{limit=20;render();});$('#filters').addEventListener('change',()=>{limit=20;render();});$('#more').addEventListener('click',()=>{limit+=20;render();});
try{
 const r=await Promise.all(['articles','status','journals','rules'].map(async n=>{const res=await fetch(`./data/${n}.json`,{cache:'no-cache'});if(!res.ok)throw Error(`${n}: HTTP ${res.status}`);return res.json();}));
 [articles,status]=r;$('#journalCount').textContent=r[2].length;$('#newCount').textContent=status.newCount;$('#totalCount').textContent=articles.length;
 $('#updated').textContent='最近完整抓取：'+(status.lastSuccess?new Date(status.lastSuccess).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false})+' 北京时间':'尚未成功');
 $('#journal').innerHTML+=[...r[2]].map(j=>`<option value="${esc(j.id)}">${esc(j.name)}</option>`).join('');
 $('#topic').innerHTML+=Object.keys(r[3].topics).map(t=>`<option value="${esc(t)}">${esc(t)}</option>`).join('');
 if(!status.fetchOk)$('#notice').innerHTML='<div class="warning">最近抓取不完整，当前显示已保存的历史记录。请查看「数据与运行状态」。</div>';
 else if(status.lastSuccess && Date.now()-Date.parse(status.lastSuccess)>48*3600000)$('#notice').innerHTML='<div class="warning">数据已超过48小时未完整更新，请检查 GitHub Actions。</div>';
 renderStatus();render();
}catch(e){$('#notice').innerHTML=`<div class="warning">数据加载失败：${esc(e.message)}。请通过 HTTP 服务访问本站，或检查部署文件。</div>`;$('#cards').innerHTML='<div class="empty">暂时无法读取文献数据。<button onclick="location.reload()">重新加载</button></div>';}
