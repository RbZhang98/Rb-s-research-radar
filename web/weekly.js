import {profileOf} from './store.js';
// Pure deterministic rules. Inputs are local notes; no AI calls or network.
const label={basic:'基础研究',clinical:'临床研究'};
const wordMatch=(text,term)=>new RegExp(`(^|[^a-z])${term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?![a-z])`,'i').test(text);
export const shanghaiDay=value=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value));
export function makeWeekly(notes,{radar,start,end,terms=[]}){
 const selected=notes.filter(n=>n.radars.includes(radar)).map(n=>({...n,...profileOf(n,radar),updatedAt:n.updatedAt,radar})).filter(n=>shanghaiDay(n.updatedAt)>=start&&shanghaiDay(n.updatedAt)<=end);
 const important=selected.filter(n=>n.favorite||n.relevance>=4||n.inspiration>=4);
 const high=selected.filter(n=>n.relevance>=4||n.inspiration>=4);const low=selected.filter(n=>n.relevance>0&&n.relevance<=2);
 const vocab=[...new Set([...terms,...selected.flatMap(n=>n.tags)])].filter(t=>t.trim());
 const count=(list,t)=>list.filter(n=>wordMatch(`${n.article.title} ${n.article.abstract||''} ${n.tags.join(' ')}`,t));
 const themes=vocab.map(term=>({term,high:count(high,term),low:count(low,term)})).filter(t=>t.high.length||t.low.length).sort((a,b)=>b.high.length-a.high.length||a.term.localeCompare(b.term));
 const suggestions=themes.filter(t=>t.high.length>=2).map(t=>({term:t.term,sourceKeys:t.high.map(n=>n.key),reason:`${t.high.length}篇高评分文章命中，建议人工审核后加入个人关注词。`}));
 const deprioritize=themes.filter(t=>t.low.length>=3&&t.high.length===0).map(t=>({term:t.term,sourceKeys:t.low.map(n=>n.key),reason:`${t.low.length}篇已评分文章相关性≤2，暂无高评分支持；只建议降低个人优先级，不改变抓取范围。`}));
 return {radar,start,end,selected,important,high,themes,suggestions,deprioritize};
}
const text=s=>String(s||'').replace(/[\r\n]+/g,' ').replace(/([\\`*_[\]<>])/g,'\\$1');
const cite=n=>`${text(n.article.title)}（${n.article.date||'日期缺失'}；DOI：${text(n.doi||n.article.id)}；记录更新：${n.updatedAt}）`;
export function weeklyMarkdown(r){
 const out=[`# ${label[r.radar]}科研周报`,`${r.start} — ${r.end}；按笔记的北京时间修改日期选择，不按论文发表日期。`,'','本报告为元数据与个人笔记的规则整理，无模型分析。个人假设未经验证。','', '## 1. 本周最值得阅读的论文'];
 const best=[...r.important].sort((a,b)=>(b.relevance*2+b.inspiration)-(a.relevance*2+a.inspiration)).slice(0,5);
 for(const n of best)out.push(`- ${cite(n)}；本 Radar 相关性 ${n.relevance||'未评'} / 启发性 ${n.inspiration||'未评'}`);
 if(!best.length)out.push('暂无个人评分或收藏支持的推荐。');
 out.push('','## 2. 本周收藏及高评分论文');for(const n of r.important)out.push(`- ${cite(n)}`);if(!r.important.length)out.push('暂无记录。');
 for(const [title,key] of [['3. 我的批注摘录','annotations'],['4. 值得借鉴的研究设计','methods']]){out.push('',`## ${title}`);const rows=r.selected.filter(n=>n[key]);for(const n of rows)out.push(`- 来源：${cite(n)}`,`  - ${text(n[key])}`);if(!rows.length)out.push('暂无记录。');}
 out.push('','## 5. 本次观察到的主题与机制词');for(const t of r.themes.filter(t=>t.high.length))out.push(`- ${text(t.term)}：${t.high.length}篇高评分文章；DOI：${t.high.map(n=>text(n.doi||n.article.id)).join('；')}`);out.push('以上为词组命中，不表示发现新机制或证明可迁移至成骨。');
 out.push('','## 6. 我的研究假设及待验证问题');for(const n of r.selected.filter(n=>n.hypotheses||n.questions))out.push(`- 来源：${cite(n)}`,`  - 我的假设：${text(n.hypotheses||'未填写')}`,`  - 待验证问题：${text(n.questions||'未填写')}`);
 out.push('','## 7. 建议新增的关键词（需人工审核）');for(const t of r.suggestions)out.push(`- ${text(t.term)}：${t.reason} 来源 DOI：${t.sourceKeys.map(k=>text(k.replace(/^doi:/,''))).join('；')}`);if(!r.suggestions.length)out.push('至少需要2篇高评分文章支持；当前证据不足，暂不新增。');
 out.push('','## 8. 下周值得关注的方向');for(const t of r.suggestions)out.push(`- 待审核方向：${text(t.term)}；来自高评分文章的个人反馈，不是新的学术结论。`);if(!r.suggestions.length)out.push('继续原有核心方向，积累评分与方法笔记。');
 out.push('','## 不建议继续高优先级推荐的主题（仅建议，不修改抓取范围）');for(const t of r.deprioritize)out.push(`- ${text(t.term)}：${t.reason} 来源 DOI：${t.sourceKeys.map(k=>text(k.replace(/^doi:/,''))).join('；')}`);if(!r.deprioritize.length)out.push('至少3篇低评分且无高评分支持才产生建议；当前保持原有范围。');
 out.push('','## 个人关注原因与低评分原因');for(const n of r.selected.filter(n=>n.lowReason||n.reasons?.length))out.push(`- ${cite(n)}；关注原因：${text(n.reasons?.join(' / ')||'未填写')}；低评分原因：${text(n.lowReason||'未填写')}`);
 return out.join('\n');
}
