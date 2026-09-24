const $=s=>document.querySelector(s);
let comfyReady=false,workflows=[],activeConversationId=null,imageData=null;
let conversations=loadJSON("lva_conversations_v2",{}),library=loadJSON("lva_library",[]);
let modalSelection={image:null,video:null};\nlet modalStep=1;

const kinds={image:["Image","🖼️"],retouch:["Retouche","✨"],video:["Vidéo","🎬"],"video-heavy":["Vidéo lourd","🎞️"]};

function loadJSON(k,f){try{return JSON.parse(localStorage.getItem(k))||f}catch{return f}}
function save(){localStorage.setItem("lva_conversations_v2",JSON.stringify(conversations));localStorage.setItem("lva_library",JSON.stringify(library))}
function toast(t){const e=$("#toast");e.textContent=t;e.classList.add("show");setTimeout(()=>e.classList.remove("show"),2300)}
async function api(url,opt){const r=await fetch(url,opt);const d=await r.json();if(!r.ok||d.error)throw new Error(d.error||"Erreur");return d}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}

function modelKind(w){return w?.kind==="video-heavy"?"video":w?.kind||"image"}
function modelsFor(task){return workflows.filter(w=>task==="image"?w.kind==="image":task==="retouch"?w.kind==="retouch":w.kind==="video"||w.kind==="video-heavy")}
function titleForConversation(c){return c?.title||"Nouvelle conversation"}
function conversationFor(id){if(!conversations[id])conversations[id]={id,title:"Nouvelle conversation",createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),settings:{image:null,retouch:null,video:null},messages:[]};return conversations[id]}

function renderConversationList(filter=""){
 const box=$("#conversationsList");box.innerHTML="";
 const rows=Object.values(conversations).sort((a,b)=>new Date(b.updatedAt)-new Date(a.updatedAt)).filter(c=>titleForConversation(c).toLowerCase().includes(filter.toLowerCase()));
 if(!rows.length){box.innerHTML='<div class="empty-conversations">Aucune conversation</div>';return}
 rows.forEach(c=>{
   const b=document.createElement("button");b.className="conversation-item"+(activeConversationId===c.id?" active":"");
   const ready=!!(c.settings?.image||c.settings?.retouch||c.settings?.video);
   const kindsUsed=[c.settings?.image,c.settings?.video].filter(Boolean).length;
   b.innerHTML='<span class="conversation-icon">◌</span><span class="conversation-main"><span class="conversation-title">'+esc(titleForConversation(c))+'</span><span class="conversation-meta">'+kindsUsed+' modèle'+(kindsUsed>1?"s":"")+' sélectionné'+(kindsUsed>1?"s":"")+'</span></span><i class="conversation-dot '+(ready?"ready":"")+'"></i>';
   b.onclick=()=>openConversation(c.id);box.appendChild(b);
 });
}

function renderLibraryCounts(){const p=library.filter(x=>x.kind==="image").length,v=library.filter(x=>x.kind==="video").length,r=library.filter(x=>x.kind==="retouch").length;$("#photoCount").textContent=p||"";$("#videoCount").textContent=v||"";$("#retouchCount").textContent=r||""}

function openConversation(id){
 activeConversationId=id;const c=conversationFor(id);renderConversationList($("#conversationSearch").value);
 $("#welcome").classList.toggle("hidden",c.messages.length>0);
 const box=$("#messages");box.innerHTML="";
 c.messages.forEach(renderMessage);scrollBottom();
 hideSidebar();
}

