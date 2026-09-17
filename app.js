const $ = (id) => document.getElementById(id);
const ids = ["age","sex","smoking","pack","tumor","stretch","frequency","duration","stiffness","fibrosis","il6","vegf","ki67"];

// Canvas contexts for both live signals
const ecgCanvas = $("ecgChart"), ecgCtx = ecgCanvas.getContext("2d");
const stretchCanvas = $("stretchChart"), stretchCtx = stretchCanvas.getContext("2d");

// Live State Buffers
const ecgPoints = Array(150).fill(0);
const stretchPoints = Array(150).fill(0);

// Initialize WebSocket with explicit cloud transport settings
const socket = io({
  transports: ['websocket', 'polling'],
  reconnectionAttempts: 5
});

function value(id) { return Number($(id).value) || 0; }

// --- LIVE ECG DRAW LOGIC ---
function drawECGChart() {
  const box = ecgCanvas.getBoundingClientRect(), ratio = devicePixelRatio || 1;
  
  if (box.width === 0 || box.height === 0) return; // Prevent drawing if not sized
  
  ecgCanvas.width = box.width * ratio; ecgCanvas.height = box.height * ratio; ecgCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const w = box.width, h = box.height;
  
  ecgCtx.clearRect(0,0,w,h); ecgCtx.strokeStyle = "rgba(16,185,129,0.15)"; ecgCtx.lineWidth = 1;
  for(let y=15;y<h;y+=15){ecgCtx.beginPath();ecgCtx.moveTo(0,y);ecgCtx.lineTo(w,y);ecgCtx.stroke()}
  for(let x=0;x<w;x+=30){ecgCtx.beginPath();ecgCtx.moveTo(x,0);ecgCtx.lineTo(x,h);ecgCtx.stroke()}
  
  ecgCtx.strokeStyle = "#10b981"; ecgCtx.lineWidth = 2; ecgCtx.beginPath();
  for(let i=0; i<ecgPoints.length; i++) {
    const x = (i / (ecgPoints.length - 1)) * w;
    // Map signal amplitude to canvas height
    const y = h/2 - (ecgPoints[i] / 100) * (h/2);
    i ? ecgCtx.lineTo(x,y) : ecgCtx.moveTo(x,y);
  } 
  ecgCtx.stroke();
}

// --- LIVE STRETCH DRAW LOGIC ---
function drawStretchChart() {
  const box = stretchCanvas.getBoundingClientRect(), ratio = devicePixelRatio || 1;
  
  if (box.width === 0 || box.height === 0) return;
  
  stretchCanvas.width = box.width * ratio; stretchCanvas.height = box.height * ratio; stretchCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const w = box.width, h = box.height;
  
  stretchCtx.clearRect(0,0,w,h); stretchCtx.strokeStyle = "rgba(59,130,246,0.15)"; stretchCtx.lineWidth = 1;
  for(let y=15;y<h;y+=15){stretchCtx.beginPath();stretchCtx.moveTo(0,y);stretchCtx.lineTo(w,y);stretchCtx.stroke()}
  for(let x=0;x<w;x+=30){stretchCtx.beginPath();stretchCtx.moveTo(x,0);stretchCtx.lineTo(x,h);stretchCtx.stroke()}
  
  stretchCtx.strokeStyle = "#3b82f6"; stretchCtx.lineWidth = 2; stretchCtx.beginPath();
  for(let i=0; i<stretchPoints.length; i++) {
    const x = (i / (stretchPoints.length - 1)) * w;
    // Map stretch signal to canvas height
    const y = h/2 - (stretchPoints[i] / 100) * (h/2);
    i ? stretchCtx.lineTo(x,y) : stretchCtx.moveTo(x,y);
  } 
  stretchCtx.stroke();
}

