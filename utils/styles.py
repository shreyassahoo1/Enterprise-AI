"""
utils/styles.py
---------------
Shared design tokens — CSS and animated background canvas.
Imported by both app.py and pages/admin.py for consistent styling.
"""

# ── Design tokens ──────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
/* ── Fonts ─────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');

/* ── Palette ───────────────────────── */
:root {
  --cream:      #F5F2EC;
  --cream-mid:  #EDE9E1;
  --cream-dark: #D8D2C8;
  --green:      #1C3D2E;
  --green-mid:  #2A5440;
  --green-light:#3B7057;
  --green-glow: rgba(28,61,46,0.12);
  --text:       #1A1A1A;
  --text-muted: #5A5A5A;
  --text-light: #8A8A8A;
  --white:      #FFFFFF;
  --error:      #C0392B;
  --border:     rgba(28,61,46,0.15);
}

/* ── Base reset ────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--cream) !important;
  font-family: 'Inter', sans-serif;
  color: var(--text);
}

[data-testid="stSidebar"] {
  background: var(--green) !important;
  border-right: none;
}
[data-testid="stSidebar"] > div,
[data-testid="stSidebarUserContent"],
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  padding-top: 0px !important;
  margin-top: 0px !important;
}
[data-testid="stSidebar"] * {
  color: var(--cream) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
  color: rgba(245,242,236,0.75) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: var(--cream) !important;
  font-family: 'Lora', serif;
  font-weight: 500;
}
[data-testid="stSidebar"] hr {
  border-color: rgba(245,242,236,0.15) !important;
}

/* File uploader styling */
[data-testid="stFileUploader"] {
  background: transparent !important;
  border: none !important;
}
[data-testid="stFileUploaderDropzone"] {
  background: var(--white) !important;
  border: 1.5px dashed var(--border) !important;
  border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzone"] * {
  color: var(--green) !important;
}
[data-testid="stFileUploaderDropzone"] button {
  background: var(--cream-mid) !important;
  color: var(--green) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
  background: var(--cream-dark) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
  display: none !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton button {
  background: rgba(245,242,236,0.1) !important;
  color: var(--cream) !important;
  border: 1px solid rgba(245,242,236,0.25) !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.01em;
  transition: background 0.2s, border-color 0.2s;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: rgba(245,242,236,0.2) !important;
  border-color: rgba(245,242,236,0.5) !important;
}

/* Sidebar status badges */
[data-testid="stSidebar"] .stSuccess {
  background: rgba(59,112,87,0.35) !important;
  border: 1px solid rgba(59,112,87,0.5) !important;
  border-radius: 8px;
  color: #A8D5B5 !important;
}
[data-testid="stSidebar"] .stInfo {
  background: rgba(245,242,236,0.08) !important;
  border: 1px solid rgba(245,242,236,0.2) !important;
  border-radius: 8px;
  color: rgba(245,242,236,0.7) !important;
}
[data-testid="stSidebar"] .stWarning {
  background: rgba(180,120,40,0.25) !important;
  border: 1px solid rgba(180,120,40,0.4) !important;
  border-radius: 8px;
}
[data-testid="stSidebar"] .stError {
  background: rgba(192,57,43,0.25) !important;
  border: 1px solid rgba(192,57,43,0.4) !important;
  border-radius: 8px;
}

/* Progress bar in sidebar */
[data-testid="stSidebar"] .stProgress > div > div {
  background: var(--green-light) !important;
}

/* ── Main area ────────────────────── */
.main .block-container {
  max-width: 860px;
  padding: 2.5rem 2rem 6rem;
  margin: 0 auto;
}

/* ── Header ───────────────────────── */
.rag-header {
  display: flex;
  align-items: baseline;
  gap: 14px;
  margin-bottom: 4px;
}
.rag-header h1 {
  font-family: 'Lora', serif;
  font-size: 2rem;
  font-weight: 500;
  color: var(--green);
  letter-spacing: -0.02em;
  margin: 0;
}
.rag-tagline {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 2rem;
  font-weight: 400;
  line-height: 1.6;
}

/* ── Chat bubbles ─────────────────── */
[data-testid="stChatMessage"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}
[data-testid="stChatMessage"][data-testid*="user"] .stChatMessageContent,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stChatMessageContent {
  background: var(--green) !important;
  color: var(--cream) !important;
  border-radius: 18px 18px 4px 18px !important;
  padding: 12px 18px !important;
  max-width: 78%;
  margin-left: auto;
  font-size: 14.5px;
  line-height: 1.65;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) .stChatMessageContent {
  background: var(--white) !important;
  color: var(--text) !important;
  border-radius: 4px 18px 18px 18px !important;
  padding: 14px 18px !important;
  border: 1px solid var(--border) !important;
  max-width: 88%;
  font-size: 14.5px;
  line-height: 1.7;
  box-shadow: 0 1px 6px rgba(28,61,46,0.06);
}
.rag-source-citation {
  font-family: 'Lora', serif !important;
  font-size: 12.5px !important;
  font-style: italic !important;
  color: var(--text-muted) !important;
  margin-top: 8px !important;
  line-height: 1.4 !important;
}
.sidebar-chat-link {
  color: var(--cream) !important;
  text-decoration: none !important;
  display: block !important;
  padding: 8px 12px !important;
  border-radius: 8px !important;
  background: rgba(245,242,236,0.06) !important;
  margin-bottom: 6px !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  transition: background 0.15s, color 0.15s !important;
  border: 1px solid rgba(245,242,236,0.08) !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}
.sidebar-chat-link:hover {
  background: rgba(245,242,236,0.15) !important;
  color: var(--white) !important;
}
div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(.sidebar-spacer) {
  margin-top: auto !important;
  padding-top: 15px !important;
}

/* Custom styling for Reset KB button (red outline warning style) */
button[id="btn_reset_kb"] {
  background: rgba(192,57,43,0.06) !important;
  border: 1.5px solid rgba(192,57,43,0.4) !important;
  color: #ff6b6b !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
}
button[id="btn_reset_kb"]:hover {
  background: rgba(192,57,43,0.15) !important;
  color: #ff4a4a !important;
  border-color: rgba(192,57,43,0.6) !important;
}

/* Custom styling for Clear Chat button (cream/green outline style) */
button[id="btn_clear_chat"] {
  background: transparent !important;
  border: 1.5px solid rgba(245,242,236,0.2) !important;
  color: var(--cream) !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
}
button[id="btn_clear_chat"]:hover {
  background: rgba(245,242,236,0.08) !important;
  color: var(--white) !important;
  border-color: rgba(245,242,236,0.4) !important;
}

/* Avatar icons */
[data-testid="chatAvatarIcon-user"] {
  background: var(--green-light) !important;
  color: var(--cream) !important;
}
[data-testid="chatAvatarIcon-assistant"] {
  background: var(--cream-mid) !important;
  color: var(--green) !important;
}

/* ── Chat input ───────────────────── */
[data-testid="stChatInput"] {
  border: 1.5px solid var(--border) !important;
  border-radius: 14px !important;
  background: var(--white) !important;
  box-shadow: 0 2px 12px rgba(28,61,46,0.08) !important;
  transition: box-shadow 0.2s, border-color 0.2s;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--green-light) !important;
  box-shadow: 0 2px 18px rgba(28,61,46,0.14) !important;
}
[data-testid="stChatInput"] textarea {
  font-family: 'Inter', sans-serif !important;
  font-size: 14.5px !important;
  color: var(--text) !important;
  padding-left: 48px !important;
}
[data-testid="stChatInput"] button {
  background: var(--green) !important;
  color: var(--white) !important;
  border-radius: 10px !important;
}