function renderMessage(m){
 const wrap=document.createElement("div");wrap.className="message "+(m.role==="user"?"user":"assistant");
 if(m.text){const b=document.createElement("div");b.className="bubble";b.textContent=m.text;wrap.appendChild(b)}
 if(m.loading){
   const label=document.createElement("div");label.className="generation-label";label.textContent=m.mediaType==="video"?"Génération de la vidéo…":m.mediaType==="retouch"?"Génération de la retouche…":"Génération de la photo…";wrap.appendChild(label);
   const f=document.createElement("div");f.className="generation-frame loading";f.dataset.loading="1";f.innerHTML='<div class="loader"></div>';wrap.appendChild(f);
 }
 if(m.result){
   const f=document.createElement("div");f.className="generation-frame";const src=resultUrl(m.result);const video=/\.(mp4|webm|mov|mkv)$/i.test(m.result.filename||"");
   f.innerHTML=video?'<video class="result-media" controls src="'+src+'"></video>':'<img class="result-media" src="'+src+'">';wrap.appendChild(f);
 }
 $("#messages").appendChild(wrap);return wrap;
}
function resultUrl(x){return "/api/view?filename="+encodeURIComponent(x.filename||"")+"&subfolder="+encodeURIComponent(x.subfolder||"")+"&type="+encodeURIComponent(x.type||"output")}
function scrollBottom(){requestAnimationFrame(()=>{$("#chat").scrollTop=$("#chat").scrollHeight})}

function addMessage(id,m){const c=conversationFor(id);c.messages.push(m);c.updatedAt=new Date().toISOString();c.title=c.title==="Nouvelle conversation"&&m.role==="user"?m.text.slice(0,48)+(m.text.length>48?"…":""):c.title;save();renderConversationList($("#conversationSearch").value);$("#welcome").classList.add("hidden");renderMessage(m);scrollBottom()}
function removeLoading(id){const c=conversationFor(id);c.messages=c.messages.filter(m=>!m.loading);c.updatedAt=new Date().toISOString();save();$("#messages").querySelectorAll(".generation-frame[data-loading='1']").forEach(x=>x.parentElement.remove());}

function resultKindForModel(model){return model?.kind==="video"||model?.kind==="video-heavy"?"video":"image"}
function selectedModelForConversation(c,task){const id=c.settings?.[task];return workflows.find(w=>w.id===id)||null}

function renderOptions(task,filter=""){
 const box=$("#"+task+"Options");box.innerHTML="";
 const rows=modelsFor(task).filter(w=>w.name.toLowerCase().includes(filter.toLowerCase()));
 if(!rows.length){box.innerHTML='<div class="no-model">Aucun modèle compatible trouvé.</div>';return}
 rows.forEach(w=>{
   const selected=modalSelection[task]===w.id;
   const b=document.createElement("button");b.className="model-option"+(selected?" selected":"");
   const label=kinds[w.kind]?.[0]||task;
   b.innerHTML='<span class="option-icon">'+(w.icon||"◌")+'</span><span><b>'+esc(w.name)+'</b><small>'+label+(comfyReady?" · prêt":" · moteur indisponible")+'</small></span>';
   b.onclick=()=>{modalSelection[task]=w.id;renderOptions(task,$('[data-search="'+task+'"]').value)};
   box.appendChild(b);
 });
}
function setModalStep(step){
 modalStep=step;
 $("#imageStep").classList.toggle("hidden",step!==1);
 $("#videoStep").classList.toggle("hidden",step!==2);
 $("#modalTitle").textContent=step===1?"Avec quel modèle générer ton image":"Avec quel modèle générer ta vidéo";
 $("#modalSubtitle").textContent=step===1?"Choisis le modèle photo qui sera utilisé dans cette conversation.":"Choisis le modèle vidéo qui sera utilisé dans cette conversation.";
 $("#stepProgress").textContent=step+"/2";
 $("#stepValidate").textContent=step===1?"Valider":"Créer la conversation";
 $("#modalError").textContent="";
 if(step===1)renderOptions("image");else renderOptions("video");
}
function openModelModal(){
 modalSelection={image:null,video:null};setModalStep(1);
 $("#modelModal").classList.remove("hidden");
}
function closeModelModal(){$("#modelModal").classList.add("hidden")}
function createConversation(){
 const c={id:crypto.randomUUID(),title:"Nouvelle conversation",createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),settings:{image:modalSelection.image,retouch:null,video:modalSelection.video},messages:[]};
 conversations[c.id]=c;activeConversationId=c.id;save();renderConversationList();closeModelModal();openConversation(c.id);
 toast("Conversation créée.");
}
function advanceModelStep(){
 if(modalStep===1){
   if(!modalSelection.image){$("#modalError").textContent="Sélectionne un modèle photo avant de continuer.";return}
   setModalStep(2);return;
 }
 if(!modalSelection.video){$("#modalError").textContent="Sélectionne un modèle vidéo avant de créer la conversation.";return}
 createConversation();
}
function renderLibrary(kind,title){
 $("#welcome").classList.add("hidden");$("#messages").innerHTML="";
 const box=document.createElement("div");box.className="library-view";
 box.innerHTML='<button class="library-back" id="libraryBack">← Retour à la conversation</button><h2>'+esc(title)+'</h2><div class="library-grid"></div>';
 $("#messages").appendChild(box);const grid=box.querySelector(".library-grid");const rows=library.filter(x=>x.kind===kind);
 if(!rows.length){grid.innerHTML='<div class="empty-library">Aucune création enregistrée ici.</div>';return}
 rows.forEach(x=>{const c=document.createElement("div");c.className="library-card";const src=resultUrl(x);const video=/\.(mp4|webm|mov|mkv)$/i.test(x.filename||"");c.innerHTML=(video?'<video controls src="'+src+'"></video>':'<img src="'+src+'">')+'<div class="meta">'+esc(x.prompt||"Création")+'</div>';grid.appendChild(c)});
 $("#libraryBack").onclick=()=>activeConversationId?openConversation(activeConversationId):openModelModal();
}

