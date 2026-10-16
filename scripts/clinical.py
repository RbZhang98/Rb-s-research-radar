"""Clinical ranking is independent of the basic Radar score; never mutates it."""
import re
try: from scripts.radar import read
except ModuleNotFoundError: from radar import read

def classify_clinical(p):
    rules=read('config/clinical-rules.json'); text=(p['title']+' '+p.get('abstract','')).lower()
    pubtypes=[str(t).lower() for t in p.get('publicationTypes',[])]
    metadata=' '.join(pubtypes); evidence={}
    for label,terms in rules['types'].items():
        matched=[t for t in terms if t in metadata]
        if matched:evidence[label]={'terms':matched,'source':'来源研究类型'}
    # A bare 'review' in an abstract is not enough to label the article a review.
    for label,terms in rules['types'].items():
        corpus=p['title'].lower() if label in ['综述','更正 / 通知'] else text
        matched=[t for t in terms if re.search(r'(?<![a-z])'+re.escape(t)+r'(?![a-z])',corpus)]
        if matched and label not in evidence:evidence[label]={'terms':matched,'source':'标题/摘要规则，未经人工确认'}
    priority=['更正 / 通知','随机对照试验','系统综述 / Meta分析','临床前研究','前瞻性队列','回顾性队列','临床病例系列','队列研究','病例对照研究','横断面研究','临床研究','叙述性综述','综述']
    kind=next((k for k in priority if k in evidence),'研究类型待确认')
    confirmed=kind in evidence and evidence[kind]['source']=='来源研究类型'
    grade='A' if kind in ['随机对照试验','系统综述 / Meta分析'] else 'C' if kind in ['临床前研究','更正 / 通知'] else 'B'
    topics=[k for k,terms in rules['topics'].items() if any(t in text for t in terms)]
    return {'grade':grade,'score':{'A':10,'B':5,'C':0}[grade],'topics':topics,'pending':not confirmed or not p.get('abstract'), 'studyType':kind,'studyTypeEvidence':evidence.get(kind,{}),'evidence':evidence,'reason':f'临床独立规则：{kind}。'+('研究类型来自元数据；' if confirmed else '类型由词组初筛或信息不足，待确认；')+'优先级不等同于研究质量评价。','rulesVersion':rules['version']}
