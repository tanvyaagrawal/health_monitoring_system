import { useState, useEffect, useRef, useCallback } from "react";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";

// ── Config ───────────────────────────────────────────────────────────────────
const WS_URL     = "ws://10.55.121.75:8765";   // ← replace with your Pi's IP
const MAX_POINTS = 120;

// ── Alert display config ──────────────────────────────────────────────────────
const ALERT_META = {
  hr_low:    { label: "LOW HEART RATE",      emoji: "🔴", color: "#ff4455" },
  hr_high:   { label: "HIGH HEART RATE",     emoji: "🔴", color: "#ff4455" },
  spo2_low:  { label: "LOW BLOOD OXYGEN",    emoji: "🔴", color: "#ff4455" },
  temp_high: { label: "HIGH TEMPERATURE",    emoji: "🌡️", color: "#ff8833" },
  temp_low:  { label: "LOW TEMPERATURE",     emoji: "🌡️", color: "#33aaff" },
};

// ── Colour tokens ─────────────────────────────────────────────────────────────
const C = {
  bg:       "#04080a",
  panel:    "#080f12",
  panelAlt: "#0b1619",
  border:   "#0d2530",
  green:    "#00e87a",
  cyan:     "#00d4ff",
  amber:    "#ffaa22",
  red:      "#ff3344",
  orange:   "#ff7733",
  blue:     "#3399ff",
  muted:    "#1a3a46",
  text:     "#b8dce6",
  textDim:  "#3a6878",
};

// ── WebSocket hook ────────────────────────────────────────────────────────────
function useWebSocket(url) {
  const [status,  setStatus]  = useState("disconnected");
  const [lastMsg, setLastMsg] = useState(null);
  const wsRef    = useRef(null);
  const retryRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen    = ()  => { setStatus("connected"); clearTimeout(retryRef.current); };
    ws.onclose   = ()  => { setStatus("disconnected"); retryRef.current = setTimeout(connect, 3000); };
    ws.onerror   = ()  => setStatus("error");
    ws.onmessage = (e) => { try { setLastMsg(JSON.parse(e.data)); } catch {} };
  }, [url]);

  useEffect(() => {
    connect();
    return () => { clearTimeout(retryRef.current); wsRef.current?.close(); };
  }, [connect]);

  return { status, lastMsg };
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function tempStatus(t) {
  if (t === null) return { label: "NO SENSOR", color: C.textDim };
  if (t > 38.5)   return { label: "⚠ FEVER",          color: C.orange };
  if (t < 35.0)   return { label: "⚠ HYPOTHERMIA",     color: C.blue };
  if (t > 37.5)   return { label: "SLIGHTLY ELEVATED", color: C.amber };
  return            { label: "NORMAL",                  color: C.green };
}
function hrStatus(hr) {
  if (hr === -1)   return { label: "CALIBRATING…",   color: C.textDim };
  if (hr < 45)     return { label: "⚠ BRADYCARDIA",  color: C.red };
  if (hr > 130)    return { label: "⚠ TACHYCARDIA",  color: C.red };
  return             { label: "NORMAL SINUS",         color: C.green };
}
function spo2Status(s) {
  if (s === -1)    return { label: "CALIBRATING…",  color: C.textDim };
  if (s < 90)      return { label: "⚠ HYPOXEMIA",   color: C.red };
  if (s < 95)      return { label: "⚠ LOW",         color: C.orange };
  return             { label: "NORMAL",              color: C.green };
}

// ── Components ────────────────────────────────────────────────────────────────

function StatusPill({ status }) {
  const map = {
    connected:    { color: C.green,  label: "LIVE" },
    connecting:   { color: C.amber,  label: "CONNECTING…" },
    disconnected: { color: C.red,    label: "DISCONNECTED" },
    error:        { color: C.red,    label: "ERROR" },
  };
  const { color, label } = map[status] ?? map.disconnected;
  return (
    <div style={{ display:"flex", alignItems:"center", gap:8 }}>
      <div style={{
        width:8, height:8, borderRadius:"50%",
        background: color, boxShadow: `0 0 8px ${color}`,
        animation: status === "connected" ? "blink 1.8s ease-in-out infinite" : "none",
      }}/>
      <span style={{ fontFamily:"'Space Mono',monospace", fontSize:10, color, letterSpacing:2 }}>
        {label}
      </span>
    </div>
  );
}