function addLibrary(result,kind,prompt){library.unshift({...result,kind,prompt,createdAt:new Date().toISOString()});save();renderLibraryCounts()}

/*
  Le chat et la génération sont volontairement séparés :
  - un message normal ne déclenche jamais /api/generate ;
  - une génération n'est envoyée à ComfyUI que si l'utilisateur formule explicitement
    une demande de création (ex. "génère une image", "crée une vidéo", "retouche cette photo").
  Le futur moteur conversationnel pourra remplacer explicitGenerationRequest() et
  appeler le même startGeneration() après avoir compris l'intention.
*/
function explicitGenerationRequest(text){
 const t=text.toLowerCase();
 const asks=t.match(/\b(génère|genere|générer|generer|crée|cree|créer|creer|produis|produire|fais|faire|fabrique|fabriquer|retouche|retoucher)\b/);
 if(!asks)return null;
 if(/\b(video|vidéo|animation|animer|film)\b/.test(t))return "video";
 if(/\b(retouche|retoucher|modifier|modifie|corrige|corriger)\b/.test(t))return "retouch";
 if(/\b(photo|image|portrait|illustration|visuel|dessin)\b/.test(t))return "image";
 return null;
}

async function sendMessage(){
 const text=$("#prompt").value.trim();if(!text)return;
 if(!activeConversationId){openModelModal();return}
 const c=conversationFor(activeConversationId);
 addMessage(activeConversationId,{role:"user",text});$("#prompt").value="";$("#prompt").style.height="";
 const task=explicitGenerationRequest(text);
 if(!task){
   // Aucun appel ComfyUI : le futur backend conversationnel répondra ici.
   addMessage(activeConversationId,{role:"assistant",text:"Je suis en mode conversation. Aucune génération n’est lancée tant que tu ne me demandes pas explicitement de créer une image, une retouche ou une vidéo."});
   return;
 }
 const model=selectedModelForConversation(c,task);
 if(!model){addMessage(activeConversationId,{role:"assistant",text:"Aucun modèle n’est configuré pour cette tâche dans cette conversation."});return}
 await startGeneration(task,model,text);
}