/* Floating plus button positioning and design over chat input */
div[data-testid="stElementContainer"]:has(#upload-popover-anchor) ~ div:not([data-testid="stChatInput"]):has(button) {
  position: fixed !important;
  bottom: 105px !important;
  z-index: 999999 !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

@media (min-width: 924px) {
  div[data-testid="stElementContainer"]:has(#upload-popover-anchor) ~ div:not([data-testid="stChatInput"]):has(button) {
    left: calc(50% - 430px + 10px) !important;
  }
}

@media (max-width: 923px) {
  div[data-testid="stElementContainer"]:has(#upload-popover-anchor) ~ div:not([data-testid="stChatInput"]):has(button) {
    left: calc(2rem + 10px) !important;
  }
}

div[data-testid="stElementContainer"]:has(#upload-popover-anchor) ~ div:not([data-testid="stChatInput"]):has(button) button {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--green) !important;
  font-size: 26px !important;
  font-weight: 400 !important;
  padding: 0 !important;
  width: 36px !important;
  height: 36px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 50% !important;
  transition: background-color 0.2s, color 0.2s;
  line-height: 1 !important;
}

div[data-testid="stElementContainer"]:has(#upload-popover-anchor) ~ div:not([data-testid="stChatInput"]):has(button) button:hover {
  background-color: rgba(28, 61, 46, 0.08) !important;
  color: var(--green-light) !important;
}

/* Hide Streamlit's default chevron arrow in the popover button */
div[data-testid="stElementContainer"]:has(#upload-popover-anchor) ~ div:not([data-testid="stChatInput"]):has(button) button svg {
  display: none !important;
}

/* ── Expanders (sources) ──────────── */
[data-testid="stExpander"] {
  background: var(--white) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  margin-top: 8px;
}
[data-testid="stExpander"] summary {
  font-size: 13px !important;
  font-weight: 500 !important;
  color: var(--green) !important;
  padding: 10px 14px !important;
}
[data-testid="stExpander"] summary:hover {
  background: var(--cream) !important;
  border-radius: 10px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
  background: #FFFFFF !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover,
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover * {
  color: #000000 !important;
}

/* ── Metrics row ──────────────────── */
[data-testid="metric-container"] {
  background: var(--cream-mid) !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
  border: 1px solid var(--border) !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
  font-size: 11px !important;
  color: var(--text-muted) !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-size: 17px !important;
  font-weight: 600 !important;
  color: var(--green) !important;
}

/* ── Spinner ──────────────────────── */
.stSpinner > div {
  border-top-color: var(--green) !important;
}

/* ── Scrollbar ────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--cream-mid); }
::-webkit-scrollbar-thumb { background: var(--cream-dark); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--green-light); }

/* ── Sidebar config expander ──────── */
[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: rgba(245,242,236,0.06) !important;
  border: 1px solid rgba(245,242,236,0.15) !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
  color: var(--cream) !important;
  font-size: 12px !important;
}

/* ── Text areas in source viewer ──── */
.stTextArea textarea {
  background: var(--cream) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  color: var(--text-muted) !important;
  font-family: 'Inter', sans-serif !important;
}

/* ── Hide Streamlit branding ──────── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Remove/Hide sidebar collapse controls ── */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
  display: none !important;
}

/* ── Feedback buttons ─────────────── */
.feedback-btn button {
  background: transparent !important;
  color: var(--text-muted) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 12px !important;
  font-weight: 400 !important;
  padding: 4px 12px !important;
  min-height: 0 !important;
  height: auto !important;
  line-height: 1.4 !important;
  transition: background 0.15s, border-color 0.15s, color 0.15s !important;
}
.feedback-btn button:hover {
  background: var(--cream-mid) !important;
  border-color: var(--green-light) !important;
  color: var(--green) !important;
}

/* ── Login form ───────────────────── */
.login-container {
  max-width: 380px;
  margin: 80px auto;
  padding: 40px 36px;
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(28,61,46,0.08);
}
.login-container h2 {
  font-family: 'Lora', serif;
  color: var(--green);
  font-size: 1.6rem;
  font-weight: 500;
  margin-bottom: 6px;
  text-align: center;
}
.login-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 28px;
}
.login-container .stTextInput input {
  background: var(--cream) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  color: var(--text) !important;
}
.login-container .stButton button {
  background: var(--green) !important;
  color: var(--cream) !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  width: 100%;
  padding: 10px 0 !important;
  transition: background 0.2s !important;
}
.login-container .stButton button:hover {
  background: var(--green-mid) !important;
}

