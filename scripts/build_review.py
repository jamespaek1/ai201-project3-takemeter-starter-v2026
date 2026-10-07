"""Build a self-contained, offline human review worksheet for TakeMeter.

The first 20 examples never carry a suggested label or AI note into the page.
The page does not train a model or attest that a person completed work for them.
It records only choices and confirmations the person makes in the worksheet.

Usage:
    python scripts/build_review.py --output review.html
"""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AREAS = ["Overall accuracy", "Per-label performance", "Balance", "Consistency", "Confidence"]


def load_payload(input_path, taxonomy_path, areas):
    """Validate the dataset and remove every cold-batch suggestion."""
    rows = json.loads(Path(input_path).read_text(encoding="utf-8"))
    taxonomy = json.loads(Path(taxonomy_path).read_text(encoding="utf-8"))
    if not isinstance(taxonomy, dict) or len(taxonomy) < 2:
        raise ValueError("Taxonomy must map at least two labels to definitions.")
    if not all(isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip()
               for k, v in taxonomy.items()):
        raise ValueError("Every taxonomy label and definition must be nonempty text.")
    if not isinstance(rows, list) or len(rows) != 200:
        raise ValueError("This worksheet requires exactly 200 review items.")
    clean, ids = [], set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError(f"Item {index + 1} requires nonempty text.")
        identifier = row.get("id")
        if not isinstance(identifier, (str, int)) or isinstance(identifier, bool) or str(identifier) in ids:
            raise ValueError(f"Item {index + 1} requires a unique string/integer id.")
        ids.add(str(identifier))
        if row.get("cold") is not (index < 20):
            raise ValueError("The first 20 items must be cold=true; the remaining 180 cold=false.")
        cold = index < 20
        label = "" if cold else row.get("label", "")
        note = "" if cold else row.get("note", "")
        if not cold and label not in taxonomy:
            raise ValueError(f"Draft item {index + 1} has no valid suggested label yet.")
        if not isinstance(note, str):
            raise ValueError(f"Item {index + 1} note must be text.")
        source = row.get("source_url", "")
        if not isinstance(source, str):
            raise ValueError(f"Item {index + 1} source_url must be text.")
        clean.append({"id": identifier, "text": row["text"], "source_url": source,
                      "label": label, "note": note, "cold": cold})
    if len(set(areas)) < 3 or not all(isinstance(a, str) and a.strip() for a in areas):
        raise ValueError("Supply at least three distinct criterion areas.")
    canonical = json.dumps({"items": clean, "taxonomy": taxonomy, "areas": areas},
                           sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {"items": clean, "taxonomy": taxonomy, "areas": areas,
            "fingerprint": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}


PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src data:; base-uri 'none'; form-action 'none'">
<title>TakeMeter · Your review worksheet</title>
<style>
:root{color-scheme:light;--ink:#162c38;--muted:#526774;--line:#d3dfdf;--teal:#086f64;--pale:#e8f5ef;--paper:#fff;--sand:#f6f5ef;--warn:#7a4512;--shadow:0 8px 30px #15353508;font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--sand);color:var(--ink);line-height:1.55}button,input,select,textarea{font:inherit}button,select{cursor:pointer}button{border:1px solid var(--teal);border-radius:8px;padding:10px 17px;background:var(--teal);color:#fff;font-weight:650}button.secondary{color:var(--teal);background:#fff}button:disabled{opacity:.48;cursor:not-allowed}button:hover:enabled{filter:brightness(.95)}:focus-visible{outline:3px solid #d47a14;outline-offset:3px}a{color:var(--teal);text-underline-offset:3px}h1,h2,h3,p{margin-top:0}h1{font-size:clamp(2rem,4vw,3.4rem);line-height:1.1;letter-spacing:-.045em;margin-bottom:20px}h2{font-size:1.35rem;line-height:1.3;letter-spacing:-.02em;margin-bottom:12px}h3{font-size:1rem;margin-bottom:8px}header,main,footer{width:min(1160px,calc(100% - 48px));margin:auto}header{padding:40px 0 24px}.eyebrow{font-size:.77rem;letter-spacing:.15em;text-transform:uppercase;font-weight:800;color:var(--teal);margin-bottom:14px}.intro{max-width:770px;font-size:1.08rem;color:var(--muted);margin-bottom:18px}.notice{padding:14px 17px;border:1px solid #cfddcb;border-left:4px solid var(--teal);border-radius:8px;background:var(--pale);font-size:.94rem}.notice p:last-child{margin-bottom:0}.notice.warning{border-color:#e7cba2;border-left-color:#b77729;background:#fff6e9;color:var(--warn)}.progress-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:22px 0}.progress-card{background:#fff;padding:18px 20px;border:1px solid var(--line);border-radius:12px}.progress-card strong{font-size:1.6rem;letter-spacing:-.04em}.progress-card small{display:block;color:var(--muted);font-weight:600}.progress-card progress{width:100%;height:6px;margin-top:12px;accent-color:var(--teal)}.work-grid{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:24px;align-items:start}.card{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:26px;box-shadow:var(--shadow);margin-bottom:24px}.section-heading{display:flex;align-items:center;gap:10px}.step{display:inline-grid;place-items:center;min-width:28px;height:28px;font-size:.83rem;font-weight:800;border:1px solid #a7cec4;background:var(--pale);border-radius:50%;color:var(--teal)}.muted{color:var(--muted)}.small{font-size:.85rem}.tabs{display:flex;gap:8px;margin:20px 0;flex-wrap:wrap}.tabs button{flex:1;white-space:nowrap}.tabs button[aria-selected="false"]{background:#fff;color:var(--teal)}.review-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.badge{background:var(--pale);color:var(--teal);font-size:.75rem;font-weight:750;padding:4px 9px;border-radius:30px;white-space:nowrap}.badge.pending{background:#f7ecd9;color:var(--warn)}.post{white-space:pre-wrap;overflow-wrap:anywhere;margin:18px 0 12px;padding:22px;background:#f7f9f8;border:1px solid #e3eae8;border-radius:10px;font-size:1.02rem;line-height:1.7}.source{font-size:.8rem;overflow-wrap:anywhere}.field{display:block;margin:18px 0}.field>span,.field>label{display:block;font-weight:700;font-size:.86rem;margin-bottom:7px}.field .hint{font-weight:400;color:var(--muted);margin-top:5px;font-size:.8rem}select,input[type="number"],textarea{width:100%;border:1px solid #aabebf;border-radius:7px;padding:10px 11px;background:white;color:var(--ink)}textarea{resize:vertical;min-height:80px}.check{display:flex;gap:10px;align-items:flex-start;background:var(--pale);border:1px solid #bcd8ce;border-radius:8px;padding:14px;cursor:pointer;font-size:.94rem}.check input{flex:none;width:19px;height:19px;margin:3px 0 0;accent-color:var(--teal)}.row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.navigation{justify-content:space-between;margin-top:22px}.navigation .row{gap:8px}.jump{max-width:170px;font-size:.85rem}.suggestion{font-size:.88rem;color:var(--muted);border-left:3px solid #d4e5df;padding-left:12px;white-space:pre-wrap;overflow-wrap:anywhere;margin:14px 0}.sidebar{position:sticky;top:20px}.sidebar .card{padding:21px}.taxonomy dt{font-size:.88rem;font-weight:800;margin:18px 0 5px;color:var(--teal)}.taxonomy dd{font-size:.85rem;margin:0;color:var(--muted)}.sidebar ol{margin:0;padding-left:20px;font-size:.85rem}.sidebar li{margin-bottom:12px}.criterion{border:1px solid var(--line);border-radius:10px;padding:20px;margin-top:18px}.criterion legend{padding:0 8px;font-weight:750;font-size:.92rem}.two-cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}.two-cols .field{margin:8px 0}.criteria-status{margin:14px 0 0;font-size:.88rem;color:var(--muted)}.downloads{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.save-status{font-size:.8rem;color:var(--muted)}footer{padding:0 0 36px;font-size:.8rem;color:var(--muted)}[hidden]{display:none!important}.storage-error{color:#943b11;font-weight:650}.complete{color:var(--teal)}.import-label{position:relative;cursor:pointer;color:var(--teal);text-decoration:underline;text-underline-offset:3px}.import-label input{position:absolute;width:1px;height:1px;opacity:0}.import-label:focus-within{outline:3px solid #d47a14;outline-offset:3px}.empty-state{padding:24px;text-align:center;background:#f6f8f6;border-radius:10px}.status-line{min-height:24px;font-size:.88rem;color:var(--muted)}@media(max-width:850px){.work-grid{grid-template-columns:1fr}.sidebar{position:static;display:grid;grid-template-columns:1fr 1fr;gap:20px}.sidebar .card{margin-bottom:20px}}@media(max-width:560px){header,main,footer{width:calc(100% - 28px)}header{padding-top:28px}.card{padding:19px}.progress-grid{gap:8px}.progress-card{padding:12px}.progress-card strong{font-size:1.2rem}.progress-card small{font-size:.74rem}.two-cols,.sidebar{grid-template-columns:1fr}.post{padding:16px}.navigation{align-items:stretch}.navigation>.row{width:100%;justify-content:space-between}.jump{max-width:none}.downloads button{width:100%}}
</style>
</head>
<body>
<header>
<div class="eyebrow">AI201 · Unit 5 · TakeMeter</div>
<h1>Your judgment is the dataset.</h1>
<p class="intro">Read the 200 real comments, make the labeling decisions, and write five acceptance criteria in your own words. This worksheet keeps the human work separate from the AI drafts.</p>
<div class="notice"><p><strong>Training is waiting on you.</strong> First classify 20 comments without suggestions. Then read and, where needed, correct every one of the 180 AI-labeled drafts. Write your own five criteria with numeric targets and reasons before training. No criteria or targets have been written for you.</p></div>
<div class="progress-grid" aria-label="Your progress">
<div class="progress-card"><small>01 · Your cold labels</small><strong id="cold-count">0 / 20</strong><progress id="cold-progress" max="20" value="0" aria-label="Cold labels completed"></progress></div>
<div class="progress-card"><small>02 · Drafts you reviewed</small><strong id="draft-count">0 / 180</strong><progress id="draft-progress" max="180" value="0" aria-label="Drafts reviewed"></progress></div>
<div class="progress-card"><small>03 · Your criteria</small><strong id="criteria-count">0 / 5</strong><progress id="criteria-progress" max="5" value="0" aria-label="Criteria completed"></progress></div>
</div>
<div class="row" style="justify-content:space-between"><span class="save-status" id="save-status" role="status">Your edits save in this browser.</span><button type="button" class="secondary" id="backup">Download progress backup</button></div>
</header>
<main class="work-grid">
<div>
<section class="card" aria-labelledby="review-title">
<h2 id="review-title" class="section-heading"><span class="step">1–2</span>Read and label</h2>
<p class="muted small">Apply the taxonomy to each whole comment. The cold batch has no suggested labels or explanations. Its completion unlocks the AI drafts.</p>
<div class="tabs" role="tablist" aria-label="Review batch"><button type="button" id="cold-tab" role="tab" aria-selected="true" aria-controls="review-panel">20 cold comments</button><button type="button" id="draft-tab" role="tab" aria-selected="false" aria-controls="review-panel" disabled>180 drafts · locked</button></div>
<div id="review-panel" role="tabpanel" aria-labelledby="cold-tab">
<div class="review-head"><h3 id="item-number" tabindex="-1"></h3><span id="item-status" class="badge pending"></span></div>
<article class="post" id="post-text" aria-label="Comment to label"></article>
<div id="source" class="source"></div>
<p id="suggestion" class="suggestion" hidden></p>
<label class="field"><span id="label-heading">Your label</span><select id="label-select" aria-describedby="label-help"></select><span class="hint" id="label-help"></span></label>
<label class="field"><span>Your note <span class="muted">(optional)</span></span><textarea id="item-note" placeholder="Explain a difficult boundary or record why you changed a draft."></textarea><span class="hint">For drafts, the existing note is AI-written until you review or revise it.</span></label>
<label class="check" id="review-check-wrap" hidden><input type="checkbox" id="review-check"><span>I read this entire comment, checked the proposed label and note against the taxonomy, and corrected them where needed.</span></label>
<div class="row navigation"><div class="row"><button type="button" class="secondary" id="previous">Previous</button><button type="button" id="next">Next comment</button></div><label class="small">Go to comment <select id="jump" class="jump" aria-label="Go to comment"></select></label></div>
<p class="status-line" id="batch-message" aria-live="polite"></p>
</div>
</section>
<section class="card" aria-labelledby="criteria-title">
<h2 id="criteria-title" class="section-heading"><span class="step">3</span>Write your acceptance criteria</h2>
<p class="muted small">You must author all five. Cover at least three areas. For each, state what you will measure, the numeric threshold and direction needed to pass, and why that target makes sense for these comments, labels, or class distribution. You may write these while reviewing; finish before training.</p>
<div id="criteria-fields"></div>
<p class="criteria-status" id="criteria-status" aria-live="polite"></p>
</section>
<section class="card" aria-labelledby="export-title">
<h2 id="export-title">Save your work for the project</h2>
<p class="muted small">A progress backup works at any point. The final review JSON unlocks after all 200 labels and all five criteria are complete. The CSV contains exactly <code>text,label,note</code> and unlocks only after you review every row. Downloading files does not submit the assignment or run training.</p>
<label class="field" style="max-width:250px"><span>Your actual hours spent <span class="muted">(optional)</span></span><input id="hours" type="number" min="0" step="0.1" inputmode="decimal" placeholder="Leave blank if unknown"></label>
<div id="ready-message" class="notice warning" role="status"></div>
<div class="downloads"><button type="button" id="export-json" disabled>Download final review JSON</button><button type="button" class="secondary" id="export-csv" disabled>Download labels.csv</button><button type="button" class="secondary" id="export-criteria" disabled>Download criteria.md</button></div>
<p class="small muted" style="margin:18px 0 0">Returning on another browser? <label class="import-label">Restore a progress JSON<input type="file" id="import" accept="application/json,.json"></label></p>
<p id="import-status" class="status-line" role="status"></p>
</section>
</div>
<aside class="sidebar" aria-label="Reference and instructions">
<section class="card"><h2>Label reference</h2><p class="small muted">Choose one label for the comment's main purpose.</p><dl class="taxonomy" id="taxonomy"></dl><h3 style="margin-top:22px">Boundary rule</h3><p class="small muted">A genuine request takes precedence over its background facts. Rhetorical or self-answered questions do not count as requests. For other comments, require support for the main claim: a number, URL, product name, ownership, or liking alone is not enough. A concrete firsthand observation counts as reported support, not verified truth.</p><hr style="border:0;border-top:1px solid var(--line);margin:24px 0"><h3>Draft distribution</h3><p class="small muted">These are the 180 AI suggestions, before your corrections. The 20 cold labels remain unknown until you choose them.</p><dl class="taxonomy" id="draft-distribution"></dl><p class="small muted" style="margin-top:16px">Use the community, taxonomy, and observed balance to choose your own criteria and targets.</p></section>
<section class="card"><h2>What you do</h2><ol><li><strong>Cold batch:</strong> choose each label yourself. A blank choice stays unfinished.</li><li><strong>AI drafts:</strong> read the text and check both label and note. Each row needs its own review checkbox.</li><li><strong>Criteria:</strong> supply five original criteria, five numeric targets, and five reasons across at least three areas.</li><li><strong>Hand back:</strong> download the final JSON so the project can import your decisions and begin training.</li></ol><p class="small muted">This page makes no automatic network requests. Source links open only when you select them. Progress is stored in this browser, so download a backup before switching browsers or clearing storage.</p></section>
</aside>
</main>
<footer>AI helped prepare the source collection, draft labels, and this worksheet. Your cold labels, corrections, review confirmations, and criteria remain your work to do.</footer>
<script type="application/json" id="payload">__PAYLOAD__</script>
<script>
"use strict";
const payload = JSON.parse(document.getElementById("payload").textContent);
const items = payload.items;
const labels = Object.keys(payload.taxonomy);
const key = "takemeter-human-review-v1-" + payload.fingerprint;
const $ = id => document.getElementById(id);
const validLabel = value => labels.includes(value);
const emptyCriterion = (_, i) => ({number:i+1,area:"",criterion:"",target:"",reason:""});
const fresh = () => ({items:items.map(row=>({id:row.id,label:row.cold?"":row.label,note:row.cold?"":row.note,reviewed:false,reviewed_at:null})),criteria:Array.from({length:5},emptyCriterion),hours_spent:"",cold_position:0,draft_position:0});
let state = fresh();
let mode = "cold";
let storageWorks = true;
const make = (tag, text, attrs={}) => {const el=document.createElement(tag);if(text!==undefined)el.textContent=text;for(const [name,value] of Object.entries(attrs))el.setAttribute(name,value);return el;};
const isCriterionComplete = c => payload.areas.includes(c.area) && c.criterion.trim().length>0 && c.target!=="" && Number.isFinite(Number(c.target)) && c.reason.trim().length>0;
const stats = () => {const cold=state.items.slice(0,20).filter(r=>r.reviewed && validLabel(r.label)).length;const draft=state.items.slice(20).filter(r=>r.reviewed && validLabel(r.label)).length;const criteria=state.criteria.filter(isCriterionComplete).length;const areas=new Set(state.criteria.filter(isCriterionComplete).map(c=>c.area)).size;return {cold,draft,criteria,areas,labelsDone:cold===20&&draft===180,criteriaDone:criteria===5&&areas>=3};};
const exportNote = (row,i) => items[i].cold?row.note:(row.reviewed&&validLabel(row.label)?row.note.replace(/\bpending_human_review\b/g,"human_reviewed"):row.note.replace(/\bhuman_reviewed\b/g,"pending_human_review"));
function normalizeImported(data) {
  if(!data || data.dataset_fingerprint!==payload.fingerprint || !Array.isArray(data.items) || data.items.length!==200 || !Array.isArray(data.criteria) || data.criteria.length!==5)throw Error("This backup does not match this worksheet's dataset and taxonomy.");
  const next=fresh();
  data.items.forEach((row,i)=>{
    if(!row || String(row.id)!==String(items[i].id) || (row.label!==""&&!validLabel(row.label)) || typeof row.note!=="string")throw Error("The backup contains an invalid review row.");
    if(row.text!==undefined && row.text!==items[i].text)throw Error("A backup comment differs from this worksheet.");
    next.items[i]={id:items[i].id,label:row.label,note:row.note,reviewed:row.reviewed===true&&validLabel(row.label),reviewed_at:typeof row.reviewed_at==="string"?row.reviewed_at:null};
  });
  data.criteria.forEach((c,i)=>{
    if(!c || ![c.area,c.criterion,c.reason].every(v=>typeof v==="string") || (c.area!==""&&!payload.areas.includes(c.area)) || !["string","number"].includes(typeof c.target))throw Error("The backup contains an invalid criterion.");
    if(c.target!==""&&!Number.isFinite(Number(c.target)))throw Error("Each criterion target must be numeric or blank.");
    next.criteria[i]={number:i+1,area:c.area,criterion:c.criterion,target:String(c.target),reason:c.reason};
  });
  const hours=data.hours_spent;
  if(hours!==null&&hours!==undefined&&hours!==""&&(!Number.isFinite(Number(hours))||Number(hours)<0))throw Error("Hours spent must be a nonnegative number or blank.");
  next.hours_spent=hours===null||hours===undefined?"":String(hours);
  const view=data.view||{};
  next.cold_position=Number.isInteger(view.cold_position)?Math.min(19,Math.max(0,view.cold_position)):0;
  next.draft_position=Number.isInteger(view.draft_position)?Math.min(179,Math.max(0,view.draft_position)):0;
  return next;
}
function exportData() {
  const s=stats();
  return {schema_version:1,dataset_fingerprint:payload.fingerprint,exported_at:new Date().toISOString(),
    disclosure:"AI prepared 180 draft labels and notes. Cold labels, review confirmations, corrections, and criteria are entered by the worksheet user; browser records are not independent verification of human authorship.",
    items:state.items.map((row,i)=>({id:row.id,text:items[i].text,source_url:items[i].source_url,label:row.label,note:exportNote(row,i),cold:items[i].cold,reviewed:row.reviewed,reviewed_at:row.reviewed_at})),
    criteria:state.criteria.map(c=>({...c,target:c.target===""?"":Number(c.target)})),
    hours_spent:state.hours_spent===""?null:Number(state.hours_spent),
    completion:{cold_labels:s.cold,reviewed_drafts:s.draft,criteria:s.criteria,criteria_areas:s.areas,labels_complete:s.labelsDone,criteria_complete:s.criteriaDone,ready_for_training:s.labelsDone&&s.criteriaDone},
    view:{cold_position:state.cold_position,draft_position:state.draft_position}};
}
function save() {
  try{localStorage.setItem(key,JSON.stringify(exportData()));storageWorks=true;$("save-status").textContent="Saved in this browser · " + new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"});$("save-status").classList.remove("storage-error");}
  catch(err){storageWorks=false;$("save-status").textContent="Browser storage is unavailable. Download a progress backup before closing this page.";$("save-status").classList.add("storage-error");}
}
try{const saved=localStorage.getItem(key);if(saved){state=normalizeImported(JSON.parse(saved));$("save-status").textContent="Your saved progress was restored from this browser.";}}
catch(err){storageWorks=false;$("save-status").textContent="Saved progress could not be read. Use a downloaded backup, or start here and download one before leaving.";$("save-status").classList.add("storage-error");}
function updateProgress() {
  const s=stats();
  $("cold-count").textContent=s.cold+" / 20";$("draft-count").textContent=s.draft+" / 180";$("criteria-count").textContent=s.criteria+" / 5";
  $("cold-progress").value=s.cold;$("draft-progress").value=s.draft;$("criteria-progress").value=s.criteria;
  $("draft-tab").disabled=s.cold!==20;$("draft-tab").textContent=s.cold===20?"180 AI drafts":"180 drafts · locked";
  $("export-json").disabled=!(s.labelsDone&&s.criteriaDone&&$("hours").validity.valid);$("export-csv").disabled=!s.labelsDone;$("export-criteria").disabled=!s.criteriaDone;
  $("criteria-status").textContent=s.criteria+" of 5 criteria complete · "+s.areas+" of at least 3 areas covered. "+(s.criteriaDone?"Your criteria are ready to export.":"Each criterion needs your own statement, a numeric target, and a reason.");
  const ready=$("ready-message");ready.replaceChildren();
  if(s.labelsDone&&s.criteriaDone){ready.className="notice";ready.append(make("strong","Ready to hand back."),document.createTextNode(" Download the final review JSON and share it with the project. Training has not run from this worksheet."));}
  else{ready.className="notice warning";ready.textContent="Before training: "+(20-s.cold)+" cold labels, "+(180-s.draft)+" draft reviews, and "+(5-s.criteria)+" criteria remain. "+(s.areas<3?"Your completed criteria must also cover at least 3 areas.":"");}
}
const position = () => mode==="cold"?state.cold_position:state.draft_position;
const currentIndex = () => position()+(mode==="cold"?0:20);
function setPosition(value) {if(mode==="cold")state.cold_position=value;else state.draft_position=value;save();renderReview();$("item-number").focus({preventScroll:true});}
function updateItemStatus() {
  const row=state.items[currentIndex()];const badge=$("item-status");badge.textContent=row.reviewed?(mode==="cold"?"You classified this":"You reviewed this"):(mode==="cold"?"Your choice needed":"Review needed");badge.className="badge"+(row.reviewed?"":" pending");
  const total=mode==="cold"?20:180;$("previous").disabled=position()===0;$("next").disabled=!row.reviewed||!validLabel(row.label);$("next").textContent=position()===total-1?(mode==="cold"?(stats().cold===20?"Open AI drafts":"First unclassified comment"):"First unreviewed draft"):"Next comment";
  $("review-check").checked=row.reviewed;
  const s=stats();$("batch-message").textContent=mode==="cold"?(s.cold===20?"All 20 cold comments are classified. You can now review the AI drafts.":"Choose each label yourself. Complete all 20 cold comments to unlock the drafts."):(s.draft===180?"All 180 drafts are reviewed. Check your criteria and download the final JSON.":"Check the review box only after reading this comment and checking its label and note.");
  const opt=$("jump").options[position()];if(opt)opt.textContent=(position()+1)+(row.reviewed?" · done":" · pending");
}
function renderReview() {
  if(mode==="draft"&&stats().cold!==20)mode="cold";
  const cold=mode==="cold",i=currentIndex(),row=state.items[i],source=items[i],total=cold?20:180;
  $("cold-tab").setAttribute("aria-selected",String(cold));$("draft-tab").setAttribute("aria-selected",String(!cold));$("review-panel").setAttribute("aria-labelledby",cold?"cold-tab":"draft-tab");
  $("item-number").textContent=(cold?"Cold comment ":"Draft comment ")+(position()+1)+" of "+total;
  $("post-text").textContent=source.text;$("source").replaceChildren();
  if(/^https?:\/\//i.test(source.source_url)){const link=make("a","Open original comment ↗",{href:source.source_url,target:"_blank",rel:"noopener noreferrer"});$("source").append(link);}
  else if(source.source_url)$("source").textContent="Source: "+source.source_url;
  $("suggestion").hidden=cold;
  $("suggestion").textContent=cold?"":"Original AI draft: "+source.label+"\n"+(source.note||"No draft explanation was supplied.");
  $("label-heading").textContent=cold?"Your label":"Label after your review";
  $("label-help").textContent=cold?"No label is preselected. Selecting a label records your own classification.":"Keep the draft label only if it fits. Changing a reviewed label or note requires confirming the review again.";
  $("label-select").replaceChildren(make("option","Choose a label…",{value:""}));labels.forEach(label=>$("label-select").append(make("option",label,{value:label})));$("label-select").value=row.label;
  $("item-note").value=row.note;$("item-note").nextElementSibling.hidden=cold;$("review-check-wrap").hidden=cold;
  $("jump").replaceChildren();for(let n=0;n<total;n++){const r=state.items[n+(cold?0:20)];$("jump").append(make("option",(n+1)+(r.reviewed?" · done":" · pending"),{value:String(n)}));}$("jump").value=String(position());
  updateItemStatus();updateProgress();
}
$("label-select").addEventListener("change",()=>{const row=state.items[currentIndex()];row.label=$("label-select").value;row.reviewed=mode==="cold"&&validLabel(row.label);row.reviewed_at=row.reviewed?new Date().toISOString():null;save();updateItemStatus();updateProgress();});
$("item-note").addEventListener("input",()=>{const row=state.items[currentIndex()];row.note=$("item-note").value;if(mode==="draft"){row.reviewed=false;row.reviewed_at=null;}save();updateItemStatus();updateProgress();});
$("review-check").addEventListener("change",()=>{const row=state.items[currentIndex()];row.reviewed=$("review-check").checked&&validLabel(row.label);row.reviewed_at=row.reviewed?new Date().toISOString():null;save();updateItemStatus();updateProgress();});
$("cold-tab").addEventListener("click",()=>{mode="cold";renderReview();});
$("draft-tab").addEventListener("click",()=>{if(stats().cold===20){mode="draft";renderReview();}});
$("previous").addEventListener("click",()=>setPosition(Math.max(0,position()-1)));
$("next").addEventListener("click",()=>{const total=mode==="cold"?20:180;if(position()<total-1)setPosition(position()+1);else if(mode==="cold"&&stats().cold===20){mode="draft";renderReview();$("item-number").focus({preventScroll:true});}else{const offset=mode==="cold"?0:20;const next=state.items.slice(offset,offset+total).findIndex(r=>!r.reviewed);if(next>=0)setPosition(next);else $("batch-message").textContent="This batch is complete. Finish your criteria and use the export section below.";}});
$("jump").addEventListener("change",()=>setPosition(Number($("jump").value)));
function field(title,control,hint) {const label=make("label",undefined,{class:"field"});label.append(make("span",title),control);if(hint)label.append(make("span",hint,{class:"hint"}));return label;}
function renderCriteria() {
  $("criteria-fields").replaceChildren();
  state.criteria.forEach((criterion,i)=>{
    const block=make("fieldset",undefined,{class:"criterion"});block.append(make("legend","Criterion "+(i+1)));
    const row=make("div",undefined,{class:"two-cols"});const area=make("select",undefined,{"aria-label":"Criterion "+(i+1)+" area"});area.append(make("option","Choose an area…",{value:""}));payload.areas.forEach(a=>area.append(make("option",a,{value:a})));area.value=criterion.area;
    const target=make("input",undefined,{type:"number",step:"any",inputmode:"decimal","aria-label":"Criterion "+(i+1)+" numeric target"});target.value=criterion.target;row.append(field("Area",area),field("Your numeric target",target,"Specify its unit and pass direction in the statement below."));
    const statement=make("textarea",undefined,{rows:"3","aria-label":"Criterion "+(i+1)+" statement"});statement.value=criterion.criterion;
    const reason=make("textarea",undefined,{rows:"3","aria-label":"Criterion "+(i+1)+" reason"});reason.value=criterion.reason;
    block.append(row,field("Your testable acceptance criterion",statement,"State the measure, threshold direction, and test procedure in your own words."),field("Why you chose this target",reason,"Tie your reason to this community, these label definitions, or your observed data distribution."));
    [[area,"area"],[target,"target"],[statement,"criterion"],[reason,"reason"]].forEach(([input,name])=>input.addEventListener("input",()=>{state.criteria[i][name]=input.value;save();updateProgress();}));
    $("criteria-fields").append(block);
  });
}
for(const [label,definition] of Object.entries(payload.taxonomy))$("taxonomy").append(make("dt",label),make("dd",definition));
for(const label of labels)$("draft-distribution").append(make("dt",label),make("dd",items.slice(20).filter(row=>row.label===label).length+" AI drafts"));
function download(name,content,type) {const url=URL.createObjectURL(new Blob([content],{type}));const a=make("a",undefined,{href:url,download:name});document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$("backup").addEventListener("click",()=>download("takemeter-review-progress.json",JSON.stringify(exportData(),null,2)+"\n","application/json"));
$("export-json").addEventListener("click",()=>{const s=stats();if(s.labelsDone&&s.criteriaDone&&$("hours").validity.valid)download("takemeter-review.json",JSON.stringify(exportData(),null,2)+"\n","application/json");});
const csvCell = value => '"'+String(value).replace(/"/g,'""')+'"';
$("export-csv").addEventListener("click",()=>{if(!stats().labelsDone)return;const rows=[["text","label","note"],...state.items.map((row,i)=>[items[i].text,row.label,items[i].cold?"cold; human_labeled"+(row.note?"; "+row.note:""):exportNote(row,i)])];download("labels.csv",rows.map(row=>row.map(csvCell).join(",")).join("\r\n")+"\r\n","text/csv;charset=utf-8");});
$("export-criteria").addEventListener("click",()=>{if(!stats().criteriaDone)return;const text="# Acceptance criteria\n\nWritten by the worksheet user before training.\n\n"+state.criteria.map(c=>c.number+". **"+c.area+"** — "+c.criterion+"\n\n   **Numeric target:** "+c.target+"\n\n   **Reason:** "+c.reason.replace(/\n/g,"\n   ")).join("\n\n")+"\n";download("criteria.md",text,"text/markdown;charset=utf-8");});
$("hours").value=state.hours_spent;$("hours").addEventListener("input",()=>{const value=$("hours").value;if(value!==""&&(!Number.isFinite(Number(value))||Number(value)<0)){$("hours").setCustomValidity("Enter your actual nonnegative hours, or leave blank. This invalid value has not been saved.");$("hours").reportValidity();$("export-json").disabled=true;return;}$("hours").setCustomValidity("");state.hours_spent=value;save();updateProgress();});
$("import").addEventListener("change",async event=>{const file=event.target.files[0];if(!file)return;try{if(file.size>5*1024*1024)throw Error("This file is too large to be a worksheet backup.");const candidate=normalizeImported(JSON.parse(await file.text()));state=candidate;mode="cold";$("hours").value=state.hours_spent;renderCriteria();renderReview();save();$("import-status").textContent="Progress restored. Review counts and criteria are shown above.";}catch(err){$("import-status").textContent="Could not restore: "+err.message;}finally{event.target.value="";}});
renderCriteria();renderReview();
</script>
</body>
</html>
'''


def build(input_path, taxonomy_path, output_path, areas=AREAS):
    payload = load_payload(input_path, taxonomy_path, areas)
    # Escape all HTML delimiters, including script-closing sequences in posts.
    encoded = json.dumps(payload, ensure_ascii=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(PAGE.replace("__PAYLOAD__", encoded), encoding="utf-8")
    return payload["fingerprint"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/review_items.json")
    parser.add_argument("--taxonomy", type=Path, default=ROOT / "data/taxonomy.json")
    parser.add_argument("--output", type=Path, default=ROOT / "review.html")
    parser.add_argument("--areas", nargs="+", default=AREAS)
    args = parser.parse_args()
    try:
        fingerprint = build(args.input, args.taxonomy, args.output, args.areas)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Built {args.output} (dataset {fingerprint[:12]}; 20 cold + 180 AI drafts).")


if __name__ == "__main__":
    main()