function BigMetric({ label, value, unit, color, sublabel, sublabelColor, icon }) {
  const displayVal = value === -1 || value === null ? "---" : String(value);
  return (
    <div style={{
      background: C.panel,
      border: `1px solid ${C.border}`,
      borderRadius: 3,
      padding: "18px 22px",
      position: "relative", overflow: "hidden",
    }}>
      <div style={{ position:"absolute", top:0, left:0, width:32, height:2, background:color, opacity:0.8 }}/>
      <div style={{
        fontFamily:"'Space Mono',monospace",
        fontSize:9, letterSpacing:3, color:C.textDim, marginBottom:6,
      }}>{icon}  {label}</div>
      <div style={{ display:"flex", alignItems:"flex-end", gap:5, lineHeight:1 }}>
        <span style={{
          fontFamily:"'Orbitron',monospace",
          fontSize:48, fontWeight:900, color,
          textShadow:`0 0 20px ${color}66`, letterSpacing:-2,
        }}>{displayVal}</span>
        <span style={{ fontFamily:"'Space Mono',monospace", fontSize:13, color:C.textDim, marginBottom:9 }}>
          {unit}
        </span>
      </div>
      {sublabel && (
        <div style={{
          fontFamily:"'Space Mono',monospace",
          fontSize:9, letterSpacing:2, marginTop:5,
          color: sublabelColor ?? C.textDim,
        }}>{sublabel}</div>
      )}
    </div>
  );
}

function RawValue({ label, value, color }) {
  return (
    <div style={{
      background:C.panel, border:`1px solid ${C.border}`,
      borderRadius:3, padding:"12px 18px",
    }}>
      <div style={{ fontFamily:"'Space Mono',monospace", fontSize:8, letterSpacing:3, color:C.textDim, marginBottom:4 }}>
        {label}
      </div>
      <div style={{ fontFamily:"'Orbitron',monospace", fontSize:20, color, textShadow:`0 0 12px ${color}55` }}>
        {value == null ? "---" : value.toLocaleString()}
      </div>
    </div>
  );
}