/* ── Admin panel cards ────────────── */
.admin-section {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}
.admin-section h3 {
  font-family: 'Lora', serif;
  color: var(--green);
  font-size: 1.15rem;
  font-weight: 500;
  margin-bottom: 14px;
}
.admin-badge-ready {
  display: inline-block;
  background: rgba(59,112,87,0.15);
  color: var(--green-light);
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 12px;
  border: 1px solid rgba(59,112,87,0.3);
}
.admin-badge-pending {
  display: inline-block;
  background: rgba(180,120,40,0.12);
  color: #B47828;
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 12px;
  border: 1px solid rgba(180,120,40,0.3);
}

/* ── Page link styling in sidebar ─── */
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
  background: rgba(245,242,236,0.08) !important;
  border: 1px solid rgba(245,242,236,0.15) !important;
  border-radius: 8px !important;
  color: var(--cream) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  transition: background 0.2s !important;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
  background: rgba(245,242,236,0.18) !important;
}
</style>
"""

# ── Animated background canvas (subtle moving particles) ──────────────────────
ANIMATED_BG = """
<canvas id="rag-bg" style="
  position:fixed; top:0; left:0; width:100%; height:100%;
  pointer-events:none; z-index:0; opacity:0.45;
"></canvas>
<script>
(function(){
  const canvas = document.getElementById('rag-bg');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, pts;

  function resize(){
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function init(){
    pts = Array.from({length: 38}, () => ({
      x: Math.random()*W, y: Math.random()*H,
      vx:(Math.random()-0.5)*0.28, vy:(Math.random()-0.5)*0.28,
      r: 1.5 + Math.random()*2.5,
      a: 0.3 + Math.random()*0.4
    }));
  }

  function draw(){
    ctx.clearRect(0,0,W,H);
    // Connection lines
    for(let i=0;i<pts.length;i++){
      for(let j=i+1;j<pts.length;j++){
        const dx=pts[i].x-pts[j].x, dy=pts[i].y-pts[j].y;
        const dist=Math.sqrt(dx*dx+dy*dy);
        if(dist<160){
          ctx.beginPath();
          ctx.moveTo(pts[i].x,pts[i].y);
          ctx.lineTo(pts[j].x,pts[j].y);
          ctx.strokeStyle=`rgba(28,61,46,${0.06*(1-dist/160)})`;
          ctx.lineWidth=0.8;
          ctx.stroke();
        }
      }
    }
    // Dots
    pts.forEach(p=>{
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(28,61,46,${p.a})`;
      ctx.fill();
      p.x+=p.vx; p.y+=p.vy;
      if(p.x<0||p.x>W) p.vx*=-1;
      if(p.y<0||p.y>H) p.vy*=-1;
    });
    requestAnimationFrame(draw);
  }

  resize();
  init();
  draw();
  window.addEventListener('resize', ()=>{ resize(); init(); });
})();
</script>
"""
