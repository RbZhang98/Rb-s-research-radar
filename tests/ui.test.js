import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';import {JSDOM} from 'jsdom';import 'fake-indexeddb/auto';
import {allNotes,closeDB,allPreferences} from '../web/store.js';
const json=async p=>JSON.parse(await readFile(new URL('../'+p,import.meta.url),'utf8'));
const tick=()=>new Promise(r=>setTimeout(r,35));
test('DOM integration: Radar isolation, favorite, rating, notes, reopen, restore preview, and traced weekly report',async()=>{
 const dom=new JSDOM(await readFile(new URL('../web/index.html',import.meta.url),'utf8'),{url:'https://rbzhang98.github.io/Rb-s-research-radar/'});
 for(const name of ['window','document','location'])globalThis[name]=dom.window[name];globalThis.alert=()=>{};globalThis.confirm=()=>true;
 const dialog=document.querySelector('dialog');dialog.showModal=()=>dialog.setAttribute('open','');dialog.close=()=>dialog.removeAttribute('open');
 const basic=await json('data/articles.json'),sample=(await json('reports/v2-clinical-validation.json')).samples;
 const resources={status:await json('data/status.json'),'clinical-status':await json('data/clinical-status.json'),journals:await json('config/journals.json'),rules:await json('config/rules.json'),'clinical-journals':await json('config/clinical-journals.json'),'clinical-rules':await json('config/clinical-rules.json')};
 for(const [radar,rows] of [['basic',basic],['clinical',sample]]){resources[radar+'/manifest']={radar,retainedCount:rows.length,chunks:[{file:'page-0001.json',start:'2026-09-16',end:'2026-10-16'}]};resources[radar+'/page-0001']=rows;}
 const requested=[];globalThis.fetch=async url=>{requested.push(url);assert.ok(url.startsWith('./data/'),'Only relative public metadata requests permitted');const name=url.replace('./data/','').replace(/\.json$/,'');if(!resources[name])throw Error('Unexpected URL '+url);return {ok:true,json:async()=>structuredClone(resources[name])};};
 await import('../web/app.js?dom-test');const $=s=>document.querySelector(s);assert.equal($('#heading').textContent,'基础研究 Radar');assert.equal(Number($('#totalCount').textContent), basic.length);
 $('#search').value='periostin';$('#search').dispatchEvent(new window.Event('input',{bubbles:true}));await tick();
 window.location.hash='clinical';await tick();assert.equal($('#search').value,'');assert.equal($('#journalCount').textContent,'4');assert.ok($('#cards').textContent.includes(sample[0].title));
 $('#cards [data-action="favorite"]').click();await tick();assert.equal((await allNotes()).length,1);assert.equal((await allNotes())[0].favorite,true);
 $('#cards [data-action="edit"]').click();$('#noteAnnotations').value='PRIVATE_CLINICAL_NOTE';$('#noteMethods').value='paired study design';$('#noteHypotheses').value='test local hypothesis';$('#noteQuestions').value='does it replicate?';$('#noteRelevance').value='5';$('#noteInspiration').value='4';$('#noteForm').dispatchEvent(new window.Event('submit',{bubbles:true,cancelable:true}));await tick();
 closeDB();const persisted=(await allNotes())[0];assert.equal(persisted.annotations,'PRIVATE_CLINICAL_NOTE');assert.equal(persisted.profiles.clinical.relevance,5);assert.equal(persisted.profiles.basic,undefined);
 window.location.hash='basic';await tick();assert.equal($('#search').value,'periostin');
 window.location.hash='library';await tick();assert.ok($('#libraryCards').textContent.includes('PRIVATE_CLINICAL_NOTE'));assert.ok($('#libraryCards').textContent.includes('does it replicate?'));
 window.location.hash='weekly';await tick();$('#weeklyRadar').value='clinical';$('#weekStart').value='2026-01-01';$('#weekEnd').value='2099-12-31';$('#weeklyForm').dispatchEvent(new window.Event('submit',{cancelable:true}));await tick();assert.ok($('#weeklyOutput').textContent.includes(persisted.doi));assert.ok($('#weeklyOutput').textContent.includes('test local hypothesis'));
 window.location.hash='settings';await tick();const before=(await allNotes())[0].annotations;
 const backup={format:'research-radar-personal',version:2,notes:[{...persisted,annotations:'RESTORED_NOTE'}],preferences:await allPreferences()};Object.defineProperty($('#restoreFile'),'files',{configurable:true,value:[{size:1000,text:async()=>JSON.stringify(backup)}]});$('#restoreFile').dispatchEvent(new window.Event('change'));await tick();assert.equal((await allNotes())[0].annotations,before);assert.ok($('#restorePreview').textContent.includes('覆盖1条'));$('#restoreConfirm').click();await tick();assert.equal((await allNotes())[0].annotations,'RESTORED_NOTE');
 assert.ok(requested.every(url=>!url.includes('PRIVATE')&&!url.includes('backup')));closeDB();dom.window.close();
});
