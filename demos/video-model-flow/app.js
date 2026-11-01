'use strict';
let data, index = 0, stage = 2, showMasks = false;
const $ = id => document.getElementById(id);
const source = $('video'), overlay = $('overlay');
const titles = ['A spoken request becomes text.','Find the object, pixel by pixel.','What changed at this moment?','Choose an inspection priority.','Ask for the next useful check.','Remember, then follow up.'];
const labels = ['VOICE TRANSCRIBE / REAL AUDIO INFERENCE','SAM 3.1 / REAL VIDEO SEGMENTATION','MUSE SPARK / REAL VIDEO OBSERVATION','RESCUE / DETERMINISTIC DEMO POLICY','MUSE WONDER / REAL HISTORY-TOOL LOOP','SHELFWATCH / RECORDED BATCH HISTORY'];
let tasks = [];
try { tasks = JSON.parse(localStorage.getItem('tomato-demo-tasks-v1') || '[]'); if (!Array.isArray(tasks)) tasks = []; } catch { tasks = []; }
function node(tag, text, cls) { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (cls) el.className = cls; return el; }
function para(text, cls) { return node('p', text, cls); }
function note(text) { return node('div', text, 'evidence-note'); }
function toast(text) { $('toast').textContent = text; $('toast').style.display = 'block'; clearTimeout(toast.timer); toast.timer = setTimeout(() => $('toast').style.display = 'none', 3500); }
function switchTab(tab) {
  document.querySelectorAll('.tab-panel').forEach(el => el.hidden = el.id !== tab);
  document.querySelectorAll('.nav').forEach(el => el.classList.toggle('active', el.dataset.tab === tab));
}
document.querySelectorAll('.nav').forEach(el => el.addEventListener('click', () => switchTab(el.dataset.tab)));
$('credits-link').addEventListener('click', () => { switchTab('trace'); window.scrollTo({top:0,behavior:'smooth'}); });
function setMode(masks) {
  showMasks = masks;
  const from = masks ? source : overlay, to = masks ? overlay : source;
  const time = from.currentTime || data?.spark.observation.checkpoints[index].second || 0;
  from.pause(); to.currentTime = time;
  source.hidden = masks; overlay.hidden = !masks;
  $('mask-choice').classList.toggle('chosen', masks); $('raw-choice').classList.toggle('chosen', !masks);
  $('media-badge').textContent = masks ? 'REAL SAM MASKS / RECORDED VIDEO OUTPUT' : 'SOURCE VIDEO / 4 FPS ANALYSIS COPY';
}
$('raw-choice').addEventListener('click', () => setMode(false));
$('mask-choice').addEventListener('click', () => setMode(true));
function choose(i, seek = true) {
  index = i;
  const cp = data.spark.observation.checkpoints[i];
  if (seek) { source.pause(); overlay.pause(); source.currentTime = cp.second; overlay.currentTime = cp.second; }
  document.querySelectorAll('.checkpoint').forEach((el,j) => { el.classList.toggle('selected',i===j); el.setAttribute('aria-pressed',String(i===j)); });
  $('playback-label').textContent = `00:${String(cp.second).padStart(2,'0')} / playback time`;
  $('mask-count').textContent = `${cp.mask_count} decoded tomato mask${cp.mask_count === 1 ? '' : 's'} at this checkpoint`;
  $('visual-score').textContent = cp.visual_priority_points + ' points';
  $('priority-label').textContent = cp.visual_priority_points >= 60 ? 'Hold for human inspection' : cp.visual_priority_points >= 30 ? 'Prioritize inspection' : 'Routine visual monitoring';
  $('next-check').textContent = cp.next_check;
  renderStage();
}
for (const video of [source,overlay]) {
  video.addEventListener('timeupdate', () => {
    if (video.hidden || video.paused || !data) return;
    let i = 0;
    data.spark.observation.checkpoints.forEach((cp,j) => { if (video.currentTime >= cp.second) i = j; });
    if (i !== index) choose(i,false);
    $('playback-label').textContent = `00:${String(Math.floor(video.currentTime)).padStart(2,'0')} / playback time`;
  });
  video.addEventListener('error',()=>toast('Video unavailable. The checkpoint stills and model receipts remain accessible.'));
}
function renderStage() {
  const cp = data.spark.observation.checkpoints[index], body = $('inspector-body'); body.replaceChildren();
  $('stage-label').textContent = labels[stage]; $('inspector-title').textContent = titles[stage]; $('stage-counter').textContent = `${stage+1} / 6`;
  document.querySelectorAll('.flow button').forEach((el,i)=>el.classList.toggle('selected',i===stage));
  document.querySelector('.verified').textContent = [3,5].includes(stage) ? '◇ Demo application logic' : '✓ API verified';
  $('prev-stage').disabled=stage===0; $('next-stage').textContent=stage===5?'View batch memory →':'Next step →';
  if (stage === 0) {
    body.append(para('The video has no sound. This separate demonstration request was synthesized locally, then sent to the real speech-to-text model.'));
    const audio=node('audio'); audio.src='voice_request.wav'; audio.controls=true; body.append(audio);
    body.append(note('SYNTHETIC INPUT · REAL TRANSCRIPTION'),para('“'+data.voice.response.transcript+'”','output'),para(`${data.voice.response.audioDurationMs / 1000}s audio · ${data.voice.elapsed_seconds}s API latency`));
  } else if (stage === 1) {
    const metric=node('div',undefined,'metric'); metric.append(node('strong',String(data.sam.frames_with_masks)),node('small',`video frames with decoded masks / ${data.frame_count} source analysis frames`));
    body.append(metric,para('SAM follows the tomato through the video and returns object boxes and pixel masks. It does not decide whether the tomato is fresh.'),note('The overlay is rendered from the actual returned masks. No hand-drawn segmentation is substituted.'),para(`Current checkpoint: ${cp.mask_count} mask(s). Parsing diagnostics: ${data.sam.diagnostics.length}.`));
    const b=node('button','Show SAM overlay →','text-button');b.onclick=()=>setMode(true);body.append(b);
  } else if (stage === 2) {
    body.append(node('span',cp.visible_concern.replaceAll('_',' ')+' · visual category','concern'+(cp.visual_priority_points>=60?' high':'')),para(cp.observation,'output'),note('These words are the saved Muse Spark output at '+cp.second+'s. Single viewpoint; no internal, gas or microbial measurements.'),para('Next check: '+cp.next_check));
  } else if (stage === 3) {
    body.append(node('span',$('priority-label').textContent,'concern'+(cp.visual_priority_points>=60?' high':'')),para(`The model's “${cp.visible_concern.replaceAll('_',' ')}” category maps to ${cp.visual_priority_points} visual-priority points in the proposed code policy.`),note('CAMERA-ONLY, PROVISIONAL. Sensor score and fused score are unavailable. The missing channel is not treated as a reassuring zero.'),para('This single-sample replay cannot demonstrate cross-crate ranking or a sensor-driven priority flip. Human inspection remains the next action.'));
  } else if (stage === 4) {
    body.append(note('REAL WONDER PLAN · READ-ONLY HISTORY TOOL · FULL-CLIP SUMMARY. This plan uses all recorded checkpoints, not only the currently selected moment.'));
    body.append(para(data.wonder.plan,'output'));
    const b=node('button','Review the next recorded observation →','text-button');b.onclick=()=>{choose(Math.min(index+1,data.spark.observation.checkpoints.length-1));setStage(2);};body.append(b);
    body.append(para('A physical repeat or A/B group test cannot be performed on a time-lapse. This button reviews saved evidence; it does not acquire a new sensor reading.'));
  } else {
    body.append(para('One batch ID ties together the source, dated model run, playback checkpoints, masks, request and plan. A later visit would add evidence to this same record.'),note('Demo actions are stored only in this browser. No real stock was sold, removed, inspected or approved.'),para(`${tasks.length} local demo task(s) created.`));
    const b=node('button','Open batch history →','primary');b.onclick=()=>switchTab('history');body.append(b);
    const receipt=node('button','Download evidence receipt ↓','text-button');receipt.onclick=downloadReceipt;body.append(receipt);
  }
}
function setStage(i){stage=i;renderStage();if(stage===1)setMode(true);}
document.querySelectorAll('.flow button').forEach(el=>el.onclick=()=>setStage(Number(el.dataset.stage)));
$('walkthrough').onclick=()=>{switchTab('replay');choose(0);setStage(0);toast('Step through the real recorded outputs. No new API calls will be made.');};
$('prev-stage').onclick=()=>setStage(Math.max(0,stage-1));
$('next-stage').onclick=()=>stage===5?switchTab('history'):setStage(stage+1);
$('investigate').onclick=()=>{setStage(4);document.querySelector('.workspace').scrollIntoView({behavior:'smooth',block:'start'});};
function renderHistory(){
  const list=$('history-list');list.replaceChildren();
  data.spark.observation.checkpoints.forEach((cp,i)=>{const row=node('article',undefined,'history-item'),img=node('img');img.src=`checkpoint_${i}.jpg`;img.alt=`Source at ${cp.second} playback seconds`;const text=node('div');text.append(node('h3',`00:${String(cp.second).padStart(2,'0')} / ${cp.visible_concern.replaceAll('_',' ')}`),para(cp.observation));const b=node('button','Inspect this checkpoint →','text-button');b.onclick=()=>{switchTab('replay');choose(i);setStage(2);};text.append(b);row.append(img,text);list.append(row);});
}
function saveTasks(){try{localStorage.setItem('tomato-demo-tasks-v1',JSON.stringify(tasks));}catch{toast('Storage unavailable: tasks remain in memory for this visit.');}}
function renderTasks(){const list=$('task-list');list.replaceChildren();for(const task of tasks){const row=node('div',undefined,'task');row.append(node('span',`${task.completed?'✓ Reviewed demo':'○ Pending demo'} · checkpoint ${task.second}s · ${task.created}`));if(!task.completed){const b=node('button','Mark demo reviewed');b.onclick=()=>{task.completed=true;saveTasks();renderTasks();toast('Demo review saved locally. No physical inspection was claimed.');};row.append(b);}list.append(row);}}
$('create-task').onclick=()=>{if(tasks.some(t=>!t.completed&&t.second===data.spark.observation.checkpoints[index].second)){toast('An open demo task already exists for this checkpoint.');return;}tasks.push({second:data.spark.observation.checkpoints[index].second,created:new Date().toLocaleString(),completed:false,kind:'browser_local_demo_not_real_stock_action'});saveTasks();renderTasks();toast('Demo task created in this browser only.');};
function downloadReceipt(){const receipt={type:'demonstration_evidence_receipt',source:data.source,recorded_run_utc:data.run_utc,checkpoint:data.spark.observation.checkpoints[index],model_response_ids:{spark:data.spark.response_id,sam:data.sam.response_id,wonder:data.wonder.calls.map(c=>c.response_id)},voice_source:data.voice.input_kind,sensor_session:null,physical_vendor_action:null,browser_local_demo_tasks:tasks,limits:'Recorded replay. Playback time is not storage time. No food-safety or shelf-life validation.'};const url=URL.createObjectURL(new Blob([JSON.stringify(receipt,null,2)],{type:'application/json'}));const a=node('a');a.href=url;a.download='video-tomato-demo-receipt.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
document.querySelectorAll('.export').forEach(el=>el.onclick=downloadReceipt);
function renderTrace(){const cards=$('model-cards');const models=[['SAM 3.1','sam-3.1',data.sam.elapsed_seconds,`Processed ${data.sam.usage?.video_frames_processed??data.frame_count} billed/reported video frames. ${data.sam.frames_with_masks} frames contain masks.`,data.sam.response_id,{usage:data.sam.usage,diagnostics:data.sam.diagnostics}],['Muse Spark','muse-spark-1.3',data.spark.elapsed_seconds,'Full uploaded video → eight structured observations and visibility limits.',data.spark.response_id,data.spark.observation],['Muse Wonder','muse-wonder-1.0',data.wonder.elapsed_seconds,`${data.wonder.calls.length} real model calls; allowlisted history tool; recorded video observations.`,data.wonder.calls.map(c=>c.response_id).join(', '),{tool_trace:data.wonder.tool_trace,calls:data.wonder.calls}],['Muse Voice Transcribe','muse-voice-transcribe-1.0',data.voice.elapsed_seconds,'Synthetic spoken demo request → real transcript. Original video is silent.',data.voice.response.sessionId,data.voice.response]];for(const [title,model,latency,desc,id,raw]of models){const card=node('article',undefined,'trace-card');card.append(node('h3',title),para(`${model} · ${latency}s observed latency`,'model-meta'),para(desc),node('code',id));const detail=node('details'),summary=node('summary','Inspect the recorded output');detail.append(summary,node('pre',JSON.stringify(raw,null,2)));card.append(detail);cards.append(card);}}
fetch('demo_data.json').then(r=>{if(!r.ok)throw new Error('Recorded results failed to load');return r.json();}).then(result=>{data=result;const points=data.spark.observation.checkpoints;points.forEach((cp,i)=>{const button=node('button',undefined,'checkpoint');button.setAttribute('aria-label',`Inspect checkpoint ${cp.second} seconds`);const img=node('img');img.src=`checkpoint_${i}.jpg`;img.alt='';const label=node('span');const dot=node('i',undefined,cp.visible_concern==='severe'?'severe':cp.visible_concern==='clear'?'clear':'mild');label.append(dot,document.createTextNode(`${cp.second}s`));button.append(img,label);button.onclick=()=>choose(i);$('checkpoints').append(button);});source.poster='checkpoint_0.jpg';overlay.poster='checkpoint_overlay_0.jpg';renderHistory();renderTrace();renderTasks();choose(0,false);}).catch(error=>{$('inspector-title').textContent='Recorded data could not load';$('inspector-body').textContent=error.message;toast('Please reload the page to load the recorded model results.');});
