const $ = (id) => document.getElementById(id);
const ids = ["age","sex","smoking","pack","tumor","stretch","frequency","duration","stiffness","fibrosis","il6","vegf","ki67"];
const chart = $("signalChart"), ctx = chart.getContext("2d");

function value(id) { return Number($(id).value) || 0; }
function drawChart() {
  const box = chart.getBoundingClientRect(), ratio = devicePixelRatio || 1;
  chart.width = box.width * ratio; chart.height = box.height * ratio; ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const w = box.width, h = box.height, stretch = value("stretch"), frequency = value("frequency");
  ctx.clearRect(0,0,w,h); ctx.strokeStyle = "rgba(194,224,215,.13)"; ctx.lineWidth = 1;
  for(let y=24;y<h;y+=34){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke()}
  for(let x=0;x<w;x+=56){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke()}
  ctx.strokeStyle = "#79d0a7"; ctx.lineWidth = 2.4; ctx.beginPath();
  const amplitude = Math.min(stretch / 30, 1) * (h*.32); const cycles = Math.max(frequency * 3, .2);
  for(let x=0;x<=w;x++){ const y=h/2 - amplitude*Math.sin((x/w)*Math.PI*2*cycles); x ? ctx.lineTo(x,y) : ctx.moveTo(x,y); } ctx.stroke();
  $("signalReadout").textContent = stretch && frequency ? `${stretch}% · ${frequency} Hz` : "Awaiting inputs";
}
function payload() {
  return {Age:value("age"), Sex:value("sex"), Smoking:value("smoking"), Smoking_PackYears:value("pack"),
    Stretch:value("stretch"), Frequency:value("frequency"), Stretch_Duration:value("duration"), Fibrosis:value("fibrosis"),
    Tissue_Stiffness:value("stiffness"), IL6:value("il6"), VEGF:value("vegf"), Ki67:value("ki67"), Tumor_Size:value("tumor")};
}
async function predictWithModel() {
  const response = await fetch("/api/predict", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload())});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The model could not return a score.");
  return data.score;
}
function showResult(score) {
  const scoreText = score.toFixed(3); let label="LOW", desc="Lower modeled progression signal", color="#70d5aa";
  if(score >= .60){label="HIGH";desc="Higher modeled progression signal";color="#ef7a6e"} else if(score >= .30){label="MODERATE";desc="Intermediate modeled progression signal";color="#e5bd5f"}
  $("emptyResult").classList.add("hidden"); $("scoreResult").classList.remove("hidden"); $("report").classList.remove("hidden");
  $("scoreValue").textContent=scoreText; $("riskLabel").textContent=label; $("riskDescription").textContent=desc; $("riskDot").style.background=color; $("meterFill").style.marginLeft=`${score*100}%`;
}
function clearResults() {
  $("scoreResult").classList.add("hidden"); $("emptyResult").classList.remove("hidden"); $("report").classList.add("hidden");
  $("emptyResult").innerHTML="<span>○</span><p>Enter study variables<br />to run the model.</p>";
  $("scoreValue").textContent="0.000"; $("meterFill").style.marginLeft="0%";
}
$("predictorForm").addEventListener("submit", async e => {
  e.preventDefault(); if(!e.currentTarget.reportValidity()) return;
  const button=e.currentTarget.querySelector(".primary"), original=button.innerHTML; button.disabled=true; button.textContent="Running model…";
  try { showResult(await predictWithModel()); drawChart(); }
  catch(error) { clearResults(); $("emptyResult").innerHTML=`<span>!</span><p>${error.message}<br />Run the site through <code>server.py</code>.</p>`; }
  finally { button.disabled=false; button.innerHTML=original; }
});
$("predictorForm").addEventListener("reset", () => setTimeout(() => {clearResults(); drawChart();}));
$("loadExample").addEventListener("click", () => {const ex={age:65,sex:0,smoking:0,pack:5.6,tumor:2.13,stretch:11.3,frequency:.28,duration:18,stiffness:9,fibrosis:1,il6:33.1,vegf:195.9,ki67:31.8}; Object.entries(ex).forEach(([k,v])=>$(k).value=v); drawChart(); document.querySelector("#explorer").scrollIntoView({behavior:"smooth",block:"start"});});
["stretch","frequency"].forEach(id=>$(id).addEventListener("input",drawChart));
$("info").addEventListener("click",()=>$("infoDialog").showModal()); $("closeDialog").addEventListener("click",()=>$("infoDialog").close());
$("report").addEventListener("click",()=>window.print()); window.addEventListener("resize",drawChart); drawChart();
