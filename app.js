const $ = (id) => document.getElementById(id);
const ids = ["age","sex","smoking","pack","tumor","stretch","frequency","duration","stiffness","fibrosis","il6","vegf","ki67"];

// Canvas contexts for both signals
const chart = $("signalChart"), ctx = chart.getContext("2d");
const ecgCanvas = $("ecgChart"), ecgCtx = ecgCanvas.getContext("2d");

// Live ECG State
const ecgPoints = Array(150).fill(0);

// Initialize WebSocket with explicit cloud transport settings
const socket = io({
  transports: ['websocket', 'polling'],
  reconnectionAttempts: 5
});

function value(id) { return Number($(id).value) || 0; }

// --- MECHANICAL STRETCH DRAW LOGIC ---
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

// --- LIVE ECG DRAW LOGIC ---
function drawECGChart() {
  const box = ecgCanvas.getBoundingClientRect(), ratio = devicePixelRatio || 1;
  
  // Prevent drawing if the canvas hasn't been sized by CSS yet
  if (box.width === 0 || box.height === 0) return;
  
  ecgCanvas.width = box.width * ratio; ecgCanvas.height = box.height * ratio; ecgCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const w = box.width, h = box.height;
  ecgCtx.clearRect(0,0,w,h); ecgCtx.strokeStyle = "rgba(16,185,129,0.15)"; ecgCtx.lineWidth = 1;
  for(let y=15;y<h;y+=15){ecgCtx.beginPath();ecgCtx.moveTo(0,y);ecgCtx.lineTo(w,y);ecgCtx.stroke()}
  for(let x=0;x<w;x+=30){ecgCtx.beginPath();ecgCtx.moveTo(x,0);ecgCtx.lineTo(x,h);ecgCtx.stroke()}
  
  ecgCtx.strokeStyle = "#10b981"; ecgCtx.lineWidth = 2; ecgCtx.beginPath();
  for(let i=0; i<ecgPoints.length; i++) {
    const x = (i / (ecgPoints.length - 1)) * w;
    // Map signal amplitude (-100 to 100 mV) to canvas height
    const y = h/2 - (ecgPoints[i] / 100) * (h/2);
    i ? ecgCtx.lineTo(x,y) : ecgCtx.moveTo(x,y);
  } 
  ecgCtx.stroke();
}

// --- WEBSOCKET EVENT LISTENERS ---
socket.on('signal_feed', (data) => {
  // Push live point to buffer and redraw
  ecgPoints.push(data.val);
  ecgPoints.shift();
  drawECGChart();
});

socket.on('score_feed', (data) => {
  // Only update the score dynamically if the user has already run the baseline prediction once
  if (!$("scoreResult").classList.contains("hidden")) {
    showResult(data.score);
  }
});

// Built-in Telemetry Simulator (Runs until the ESP32 is powered on)
socket.on('connect', () => {
  $("ecgStatus").textContent = "Connected: Stream active";
  let time = 0;
  setInterval(() => {
    time += 0.12;
    // Simulates an ECG wave (P-wave, QRS-complex, T-wave)
    let mockEcg = (Math.sin(time)*10) + (time%4<0.1 ? 65:0) - (time%4>0.1&&time%4<0.2 ? 25:0) + (Math.random()*5);
    socket.emit('ecg_data', { value: mockEcg });
  }, 40);
});

// --- MODEL PREDICTION LOGIC ---
function payload() {
  return {Age:value("age"), Sex:value("sex"), Smoking:value("smoking"), Smoking_PackYears:value("pack"),
    Stretch:value("stretch"), Frequency:value("frequency"), Stretch_Duration:value("duration"), Fibrosis:value("fibrosis"),
    Tissue_Stiffness:value("stiffness"), IL6:value("il6"), VEGF:value("vegf"), Ki67:value("ki67"), Tumor_Size:value("tumor")};
}

async function predictWithModel() {
  const response = await fetch("/api/predict", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload())});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The model could not return a score.");
  return data.score; // Returns the baseline score
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

// --- FORM AND DOM EVENT LISTENERS ---
$("predictorForm").addEventListener("submit", async e => {
  e.preventDefault(); if(!e.currentTarget.reportValidity()) return;
  const button=e.currentTarget.querySelector(".primary"), original=button.innerHTML; button.disabled=true; button.textContent="Running model…";
  try { showResult(await predictWithModel()); drawChart(); }
  catch(error) { clearResults(); $("emptyResult").innerHTML=`<span>!</span><p>${error.message}<br />Check server logs.</p>`; }
  finally { button.disabled=false; button.innerHTML=original; }
});

$("predictorForm").addEventListener("reset", () => setTimeout(() => {clearResults(); drawChart();}));
$("loadExample").addEventListener("click", () => {const ex={age:65,sex:0,smoking:0,pack:5.6,tumor:2.13,stretch:11.3,frequency:.28,duration:18,stiffness:9,fibrosis:1,il6:33.1,vegf:195.9,ki67:31.8}; Object.entries(ex).forEach(([k,v])=>$(k).value=v); drawChart(); document.querySelector("#explorer").scrollIntoView({behavior:"smooth",block:"start"});});
["stretch","frequency"].forEach(id=>$(id).addEventListener("input",drawChart));
$("info").addEventListener("click",()=>$("infoDialog").showModal()); $("closeDialog").addEventListener("click",()=>$("infoDialog").close());
$("report").addEventListener("click",()=>window.print()); window.addEventListener("resize", () => { drawChart(); drawECGChart(); });

// Wait for the CSS and layout to fully load before drawing the canvases
window.addEventListener("load", () => {
  drawChart();
  drawECGChart();
});