async function startGeneration(task,model,prompt){
 const id=activeConversationId;const c=conversationFor(id);
 c.messages.push({role:"assistant",loading:true,mediaType:task});c.updatedAt=new Date().toISOString();save();renderMessage(c.messages[c.messages.length-1]);scrollBottom();
 $("#send").disabled=true;
 try{
   const d=await api("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({workflow:model.id,prompt,negative:"",image:imageData?.data||null,image_name:imageData?.name||null})});
   await waitResult(d.prompt_id,id,model,prompt,task);
 }catch(e){removeLoading(id);addMessage(id,{role:"assistant",text:"Erreur de génération : "+e.message});toast(e.message)}
 finally{$("#send").disabled=false}
}

async function waitResult(pid,id,model,prompt,task){
 for(let i=0;i<900;i++){
   await new Promise(r=>setTimeout(r,1000));
   try{
     const d=await api("/api/history/"+encodeURIComponent(pid)),h=d[pid];if(!h)continue;
     if(h.status?.status_str==="error"||h.status?.status_str==="failed"){removeLoading(id);addMessage(id,{role:"assistant",text:"La génération a échoué."});return}
     if(h.outputs){
       let found=null;
       for(const o of Object.values(h.outputs)){if(o.images?.length){found=o.images[0];break}if(o.gifs?.length){found=o.gifs[0];break}}
       if(found){
         removeLoading(id);const c=conversationFor(id);c.messages.push({role:"assistant",result:found});c.updatedAt=new Date().toISOString();save();renderMessage(c.messages[c.messages.length-1]);scrollBottom();
         addLibrary(found,resultKindForModel(model),prompt);return;
       }
     }
   }catch(e){}
 }
 removeLoading(id);addMessage(id,{role:"assistant",text:"La génération prend plus de temps que prévu."});
}

function showSidebar(){$("#sidebar").classList.remove("closed")}
function hideSidebar(){$("#sidebar").classList.add("closed")}

async function refresh(){
 comfyReady=false;
 try{const h=await api("/api/health");comfyReady=!!h.online;$("#statusText").textContent=h.online?"ComfyUI connecté":"ComfyUI arrêté";$(".status").className="status "+(h.online?"ok":"bad")}
 catch(e){$("#statusText").textContent="Moteur indisponible";$(".status").className="status bad"}
 const d=await api("/api/workflows");workflows=d.workflows;
 renderConversationList($("#conversationSearch").value);renderLibraryCounts();
 if(activeConversationId&&conversations[activeConversationId])openConversation(activeConversationId);
 else if(!Object.keys(conversations).length){$("#welcome").classList.remove("hidden");$("#messages").innerHTML=""}
}

function setup(){
 $("#openSidebar").onclick=showSidebar;$("#closeSidebar").onclick=hideSidebar;
 $("#newConversation").onclick=openModelModal;
 $("#closeModal").onclick=closeModelModal;
 $("#modelModal").addEventListener("click",e=>{if(e.target.id==="modelModal")closeModelModal()});
 $("#createConversation").onclick=()=>{
   const missing=[];if(!modalSelection.image)missing.push("image");if(!modalSelection.retouch)missing.push("retouche");if(!modalSelection.video)missing.push("vidéo");
   if(missing.length){$("#modalError").textContent="Sélectionne un modèle pour chaque bloc.";return}createConversation();
 };
 document.querySelectorAll("[data-search]").forEach(input=>input.addEventListener("input",e=>renderOptions(e.target.dataset.search,e.target.value)));
 $("#conversationSearch").oninput=e=>renderConversationList(e.target.value);
 $("#send").onclick=sendMessage;
 $("#prompt").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();sendMessage()}});
 $("#prompt").addEventListener("input",e=>{e.target.style.height="auto";e.target.style.height=Math.min(e.target.scrollHeight,220)+"px"});
 $("#attachBtn").onclick=()=>$("#imageFile").click();
 $("#imageFile").onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{imageData={data:r.result,name:f.name};};r.readAsDataURL(f)};
 
 $("#photosLibrary").onclick=()=>renderLibrary("image","Mes photos générées");
 $("#videosLibrary").onclick=()=>renderLibrary("video","Mes vidéos générées");
 $("#retouchLibrary").onclick=()=>renderLibrary("retouch","Mes retouches générées");
 $("#importBtn").onclick=()=>$("#workflowFile").click();
 $("#workflowFile").onchange=async e=>{const f=e.target.files[0];if(!f)return;try{const wf=JSON.parse(await f.text());await api("/api/import-workflow",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:f.name,workflow:wf})});toast("Workflow ajouté.");await refresh()}catch(err){toast(err.message)}};
 $("#comfyBtn").onclick=()=>window.open("http://127.0.0.1:8188","_blank");
 refresh();
}
setup();