function MiniWave({ data, color, label }) {
  return (
    <div style={{ background:C.panel, border:`1px solid ${C.border}`, borderRadius:3, padding:"14px 18px" }}>
      <div style={{ fontFamily:"'Space Mono',monospace", fontSize:8, letterSpacing:3, color:C.textDim, marginBottom:8 }}>
        {label}
      </div>
      <div style={{ height:64 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{top:2,right:0,bottom:2,left:0}}>
            <YAxis domain={["auto","auto"]} hide />
            <Line type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} dot={false} isAnimationActive={false}/>
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ECGStrip({ data }) {
  return (
    <div style={{ background:C.panel, border:`1px solid ${C.border}`, borderRadius:3, padding:"14px 18px" }}>
      <div style={{ fontFamily:"'Space Mono',monospace", fontSize:8, letterSpacing:3, color:C.textDim, marginBottom:8 }}>
        ◉  IR PHOTOPLETHYSMOGRAM — LIVE WAVEFORM
      </div>
      <div style={{ position:"relative", height:88 }}>
        <svg style={{ position:"absolute", inset:0, width:"100%", height:"100%" }}>
          {[0,0.33,0.66,1].map(f => (
            <line key={f} x1="0" y1={`${f*100}%`} x2="100%" y2={`${f*100}%`}
              stroke={C.muted} strokeWidth="0.5" strokeDasharray="4,10"/>
          ))}
        </svg>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{top:4,right:0,bottom:4,left:0}}>
            <YAxis domain={["auto","auto"]} hide />
            <Line type="monotone" dataKey="v" stroke={C.green} strokeWidth={2} dot={false} isAnimationActive={false}/>
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function AlertBadge({ alertKey }) {
  const meta = ALERT_META[alertKey];
  if (!meta) return null;
  return (
    <div style={{
      display:"flex", alignItems:"center", gap:8,
      background:`${meta.color}18`,
      border:`1px solid ${meta.color}55`,
      borderRadius:3, padding:"8px 14px",
      animation:"alertPulse 2s ease-in-out infinite",
    }}>
      <span style={{ fontSize:14 }}>{meta.emoji}</span>
      <span style={{ fontFamily:"'Space Mono',monospace", fontSize:9, letterSpacing:2, color:meta.color }}>
        {meta.label}
      </span>
    </div>
  );
}

function AlertLog({ log }) {
  if (log.length === 0) return null;
  return (
    <div style={{ background:C.panel, border:`1px solid ${C.border}`, borderRadius:3, padding:"14px 18px" }}>
      <div style={{ fontFamily:"'Space Mono',monospace", fontSize:8, letterSpacing:3, color:C.textDim, marginBottom:10 }}>
        📋  ALERT LOG  (last {log.length})
      </div>
      {log.slice().reverse().map((entry, i) => (
        <div key={i} style={{
          display:"flex", gap:12, alignItems:"flex-start",
          padding:"6px 0",
          borderBottom: i < log.length - 1 ? `1px solid ${C.border}` : "none",
        }}>
          <span style={{ fontFamily:"'Space Mono',monospace", fontSize:8, color:C.textDim, whiteSpace:"nowrap" }}>
            {entry.time}
          </span>
          <span style={{ fontFamily:"'Space Mono',monospace", fontSize:8, color: ALERT_META[entry.key]?.color ?? C.text }}>
            {ALERT_META[entry.key]?.emoji} {ALERT_META[entry.key]?.label ?? entry.key}
          </span>
          <span style={{ fontFamily:"'Space Mono',monospace", fontSize:8, color:C.textDim }}>
            {entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  const { status, lastMsg } = useWebSocket(WS_URL);

  const irData  = useRef([]);
  const redData = useRef([]);
  const [, forceRender] = useState(0);

  const [vitals, setVitals] = useState({
    hr: -1, spo2: -1.0, temp: null,
    ir: null, red: null, ready: false,
    activeAlerts: [],
  });

  const [alertLog, setAlertLog] = useState([]);

  useEffect(() => {
    if (!lastMsg) return;
    const { hr, spo2, temp, ir, red, ready, active_alerts, fired_alerts } = lastMsg;

    irData.current  = [...irData.current,  { v: ir  }].slice(-MAX_POINTS);
    redData.current = [...redData.current, { v: red }].slice(-MAX_POINTS);

    setVitals({ hr, spo2, temp, ir, red, ready, activeAlerts: active_alerts ?? [] });

    // Append newly fired alerts to the log
    if (fired_alerts?.length) {
      const timeStr = new Date().toLocaleTimeString();
      const entries = fired_alerts.map(key => ({
        key,
        time: timeStr,
        value: key.startsWith("hr")    ? `${hr} bpm`
             : key.startsWith("spo2")  ? `${spo2}%`
             : `${temp}°C`,
      }));
      setAlertLog(prev => [...prev, ...entries].slice(-20));
    }

    forceRender(n => n + 1);
  }, [lastMsg]);

  const hrStat   = hrStatus(vitals.hr);
  const spo2Stat = spo2Status(vitals.spo2);
  const tempStat = tempStatus(vitals.temp);

  const hasAlerts = vitals.activeAlerts.length > 0;

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');
        *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
        html, body { background:${C.bg}; min-height:100vh; }
        ::-webkit-scrollbar { width:4px; background:${C.bg}; }
        ::-webkit-scrollbar-thumb { background:${C.muted}; }

        @keyframes blink {
          0%,100% { opacity:1; }
          50%      { opacity:0.25; }
        }
        @keyframes alertPulse {
          0%,100% { opacity:1; }
          50%      { opacity:0.6; }
        }
        @keyframes scanline {
          from { transform:translateY(-100%); }
          to   { transform:translateY(100vh); }
        }
      `}</style>

      {/* CRT scanline overlay */}
      <div style={{
        position:"fixed", inset:0, pointerEvents:"none", zIndex:999,
        background:`repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,200,100,0.012) 2px, rgba(0,200,100,0.012) 4px)`,
      }}/>

      <div style={{
        maxWidth:900, margin:"0 auto",
        padding:"20px 20px 40px",
        minHeight:"100vh",
        color: C.text,
      }}>

        {/* ── Header ── */}
        <div style={{
          display:"flex", justifyContent:"space-between", alignItems:"flex-start",
          borderBottom:`1px solid ${C.border}`, paddingBottom:16, marginBottom:20,
        }}>
          <div>
            <div style={{
              fontFamily:"'Orbitron',monospace",
              fontSize:12, fontWeight:700, letterSpacing:5,
              color:C.green, textShadow:`0 0 20px ${C.green}55`,
            }}>
              VITAL SIGNS MONITOR
            </div>
            <div style={{ fontFamily:"'Space Mono',monospace", fontSize:8, color:C.textDim, letterSpacing:3, marginTop:4 }}>
              MAX30102 · DS18B20 · RASPBERRY PI · I²C + 1-WIRE
            </div>
          </div>
          <div style={{ display:"flex", flexDirection:"column", alignItems:"flex-end", gap:6 }}>
            <StatusPill status={status} />
            <div style={{ fontFamily:"'Space Mono',monospace", fontSize:8, color:C.textDim, letterSpacing:2 }}>
              {new Date().toLocaleString()}
            </div>
          </div>
        </div>

        {/* ── Active alert banner ── */}
        {hasAlerts && (
          <div style={{
            background:`${C.red}12`,
            border:`1px solid ${C.red}44`,
            borderRadius:3, padding:"10px 16px", marginBottom:16,
          }}>
            <div style={{ fontFamily:"'Space Mono',monospace", fontSize:9, color:C.red, letterSpacing:2, marginBottom:8 }}>
              🚨 ACTIVE ALERTS — TELEGRAM NOTIFICATION SENT
            </div>
            <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
              {vitals.activeAlerts.map(k => <AlertBadge key={k} alertKey={k} />)}
            </div>
          </div>
        )}

        {/* ── Calibrating notice ── */}
        {!vitals.ready && status === "connected" && (
          <div style={{
            background:"#1a1a08", border:`1px solid ${C.amber}33`,
            borderRadius:3, padding:"9px 14px", marginBottom:16,
            fontFamily:"'Space Mono',monospace", fontSize:9, color:C.amber, letterSpacing:2,
          }}>
            ⏳ CALIBRATING — PLACE FINGER FIRMLY ON SENSOR AND HOLD STILL…
          </div>
        )}

        {/* ── Main metric cards ── */}
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:10, marginBottom:10 }}>
          <BigMetric
            label="HEART RATE" icon="♥️"
            value={vitals.hr} unit="bpm"
            color={hrStat.color}
            sublabel={hrStat.label} sublabelColor={hrStat.color}
          />
          <BigMetric
            label="BLOOD OXYGEN" icon="◎"
            value={vitals.spo2 === -1 ? -1 : vitals.spo2} unit="%"
            color={spo2Stat.color}
            sublabel={spo2Stat.label} sublabelColor={spo2Stat.color}
          />
          <BigMetric
            label="TEMPERATURE" icon="🌡"
            value={vitals.temp ?? -1} unit="°C"
            color={tempStat.color}
            sublabel={tempStat.label} sublabelColor={tempStat.color}
          />
        </div>

        {/* ── Raw ADC values ── */}
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:10 }}>
          <RawValue label="RAW IR  (18-BIT ADC)" value={vitals.ir}  color={C.green} />
          <RawValue label="RAW RED (18-BIT ADC)" value={vitals.red} color={C.red} />
        </div>

        {/* ── IR waveform strip ── */}
        <div style={{ marginBottom:10 }}>
          <ECGStrip data={irData.current} />
        </div>

        {/* ── Mini waveform charts ── */}
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:10 }}>
          <MiniWave data={irData.current}  color={C.green} label="▲ IR CHANNEL" />
          <MiniWave data={redData.current} color={C.red}   label="▲ RED CHANNEL" />
        </div>

        {/* ── Alert log ── */}
        {alertLog.length > 0 && (
          <div style={{ marginBottom:10 }}>
            <AlertLog log={alertLog} />
          </div>
        )}

        {/* ── Footer ── */}
        <div style={{
          borderTop:`1px solid ${C.border}`, paddingTop:12, marginTop:4,
          display:"flex", justifyContent:"space-between",
          fontFamily:"'Space Mono',monospace", fontSize:8, color:C.textDim, letterSpacing:2,
        }}>
          <span>25 Hz EFFECTIVE · 4× AVG · ALERT PERSIST 15s · COOLDOWN 10min</span>
          <span>{WS_URL}</span>
        </div>

      </div>
    </>
  );
}