// --- WEBSOCKET EVENT LISTENERS ---
socket.on('signal_feed', (data) => {
  // Update ECG buffer and redraw
  ecgPoints.push(data.ecg_val);
  ecgPoints.shift();
  drawECGChart();

  // Update Stretch buffer and redraw
  stretchPoints.push(data.stretch_val);
  stretchPoints.shift();
  drawStretchChart();
});

socket.on('score_feed', (data) => {
  // Only update the score dynamically if the user has already run the baseline prediction once
  if (!$("scoreResult").classList.contains("hidden")) {
    showResult(data.score);
  }
});

// Auto-fill form and UI from calculated live backend data
socket.on('biomechanics_update', (data) => {
  // Update the Stretch UI
  if ($("liveAmplitude") && $("liveFrequency")) {
    $("liveAmplitude").textContent = data.amplitude + "%";
    $("liveFrequency").textContent = data.frequency + " Hz";
    $("stretchStatus").textContent = "Auto-synced to form";
  }

  // Update the ECG UI
  if ($("liveHeartRate")) {
    $("liveHeartRate").textContent = data.bpm + " BPM";
    $("ecgStatus").textContent = "Auto-calculated";
  }

  // Automatically fill the input boxes on the left panel
  $("stretch").value = data.amplitude;
  $("frequency").value = data.frequency;

  // Give the input boxes a quick flash
  $("stretch").style.backgroundColor = "#e0f2fe"; 
  $("frequency").style.backgroundColor = "#e0f2fe";
  setTimeout(() => {
    $("stretch").style.backgroundColor = "";
    $("frequency").style.backgroundColor = "";
  }, 600);
});

// Built-in Telemetry Simulator (Runs until the Hardware is connected)
socket.on('connect', () => {
  $("ecgStatus").textContent = "Connected: Stream active";
  if ($("stretchStatus")) $("stretchStatus").textContent = "Connected: Stream active";
  
  let time = 0;
  setInterval(() => {
    time += 0.12;
    // Simulates an ECG wave
    let mockEcg = (Math.sin(time)*10) + (time%4<0.1 ? 65:0) - (time%4>0.1&&time%4<0.2 ? 25:0) + (Math.random()*5);
    // Simulates a slower, rolling mechanical stretch wave (like breathing/movement)
    let mockStretch = (Math.sin(time * 0.4) * 40) + (Math.random() * 2);
    
    // Emit the combined payload mimicking the hardware
    socket.emit('sensor_data', { ecg_value: mockEcg, stretch_value: mockStretch });
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

// --- FORM AND DOM EVENT LISTENERS ---
$("predictorForm").addEventListener("submit", async e => {
  e.preventDefault(); if(!e.currentTarget.reportValidity()) return;
  const button=e.currentTarget.querySelector(".primary"), original=button.innerHTML; button.disabled=true; button.textContent="Running model…";
  try { showResult(await predictWithModel()); }
  catch(error) { clearResults(); $("emptyResult").innerHTML=`<span>!</span><p>${error.message}<br />Check server logs.</p>`; }
  finally { button.disabled=false; button.innerHTML=original; }
});

$("predictorForm").addEventListener("reset", () => setTimeout(() => clearResults()));
$("loadExample").addEventListener("click", () => {const ex={age:65,sex:0,smoking:0,pack:5.6,tumor:2.13,stretch:11.3,frequency:.28,duration:18,stiffness:9,fibrosis:1,il6:33.1,vegf:195.9,ki67:31.8}; Object.entries(ex).forEach(([k,v])=>$(k).value=v); document.querySelector("#explorer").scrollIntoView({behavior:"smooth",block:"start"});});
$("info").addEventListener("click",()=>$("infoDialog").showModal()); $("closeDialog").addEventListener("click",()=>$("infoDialog").close());
$("report").addEventListener("click",()=>window.print()); 
window.addEventListener("resize", () => { drawECGChart(); drawStretchChart(); });

// Wait for the CSS and layout to fully load before drawing the canvases
window.addEventListener("load", () => {
  drawECGChart();
  drawStretchChart();
});
