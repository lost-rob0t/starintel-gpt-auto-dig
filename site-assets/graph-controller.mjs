import { URL_KEYS, clamp, edgeKey, findPaths } from "./graph-core.mjs";
import { GraphModel } from "./graph-model.mjs";
import { GraphRenderer } from "./graph-render.mjs";
import { buildUI, populateNodeOptions, renderLegend, renderDetail, renderPaths } from "./graph-ui.mjs";

export async function mount(canvasId, detailId, url) {
  const canvas = document.getElementById(canvasId), detail = document.getElementById(detailId);
  if (!canvas || !detail) return;
  const search = document.getElementById("graph-search"), filter = document.getElementById("graph-filter"), reset = document.getElementById("graph-reset");
  if (reset) { reset.textContent = "Fit"; reset.title = "Fit visible nodes"; }
  const response = await fetch(url); if (!response.ok) { detail.textContent = `Graph load failed: ${response.status}`; return; }
  const model = new GraphModel(await response.json()), renderer = new GraphRenderer(canvas, model), ui = buildUI(canvas, detail);
  const state = {
    scale: 1, pan: {x:0,y:0}, drag: null, hover: null, primary: null, selected: new Set(),
    focusIds: null, focusDepth: 1, edgeLabels: false, pathStart: null, pathEnd: null,
    paths: [], activePath: -1, pathNodes: new Set(), pathEdges: new Set(), restoring: false, urlTimer: null
  };
  let frame = null;

  const incident = (node) => model.edges.filter((edge) => edge.a === node || edge.b === node);
  const view = () => ({ scale: state.scale, pan: state.pan, hover: state.hover, primary: state.primary, selected: state.selected, pathNodes: state.pathNodes, pathEdges: state.pathEdges, edgeLabels: state.edgeLabels });
  const point = (event) => { const rect = canvas.getBoundingClientRect(); return {x:event.clientX-rect.left,y:event.clientY-rect.top}; };
  const resolve = (value) => {
    const text = String(value || "").trim(); if (!text) return null; if (model.nodeMap.has(text)) return text;
    const found = model.nodes.filter((node) => (node.label || "").toLowerCase() === text.toLowerCase()); return found.length === 1 ? found[0].id : null;
  };
  const updateVisibility = (relayout=true) => {
    model.updateVisibility({ query: search?.value || "", group: filter?.value || "", focusIds: state.focusIds, pathIds: state.pathNodes });
    state.selected = new Set([...state.selected].filter((node) => node.visible));
    if (state.primary && !state.primary.visible && !state.pathNodes.has(state.primary.id)) state.primary = null;
    if (relayout) model.applyLayout(model.layout, state.primary, false);
    renderLegend(ui, model.nodes); renderDetail(ui, state.primary, state, incident); scheduleURL();
  };
  const select = (node, additive=false) => {
    if (!node) { if (!additive) { state.selected.clear(); state.primary = null; } }
    else if (additive) { state.selected.has(node) ? state.selected.delete(node) : state.selected.add(node); state.primary = state.selected.has(node) ? node : [...state.selected].at(-1) || null; }
    else { state.selected = new Set([node]); state.primary = node; }
    renderDetail(ui, state.primary, state, incident); scheduleURL();
  };
  const focus = (depth=1) => { if (!state.primary) return; state.focusDepth = depth; state.focusIds = model.neighborhood(state.primary, depth); updateVisibility(); fit(model.visibleNodes(), true); };
  const showAll = () => { state.focusIds = null; state.focusDepth = 1; updateVisibility(); fit(model.visibleNodes(), true); };
  const fit = (nodes, animate=true) => {
    const active = nodes.filter(Boolean); if (!active.length) return;
    let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
    active.forEach((node) => { minX=Math.min(minX,node.x-node.radius-25); minY=Math.min(minY,node.y-node.radius-25); maxX=Math.max(maxX,node.x+node.radius+25); maxY=Math.max(maxY,node.y+node.radius+25); });
    const targetScale = clamp(Math.min((renderer.width-40)/Math.max(1,maxX-minX),(renderer.height-40)/Math.max(1,maxY-minY)),.08,4);
    const targetPan = {x:renderer.width/2-(minX+maxX)/2*targetScale,y:renderer.height/2-(minY+maxY)/2*targetScale};
    if (!animate) { state.scale=targetScale; state.pan=targetPan; scheduleURL(); return; }
    const startScale=state.scale,startPan={...state.pan},started=performance.now();
    const step=(now)=>{ const p=clamp((now-started)/280,0,1),e=1-Math.pow(1-p,3); state.scale=startScale+(targetScale-startScale)*e; state.pan.x=startPan.x+(targetPan.x-startPan.x)*e; state.pan.y=startPan.y+(targetPan.y-startPan.y)*e; if(p<1)requestAnimationFrame(step); else scheduleURL(); }; requestAnimationFrame(step);
  };

  const applyPath = (index, shouldFit=true) => {
    const path = state.paths[index]; state.activePath = path ? index : -1;
    state.pathNodes = new Set(path?.nodes || []); state.pathEdges = new Set((path?.edges || []).map(edgeKey));
    updateVisibility(false); renderPaths(ui,state.paths,state.activePath,model.nodeMap,state.pathStart,state.pathEnd);
    if (path && shouldFit) fit(path.nodes.map((id)=>model.nodeMap.get(id)),true); scheduleURL();
  };
  const calculatePaths = (activate=true) => {
    state.pathStart = resolve(ui.pathStart.value) || state.pathStart; state.pathEnd = resolve(ui.pathEnd.value) || state.pathEnd;
    ui.pathStart.value=state.pathStart || ""; ui.pathEnd.value=state.pathEnd || "";
    state.paths=findPaths(model.nodes,model.edges,state.pathStart,state.pathEnd,5,9); ui.path.open=true;
    if (activate && state.paths.length) applyPath(0,true); else { state.activePath=-1; state.pathNodes.clear(); state.pathEdges.clear(); updateVisibility(false); renderPaths(ui,state.paths,-1,model.nodeMap,state.pathStart,state.pathEnd); }
  };
  const clearPath = () => { state.pathStart=null; state.pathEnd=null; state.paths=[]; state.activePath=-1; state.pathNodes.clear(); state.pathEdges.clear(); ui.pathStart.value=""; ui.pathEnd.value=""; renderPaths(ui,[], -1,model.nodeMap,null,null); updateVisibility(false); };
  const twoSelected = () => { const picks=[...state.selected]; if(picks.length!==2){ui.path.open=true;ui.pathResults.innerHTML='<p class="graph-path-empty">Select exactly two nodes with Shift-click first.</p>';return;} state.pathStart=picks[0].id;state.pathEnd=picks[1].id;ui.pathStart.value=state.pathStart;ui.pathEnd.value=state.pathEnd;calculatePaths(true); };

  const serialize = () => {
    const next=new URL(location.href); URL_KEYS.forEach((key)=>next.searchParams.delete(key));
    if(model.layout!=="force")next.searchParams.set("layout",model.layout); if(filter?.value)next.searchParams.set("type",filter.value); if(search?.value.trim())next.searchParams.set("q",search.value.trim()); if(state.edgeLabels)next.searchParams.set("relations","1");
    if(state.primary)next.searchParams.set("node",state.primary.id); if(state.focusIds&&state.primary){next.searchParams.set("focus",state.primary.id);next.searchParams.set("depth",String(state.focusDepth));}
    if(state.pathStart)next.searchParams.set("from",state.pathStart);if(state.pathEnd)next.searchParams.set("to",state.pathEnd);if(state.activePath>=0)next.searchParams.set("route",String(state.activePath));
    next.searchParams.set("scale",state.scale.toFixed(4));next.searchParams.set("panx",state.pan.x.toFixed(1));next.searchParams.set("pany",state.pan.y.toFixed(1));return next;
  };
  const syncURL=()=>{if(state.restoring)return;const next=serialize();history.replaceState(null,"",`${next.pathname}${next.search}${next.hash}`);};
  function scheduleURL(){if(state.restoring)return;clearTimeout(state.urlTimer);state.urlTimer=setTimeout(syncURL,140);}
  const restore=()=>{
    state.restoring=true;const params=new URLSearchParams(location.search),layout=params.get("layout")||"force";model.layout=["force","hierarchical","radial","concentric","grid"].includes(layout)?layout:"force";ui.layout.value=model.layout;
    if(filter)filter.value=params.get("type")||"";if(search)search.value=params.get("q")||"";state.edgeLabels=params.get("relations")==="1";ui.labels.checked=state.edgeLabels;
    state.primary=model.nodeMap.get(params.get("node"))||null;state.selected=state.primary?new Set([state.primary]):new Set();const focusNode=model.nodeMap.get(params.get("focus"));state.focusDepth=clamp(Number(params.get("depth"))||1,1,2);state.focusIds=focusNode?model.neighborhood(focusNode,state.focusDepth):null;if(focusNode&&!state.primary){state.primary=focusNode;state.selected=new Set([focusNode]);}
    state.pathStart=model.nodeMap.has(params.get("from"))?params.get("from"):null;state.pathEnd=model.nodeMap.has(params.get("to"))?params.get("to"):null;ui.pathStart.value=state.pathStart||"";ui.pathEnd.value=state.pathEnd||"";
    state.paths=state.pathStart&&state.pathEnd?findPaths(model.nodes,model.edges,state.pathStart,state.pathEnd,5,9):[];state.activePath=state.paths.length?clamp(Number(params.get("route"))||0,0,state.paths.length-1):-1;const route=state.paths[state.activePath];state.pathNodes=new Set(route?.nodes||[]);state.pathEdges=new Set((route?.edges||[]).map(edgeKey));if(route)ui.path.open=true;
    const s=Number(params.get("scale")),x=Number(params.get("panx")),y=Number(params.get("pany"));if(Number.isFinite(s))state.scale=clamp(s,.08,5);if(Number.isFinite(x))state.pan.x=x;if(Number.isFinite(y))state.pan.y=y;
    updateVisibility(false);model.applyLayout(model.layout,state.primary,model.layout!=="force");renderPaths(ui,state.paths,state.activePath,model.nodeMap,state.pathStart,state.pathEnd);renderDetail(ui,state.primary,state,incident);state.restoring=false;
  };
  const copyLink=async(pathOnly=false)=>{syncURL();try{await navigator.clipboard.writeText(location.href);}catch(_){const input=document.createElement("input");input.value=location.href;document.body.appendChild(input);input.select();document.execCommand("copy");input.remove();}ui.status.textContent=pathOnly?"Path copied":"Copied";setTimeout(()=>ui.status.textContent="",1800);};

  renderer.resize(); populateNodeOptions(ui,model.nodes); [...new Set(model.nodes.map((node)=>node.group||"entity"))].sort().forEach((group)=>{if(filter&&![...filter.options].some((option)=>option.value===group)){const option=document.createElement("option");option.value=group;option.textContent=group.replaceAll("-"," ");filter.appendChild(option);}});
  restore(); if(!new URLSearchParams(location.search).has("scale"))requestAnimationFrame(()=>fit(model.visibleNodes(),false));

  canvas.addEventListener("pointerdown",(event)=>{const p=point(event),node=renderer.nearest(p,view());canvas.setPointerCapture(event.pointerId);if(node){select(node,event.shiftKey);state.drag={node,last:p};node.vx=node.vy=0;model.reheat(.55);}else{if(!event.shiftKey)select(null,false);state.drag={pan:true,last:p};}});
  canvas.addEventListener("pointermove",(event)=>{const p=point(event);state.hover=renderer.nearest(p,view());canvas.style.cursor=state.hover?"pointer":state.drag?"grabbing":"grab";if(!state.drag)return;if(state.drag.pan){state.pan.x+=p.x-state.drag.last.x;state.pan.y+=p.y-state.drag.last.y;state.drag.last=p;scheduleURL();}else{const world=renderer.world(p,view()),node=state.drag.node;node.x=world.x;node.y=world.y;node.vx=node.vy=0;if(model.layout!=="force"){node.tx=world.x;node.ty=world.y;}model.reheat(.35);}});
  canvas.addEventListener("pointerup",(event)=>{if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);state.drag=null;scheduleURL();});canvas.addEventListener("pointercancel",()=>state.drag=null);canvas.addEventListener("pointerleave",()=>{if(!state.drag)state.hover=null;});
  canvas.addEventListener("dblclick",(event)=>{const node=renderer.nearest(point(event),view());if(node?.href)location.href=node.href;});canvas.addEventListener("contextmenu",(event)=>{event.preventDefault();const node=renderer.nearest(point(event),view());if(node){select(node,false);focus(1);}});
  canvas.addEventListener("wheel",(event)=>{event.preventDefault();const p=point(event),old=state.scale;state.scale=clamp(state.scale*(event.deltaY<0?1.13:.885),.08,5);state.pan.x=p.x-(p.x-state.pan.x)*(state.scale/old);state.pan.y=p.y-(p.y-state.pan.y)*(state.scale/old);scheduleURL();},{passive:false});
  search?.addEventListener("input",()=>updateVisibility());filter?.addEventListener("input",()=>updateVisibility());reset?.addEventListener("click",()=>fit(model.visibleNodes(),true));
  ui.layout.addEventListener("change",()=>{model.applyLayout(ui.layout.value,state.primary,ui.layout.value!=="force");requestAnimationFrame(()=>fit(model.visibleNodes(),true));});ui.labels.addEventListener("change",()=>{state.edgeLabels=ui.labels.checked;scheduleURL();});ui.focus.addEventListener("click",()=>focus(1));ui.all.addEventListener("click",showAll);ui.share.addEventListener("click",()=>copyLink(false));
  ui.legend.addEventListener("click",(event)=>{const button=event.target.closest("[data-group]");if(!button||!filter)return;filter.value=filter.value===button.dataset.group?"":button.dataset.group;updateVisibility();fit(model.visibleNodes(),true);});
  ui.detail.addEventListener("click",(event)=>{const nodeButton=event.target.closest("[data-node-id]");if(nodeButton){const node=model.nodeMap.get(nodeButton.dataset.nodeId);if(node){select(node,false);const p=renderer.screen(node,view());state.pan.x+=renderer.width/2-p.x;state.pan.y+=renderer.height/2-p.y;scheduleURL();}return;}const action=event.target.closest("[data-action]")?.dataset.action;if(action==="focus-1")focus(1);if(action==="focus-2")focus(2);if(action==="show-all")showAll();if(action==="path-start"&&state.primary){state.pathStart=state.primary.id;ui.pathStart.value=state.pathStart;ui.path.open=true;state.pathEnd?calculatePaths(true):renderPaths(ui,[], -1,model.nodeMap,state.pathStart,state.pathEnd);renderDetail(ui,state.primary,state,incident);}if(action==="path-end"&&state.primary){state.pathEnd=state.primary.id;ui.pathEnd.value=state.pathEnd;ui.path.open=true;state.pathStart?calculatePaths(true):renderPaths(ui,[], -1,model.nodeMap,state.pathStart,state.pathEnd);renderDetail(ui,state.primary,state,incident);}if(action==="pin"&&state.primary){state.primary.pinned=!state.primary.pinned;state.primary.vx=state.primary.vy=0;renderDetail(ui,state.primary,state,incident);}});
  ui.path.addEventListener("click",(event)=>{const route=event.target.closest("[data-path-index]");if(route){applyPath(Number(route.dataset.pathIndex),true);return;}const action=event.target.closest("[data-path-action]")?.dataset.pathAction;if(action==="selected")twoSelected();if(action==="find")calculatePaths(true);if(action==="clear")clearPath();if(action==="copy")copyLink(true);});
  ui.pathStart.addEventListener("change",()=>{state.pathStart=resolve(ui.pathStart.value);scheduleURL();});ui.pathEnd.addEventListener("change",()=>{state.pathEnd=resolve(ui.pathEnd.value);scheduleURL();});
  window.addEventListener("resize",()=>{renderer.resize();model.reheat(.3);scheduleURL();});window.addEventListener("popstate",restore);window.addEventListener("keydown",(event)=>{if(event.key==="Escape")showAll();if(event.key.toLowerCase()==="f"&&!/input|select|textarea/i.test(document.activeElement?.tagName||""))fit(model.visibleNodes(),true);});
  const loop=()=>{model.simulate(state.drag?.node||null);renderer.draw(view());frame=requestAnimationFrame(loop);};if(frame)cancelAnimationFrame(frame);loop();renderLegend(ui,model.nodes);renderDetail(ui,state.primary,state,incident);renderPaths(ui,state.paths,state.activePath,model.nodeMap,state.pathStart,state.pathEnd);
}
