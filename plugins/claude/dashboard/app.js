'use strict';
const $ = id => document.getElementById(id);
const icons = {
  orchestrator:'<circle cx="12" cy="5" r="3"/><circle cx="5" cy="19" r="3"/><circle cx="19" cy="19" r="3"/><path d="M12 8v4M5 16v-4h14v4"/>',
  'spec-writer':'<path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6"/>',
  builder:'<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-14-2 16"/>',
  verifier:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  'code-reviewer':'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',
  'security-reviewer':'<path d="m12 2 8 4v6c0 6-8 10-8 10S4 18 4 12V6z"/>',
  'ui-reviewer':'<rect x="2" y="3" width="20" height="14" rx="1"/><path d="M8 22h8m-4-5v5"/>',
  'ux-reviewer':'<circle cx="6" cy="4" r="2"/><circle cx="18" cy="8" r="2"/><circle cx="6" cy="20" r="2"/><path d="M6 6v12m0-4c8 0 12 0 12-4"/>',
  'readiness-reviewer':'<path d="M5 22V3c5-4 9 4 15 0v11c-6 4-10-4-15 0"/>',
  git:'<circle cx="6" cy="4" r="2"/><circle cx="6" cy="20" r="2"/><circle cx="18" cy="4" r="2"/><path d="M6 6v12m12-12v4c0 4-12 0-12 6"/>'
};
function icon(name){return '<svg viewBox="0 0 24 24" aria-hidden="true">'+icons[name]+'</svg>';}
const names={orchestrator:'Engineering Lead','spec-writer':'Product Planner',builder:'Software Engineer',verifier:'QA Engineer','code-reviewer':'Code Reviewer','security-reviewer':'Security Engineer','ui-reviewer':'Visual Designer','ux-reviewer':'UX Reviewer','readiness-reviewer':'Release Reviewer'};
const labels={working:'Working now',idle:'Waiting',returned:'Finished task',stale:'No recent signal',ended:'Session ended',interrupted:'Interrupted',attention:'Needs attention',queued:'Up next',not_required:'Not needed'};
const resultLabels={passed:'Passed',failed:'Failed',not_verified:'Not verified',blocked:'Blocked',note:'Note'};
let data=null, selected='orchestrator', tab='activity', online=false, pending=false, requestError='';
const cards={};
function make(tag,className,content){const node=document.createElement(tag);if(className)node.className=className;if(content!==undefined)node.textContent=content;return node;}
Object.entries(names).forEach(([role,name])=>{
  const card=make('button','agent');card.type='button';card.setAttribute('aria-pressed',String(role===selected));card.setAttribute('aria-controls','details');
  const mark=make('span','agent-icon');mark.innerHTML=icon(role);card.append(mark,make('span','agent-name',name),make('span','state','Waiting'),make('span','agent-summary',''),make('span','agent-action',''));
  card.hidden=role!=='orchestrator';
  card.addEventListener('click',()=>{selected=role;$('details').hidden=false;document.querySelector('main').classList.remove('details-closed');updateSelection();renderPanel();if(window.matchMedia('(max-width:850px)').matches){$('detail-name').focus({preventScroll:true});$('details').scrollIntoView({block:'start',behavior:'instant'});}});
  $(role==='orchestrator'?'coordinator':'specialists').append(card);cards[role]=card;
});
$('git-icon').innerHTML=icon('git');
function status(agent){return !online&&agent.status==='working'?'stale':agent.status;}
function task(agent){
  if(agent?.report.summary&&!agent.report_stale)return agent.report.summary;
  return agent?.role==='orchestrator'?'Coordinates your request and the specialist team.':agent?.status==='returned'?'Task finished. Open Checks for reported results.':agent?.status==='working'?'Task details have not been reported yet.':'No current task reported.';
}
function action(agent){
  const a=agent?.activity;if(!a)return '';
  const age=Math.max(0,Math.floor(Date.now()/1000-a.time));
  return a.summary+(a.file?' · '+a.file:'')+' · '+(age<60?'just now':Math.floor(age/60)+' min ago');
}
// Geometry comes from the rendered buttons; no graph dependency or fake workers.
const svgNS='http://www.w3.org/2000/svg', links=new Map(), seenHandoffs=new Set();
const reducedMotion=window.matchMedia('(prefers-reduced-motion:reduce)');
let mapSession=null, frame=0;
function svg(tag,attrs){const node=document.createElementNS(svgNS,tag);Object.entries(attrs).forEach(([key,value])=>node.setAttribute(key,value));return node;}
function cancelPulses(){document.querySelectorAll('.handoff-pulse').forEach(node=>{node.getAnimations().forEach(a=>a.cancel());node.remove();});}
function drawConnections(){
  frame=0;if(!data)return;
  const map=$('team-map').getBoundingClientRect(), hub=cards.orchestrator.getBoundingClientRect();
  $('connections').setAttribute('viewBox',`0 0 ${map.width} ${map.height}`);
  const visible=new Set();
  data.agents.filter(a=>a.role!=='orchestrator'&&a.invoked&&!cards[a.role].hidden).forEach(agent=>{
    visible.add(agent.role);let link=links.get(agent.role);
    if(!link){const path=svg('path',{'class':'connection','data-role':agent.role,'fill':'none'});$('connections').append(path);link={path,d:'',reverse:''};links.set(agent.role,link);}
    const node=cards[agent.role].getBoundingClientRect();
    const x1=hub.left+hub.width/2-map.left,y1=hub.bottom-map.top;
    const x2=node.left+node.width/2-map.left,y2=node.top-map.top;
    const middle=y1+(y2-y1)*.55;
    link.d=`M ${x1} ${y1} C ${x1} ${middle}, ${x2} ${middle}, ${x2} ${y2}`;
    link.reverse=`M ${x2} ${y2} C ${x2} ${middle}, ${x1} ${middle}, ${x1} ${y1}`;
    if(window.matchMedia('(max-width:540px)').matches){
      const hx=hub.left-map.left,hy=hub.top+hub.height/2-map.top,nx=node.left-map.left,ny=node.top+node.height/2-map.top;
      link.d=`M ${hx} ${hy} C 4 ${hy}, 4 ${ny}, ${nx} ${ny}`;
      link.reverse=`M ${nx} ${ny} C 4 ${ny}, 4 ${hy}, ${hx} ${hy}`;
    }
    link.path.setAttribute('d',link.d);link.path.setAttribute('class','connection '+status(agent));
  });
  links.forEach((link,role)=>{if(!visible.has(role)){link.path.remove();links.delete(role);}});
}
function scheduleConnections(){if(!frame)frame=requestAnimationFrame(drawConnections);}
function pulse(role,direction){
  const link=links.get(role);if(!link||reducedMotion.matches||document.hidden||!online)return;
  const path=svg('path',{'class':'handoff-pulse','data-direction':direction,'d':direction==='return'?link.reverse:link.d,'fill':'none'});
  $('connections').append(path);
  const length=path.getTotalLength();path.setAttribute('stroke-dasharray',`10 ${length+10}`);
  const animation=path.animate([{strokeDashoffset:0},{strokeDashoffset:-length}],{duration:1000,easing:'linear',iterations:1});
  animation.onfinish=()=>path.remove();animation.oncancel=()=>path.remove();
}
function renderHandoffs(){
  const session=data.session?.id||null, first=mapSession!==session;
  if(first){mapSession=session;seenHandoffs.clear();cancelPulses();}
  const events=data.events.filter(e=>e.kind==='SubagentStart'||e.kind==='SubagentStop');
  const latest=events[0];
  $('handoff-status').textContent=latest?'Last handoff: '+(latest.kind==='SubagentStart'?names.orchestrator+' → '+names[latest.role]:names[latest.role]+' → '+names.orchestrator)+' · '+(latest.kind==='SubagentStart'?'Task started':'Task returned; checks stay separate'):'Connections appear when agents are invoked.';
  const now=Date.now()/1000;
  events.slice().reverse().forEach(event=>{
    const key=[session,event.role,event.kind,event.time].join(':');
    if(!seenHandoffs.has(key)&&!first&&online&&data.session?.state!=='ended'&&now-event.time>=0&&now-event.time<12){
      pulse(event.role,event.kind==='SubagentStart'?'assign':'return');
    }
    seenHandoffs.add(key);
  });
  // Retain only the bounded snapshot window; no replay on unchanged polls.
  if(seenHandoffs.size>300){seenHandoffs.clear();events.forEach(e=>seenHandoffs.add([session,e.role,e.kind,e.time].join(':')));}
  if(!online||data.session?.state==='ended')cancelPulses();
}
new ResizeObserver(scheduleConnections).observe($('team-map'));
new ResizeObserver(scheduleConnections).observe(cards.orchestrator);
window.addEventListener('resize',scheduleConnections);
reducedMotion.addEventListener('change',()=>{if(reducedMotion.matches)cancelPulses();});
document.addEventListener('visibilitychange',()=>{if(document.hidden)cancelPulses();});
function updateSelection(){
  Object.entries(cards).forEach(([role,card])=>card.setAttribute('aria-pressed',String(role===selected)));
  const agent=data?.agents.find(a=>a.role===selected);
  $('detail-name').textContent=names[selected];$('detail-icon').innerHTML=icon(selected);
  const state=agent?status(agent):'idle';$('detail-status').textContent=(labels[state]||'Unknown')+(agent?.active_count>1?' · '+agent.active_count+' instances':'');$('detail-status').className='state '+state;
  $('detail-task').textContent=task(agent);
  $('detail-provenance').textContent=agent?.report_stale?'Earlier task summary—waiting for a fresh update.':agent?.status==='returned'?'Finished means the agent stopped working—not that all checks passed.':'Task summaries come from Claude. Actions reflect tool activity, not private reasoning.';
}
function renderPanel(){
  const panel=$('panel');panel.replaceChildren();panel.setAttribute('aria-labelledby','tab-'+tab);
  if(!data){panel.append(make('p','empty-state','Waiting for recorded activity.'));return;}
  if(tab==='activity'){
    const events=data.events.filter(e=>e.role===selected&&(e.file||e.source==='coordinator'||e.kind==='PostToolUseFailure'||e.kind==='request'));
    const distinct=events.filter((e,i)=>i===0||e.summary!==events[i-1].summary||e.file!==events[i-1].file);
    if(!distinct.length)panel.append(make('p','empty-state','No detailed updates yet. Claude has not reported a task update or file action for this agent.'));
    distinct.forEach(e=>{const row=make('div','event');const time=make('time','',new Date(e.time*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}));time.dateTime=new Date(e.time*1000).toISOString();const body=make('div','',e.summary);if(e.file)body.append(make('small','',e.file));row.append(time,body);panel.append(row);});
  }else if(tab==='changes'){
    const paths=[...new Set(data.events.filter(e=>e.role===selected&&e.file&&e.kind==='PostToolUse'&&['Edited a file','Wrote a file'].includes(e.summary)).map(e=>e.file))];
    if(!paths.length)panel.append(make('p','empty-state','No file changes attributed to this agent. Attribution is available only when Claude supplies an agent identity for the file event. Use the bottom bar for the full working copy.'));
    paths.forEach(path=>panel.append(make('div','file-row',path)));
  }else{
    const agent=data.agents.find(a=>a.role===selected);const items=[...(agent?.report.findings||[]),...(agent?.report.checks||[])];
    if(agent?.report_stale)panel.append(make('p','notice','This report may be stale. Refresh affected checks before a readiness claim.'));
    if(!items.length)panel.append(make('p','empty-state','No checks reported yet. An agent returning does not mean its tests or review passed.'));
    items.forEach(item=>{const row=make('div','finding',item.title||'Untitled report');row.dataset.result=item.result;row.append(make('small','',(resultLabels[item.result]||'Unknown')+' · Coordinator-reported'));panel.append(row);});
  }
}
const tabs=['activity','changes','checks'];
function setTab(value){tab=value;tabs.forEach(t=>{$('tab-'+t).setAttribute('aria-selected',String(t===tab));$('tab-'+t).tabIndex=t===tab?0:-1;});renderPanel();}
tabs.forEach(t=>{$('tab-'+t).addEventListener('click',()=>setTab(t));$('tab-'+t).addEventListener('keydown',e=>{let index=tabs.indexOf(tab);if(e.key==='ArrowRight')index=(index+1)%3;else if(e.key==='ArrowLeft')index=(index+2)%3;else if(e.key==='Home')index=0;else if(e.key==='End')index=2;else return;e.preventDefault();setTab(tabs[index]);$('tab-'+tab).focus();});});
$('close-details').addEventListener('click',()=>{$('details').hidden=true;document.querySelector('main').classList.add('details-closed');cards[selected].focus();});
$('show-changes').addEventListener('click',()=>{const open=$('all-changes').hidden;$('all-changes').hidden=!open;$('show-changes').setAttribute('aria-expanded',String(open));});
function render(){
  data.agents.forEach(agent=>{const card=cards[agent.role];if(!card)return;const state=status(agent);card.hidden=agent.role!=='orchestrator'&&!agent.participated;card.dataset.state=state;const stateNode=card.querySelector('.state');stateNode.className='state '+state;stateNode.textContent=(labels[state]||'Unknown')+(agent.active_count>1?' · '+agent.active_count+' instances':'');card.querySelector('.agent-summary').textContent=task(agent);card.querySelector('.agent-action').textContent=(state==='working'?'Latest action: ':'Last action: ')+action(agent);card.querySelector('.agent-action').hidden=!agent.activity;card.setAttribute('aria-label',agent.name+': '+stateNode.textContent);});
  const active=data.agents.filter(a=>status(a)==='working');
  if(cards[selected]?.hidden){const hadFocus=document.activeElement===cards[selected];selected='orchestrator';if(hadFocus)cards[selected].focus();}
  const finished=data.agents.filter(a=>a.role!=='orchestrator'&&a.participated&&status(a)!=='working');
  $('team-summary').textContent=(active.length?active.map(a=>a.name).join(' + ')+' working now.':'No agents working right now.')+(finished.length?' '+finished.length+' earlier participant'+(finished.length===1?'':'s')+' shown muted.':'')+' Select an agent for details.';
  $('project').textContent=data.agents.find(a=>a.role==='orchestrator')?.report.summary||data.project;
  $('empty').hidden=Boolean(data.session);$('offline').hidden=online;
  const age=data.session?Math.max(0,Math.floor((Date.now()/1000-data.session.seen)/60)):null;
  const fresh=online&&data.session&&age<data.stale_after/60&&data.session.state!=='ended';
  $('connection').dataset.fresh=String(Boolean(fresh));$('connection').textContent=!online?'Offline':!data.session?'No session yet':data.session.state==='ended'?'Session ended':fresh?'Receiving activity':'No recent signal';
  $('session-note').textContent=age===null?'Waiting for Claude':age<1?'Last signal just now':'Last signal '+age+' min ago';
  const git=data.git;$('change-count').textContent=git.available?git.visible_count+' local change'+(git.visible_count===1?'':'s'):'Local changes unavailable';
  $('commit-count').textContent=git.ahead===null?'Unpushed commits unknown':git.ahead+' commit'+(git.ahead===1?'':'s')+' ahead of cached upstream';
  $('git-note').textContent=git.note;$('all-changes').replaceChildren(make('h2','','Local working copy'));
  if(!git.files.length)$('all-changes').append(make('p','empty-state',git.available?'No visible working-copy changes. This does not prove the branch is pushed.':'Git status unavailable.'));
  git.files.forEach(file=>{const row=make('div','file-row',file.path);row.append(make('span','',file.status+' · '+(file.staged?'Staged':'Not staged')));$('all-changes').append(row);});
  if(git.hidden_count)$('all-changes').append(make('p','quiet','Credential, hidden, or generated paths omitted: '+git.hidden_count));
  if(git.truncated)$('all-changes').append(make('p','quiet','Showing the first 100 paths.'));
  const queued=data.requests.filter(r=>r.state==='queued');
  $('submit').disabled=!online||pending||queued.some(r=>r.action==='submit');$('request-publish').disabled=!online||pending||queued.some(r=>r.action==='request-publish');
  if(requestError){$('request-notice').hidden=false;$('request-notice').textContent=requestError;}
  else if(queued.length){$('request-notice').hidden=false;$('request-notice').textContent='Request queued. Return to Claude and send “Continue” to start '+queued.map(r=>r.action==='submit'?'Submit changes':'Request publish').join(' and ')+'. No Git or publishing action has run.';}
  else if(data.requests.length){$('request-notice').hidden=false;$('request-notice').textContent='Latest request delivered to Claude. Delivery is not execution or approval; check Claude for the outcome.';}
  updateSelection();renderPanel();drawConnections();renderHandoffs();
}
async function refresh(){
  try{const response=await fetch('api/state',{cache:'no-store'});if(!response.ok)throw Error();data=await response.json();online=true;render();}
  catch{online=false;$('offline').hidden=false;$('connection').textContent='Offline';$('connection').dataset.fresh='false';$('submit').disabled=true;$('request-publish').disabled=true;if(data)render();}
}
async function request(action){
  pending=true;$('submit').disabled=true;$('request-publish').disabled=true;
  try{const response=await fetch('api/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});if(!response.ok)throw Error();requestError='';await refresh();}
  catch{requestError='Could not queue the request. Nothing was executed. Ask Claude to run '+(action==='submit'?'/abacus-studio:submit':'/abacus-studio:request-publish')+' instead.';$('request-notice').hidden=false;$('request-notice').textContent=requestError;}
  finally{pending=false;if(data){const queued=data.requests.filter(r=>r.state==='queued');$('submit').disabled=!online||queued.some(r=>r.action==='submit');$('request-publish').disabled=!online||queued.some(r=>r.action==='request-publish');}}
}
$('submit').addEventListener('click',()=>request('submit'));$('request-publish').addEventListener('click',()=>request('request-publish'));
updateSelection();refresh();setInterval(refresh,3000);
