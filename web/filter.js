export function filterArticles(articles,f,now=new Date()){
 const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
 const lower=f.period==='7'||f.period==='30'?new Date(Date.parse(today+'T00:00:00Z')-(Number(f.period)-1)*86400000).toISOString().slice(0,10):'';
 const query=(f.search||'').toLowerCase().trim();
 return articles.filter(p=>(!lower||p.date>=lower)&&(!f.journal||p.journalId===f.journal)&&(!f.topic||p.topics.includes(f.topic))&&(!f.grade||(f.grade==='recommended'?p.grade==='A'||p.grade==='B':p.grade===f.grade))&&(!f.pending||p.pending)&&(f.period!=='custom'||((!f.start||p.date>=f.start)&&(!f.end||p.date<=f.end)))&&(!query||`${p.title} ${p.abstract} ${p.doi}`.toLowerCase().includes(query)));
}
export function sortArticles(articles){return [...articles].sort((a,b)=>a.grade.localeCompare(b.grade)||b.date.localeCompare(a.date)||b.score-a.score);}
