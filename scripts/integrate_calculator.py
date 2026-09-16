from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

button_anchor = '    <h3>Edit Sets — ${escapeHtml(ex.name)}</h3>\n'
button_insert = '''    <h3>Edit Sets — ${escapeHtml(ex.name)}</h3>\n\n    <div class="actions" style="margin:0 0 12px;">\n      <button style="width:100%; border-color:rgba(61,214,198,.45);" onclick="openWorkoutCalculator('${groupId}','${exId}')">Calculate using calculator</button>\n    </div>\n'''
if 'Calculate using calculator' not in s:
    if button_anchor not in s:
        raise SystemExit('Edit Sets anchor not found')
    s = s.replace(button_anchor, button_insert, 1)

marker = '''/* =======================\n   GROUP LIST / SORT\n======================= */'''
calculator = r'''
/* =======================
   WORKOUT LOAD CALCULATOR
======================= */
const LOAD_CALC_PCT={1:1,2:.95,3:.93,4:.90,5:.87,6:.85,7:.83,8:.80,9:.77,10:.75,11:.72,12:.70,13:.68,14:.66,15:.65};
let LOAD_CALC_CONTEXT=null;
let LOAD_CALC_ROWS=[];

function loadCalcRoundDown(value, increment){
  return Math.floor((value / increment) + Number.EPSILON) * increment;
}
function loadCalcWeight(value, increment){
  return value.toFixed(Number.isInteger(increment) ? 0 : 1);
}
function openWorkoutCalculator(groupId, exId){
  const g=APP.groups.find(x=>x.id===groupId);
  const ex=g?.exercises.find(e=>e.id===exId);
  if(!g || !ex) return;
  LOAD_CALC_CONTEXT={groupId,exId};
  const cfg=ex.percentageConfig || {};
  const startWeight=Number(cfg.maxWeight)>0 ? Number(cfg.maxWeight) : 140;
  const startReps=Number(cfg.maxReps)>0 ? Math.min(15,Math.max(1,Number(cfg.maxReps))) : 12;

  openModal(`
    <h3>Workout Load Calculator — ${escapeHtml(ex.name)}</h3>
    <div class="hint" style="margin-bottom:12px;">Enter a weight and reps you completed. The calculator estimates 1RM, then builds a warm up and descending working sets.</div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
      <label class="hint">Weight done (lb)<input id="lcDoneWeight" type="number" inputmode="decimal" min="2.5" max="500" step="2.5" value="${startWeight.toFixed(1)}" oninput="updateWorkoutCalculator()"></label>
      <label class="hint">Reps done: <b id="lcDoneRepsVal">${startReps}</b><input id="lcDoneReps" type="range" min="1" max="15" step="1" value="${startReps}" oninput="updateWorkoutCalculator()"></label>
      <label class="hint">Calculated 1RM (lb)<input id="lcOneRM" type="number" readonly></label>
      <label class="hint">Target reps: <b id="lcTargetRepsVal">12</b><input id="lcTargetReps" type="range" min="1" max="15" step="1" value="12" oninput="updateWorkoutCalculator()"></label>
      <label class="hint">Working sets: <b id="lcSetsVal">4</b><input id="lcSets" type="range" min="1" max="5" step="1" value="4" oninput="updateWorkoutCalculator()"></label>
      <label class="hint">Drop per set: <b id="lcDropVal">20%</b><input id="lcDrop" type="range" min="0" max="100" step="5" value="20" oninput="updateWorkoutCalculator()"></label>
      <label class="hint">Rest: <b id="lcRestVal">60 sec</b><input id="lcRest" type="range" min="30" max="180" step="30" value="60" oninput="updateWorkoutCalculator()"></label>
      <label class="hint">Round down to (lb)<select id="lcRound" onchange="updateWorkoutCalculator()" style="width:100%;padding:12px;border-radius:12px;background:rgba(12,16,22,.55);color:var(--text);border:1px solid rgba(255,255,255,.14);"><option value="2.5" selected>2.5</option><option value="5">5</option><option value="10">10</option></select></label>
    </div>

    <div id="lcSummary" class="hint" style="margin:14px 0 8px;"></div>
    <div id="lcResults" class="percent-preview"></div>

    <div class="hint" style="margin-top:14px;text-align:center;">Would you like to update the sets for this workout to the calculated sets above?</div>
    <div class="actions">
      <button onclick="openSetSettings('${groupId}','${exId}')">Back</button>
      <button style="border-color:rgba(61,214,198,.45);" onclick="applyWorkoutCalculatorSets()">Update sets for this workout</button>
    </div>
  `);
  updateWorkoutCalculator();
}

function updateWorkoutCalculator(){
  const doneWeight=Number(document.getElementById('lcDoneWeight')?.value)||0;
  const doneReps=Math.max(1,Math.min(15,parseInt(document.getElementById('lcDoneReps')?.value,10)||1));
  const targetReps=Math.max(1,Math.min(15,parseInt(document.getElementById('lcTargetReps')?.value,10)||1));
  const workingSets=Math.max(1,parseInt(document.getElementById('lcSets')?.value,10)||1);
  const drop=(Number(document.getElementById('lcDrop')?.value)||0)/100;
  const rest=Number(document.getElementById('lcRest')?.value)||0;
  const increment=Number(document.getElementById('lcRound')?.value)||2.5;
  const rm=doneWeight/(LOAD_CALC_PCT[doneReps]||1);
  const base=rm*(LOAD_CALC_PCT[targetReps]||1);

  const doneRepsVal=document.getElementById('lcDoneRepsVal'); if(doneRepsVal) doneRepsVal.textContent=doneReps;
  const targetVal=document.getElementById('lcTargetRepsVal'); if(targetVal) targetVal.textContent=targetReps;
  const setsVal=document.getElementById('lcSetsVal'); if(setsVal) setsVal.textContent=workingSets;
  const dropVal=document.getElementById('lcDropVal'); if(dropVal) dropVal.textContent=Math.round(drop*100)+'%';
  const restVal=document.getElementById('lcRestVal'); if(restVal) restVal.textContent=rest+' sec';
  const rmEl=document.getElementById('lcOneRM'); if(rmEl) rmEl.value=rm.toFixed(1);

  LOAD_CALC_ROWS=[];
  const warmRaw=base*.50;
  const warmWeight=loadCalcRoundDown(warmRaw,increment);
  LOAD_CALC_ROWS.push({label:'Warm Up',weight:warmWeight,reps:targetReps,raw:warmRaw});
  for(let set=1;set<=workingSets;set++){
    const raw=base*Math.pow(1-drop,set-1);
    LOAD_CALC_ROWS.push({label:`Set ${set}`,weight:loadCalcRoundDown(raw,increment),reps:targetReps,raw});
  }

  const totalVolume=LOAD_CALC_ROWS.reduce((sum,row)=>sum+(row.weight*row.reps),0);
  const summary=document.getElementById('lcSummary');
  if(summary) summary.innerHTML=`Fresh target: <b>${loadCalcWeight(loadCalcRoundDown(base,increment),increment)} lb</b> &nbsp; • &nbsp; Working reps: <b>${workingSets*targetReps}</b> &nbsp; • &nbsp; Total volume: <b>${totalVolume.toLocaleString(undefined,{maximumFractionDigits:1})} lb</b> &nbsp; • &nbsp; Rest: <b>${rest} sec</b>`;
  const results=document.getElementById('lcResults');
  if(results) results.innerHTML=LOAD_CALC_ROWS.map(row=>`<div class="percent-preview-row"><strong>${escapeHtml(row.label)}</strong><span>${rm>0?(row.raw/rm*100).toFixed(1):'0.0'}% 1RM</span><span>${loadCalcWeight(row.weight,increment)} lb × ${row.reps}</span></div>`).join('');
}

function applyWorkoutCalculatorSets(){
  if(!LOAD_CALC_CONTEXT || !LOAD_CALC_ROWS.length) return;
  const {groupId,exId}=LOAD_CALC_CONTEXT;
  const g=APP.groups.find(x=>x.id===groupId);
  const ex=g?.exercises.find(e=>e.id===exId);
  if(!g || !ex) return;

  const oldLabels=[...getExerciseSetLabels(ex)];
  const newLabels=LOAD_CALC_ROWS.map(row=>row.label);
  migrateWorkoutKeys_ExerciseSetLabels(g,ex,oldLabels,newLabels);
  ex.setLabels=newLabels;
  ex.percentageConfig={enabled:false,maxWeight:0,maxReps:0};
  saveAppData(APP);

  LOAD_CALC_ROWS.forEach(row=>{
    const key=`${KEY_PREFIX}${safeKey(g.name)}::${safeKey(ex.name)}::${safeKey(row.label)}`;
    localStorage.setItem(key,JSON.stringify({weight:row.weight,set:row.reps}));
  });

  closeModal();
  if(CURRENT_GROUP_ID===groupId) openGroupPanel(groupId);
}

'''
if 'const LOAD_CALC_PCT=' not in s:
    if marker not in s:
        raise SystemExit('Group list marker not found')
    s = s.replace(marker, calculator + marker, 1)

p.write_text(s, encoding='utf-8')
print('Calculator integration applied to index.html')
