import React from "react";

/**
 * Analog-instrument style gauge — the page's signature element.
 * Renders the ATS score as a needle sweep across a 270° arc with tick marks,
 * evoking a diagnostic scanner reading rather than a generic progress ring.
 */
export default function ScoreGauge({ score = 0, label = "ATS MATCH" }) {
  const clamped = Math.max(0, Math.min(100, score));
  const angle = -135 + (clamped / 100) * 270; // -135deg to +135deg sweep
  const ticks = Array.from({ length: 12 }, (_, i) => -135 + (i * 270) / 11);

  const color =
    clamped >= 75 ? "var(--good)" : clamped >= 45 ? "var(--signal)" : "var(--bad)";

  return (
    <div className="gauge">
      <svg viewBox="0 0 200 200" width="220" height="220">
        <circle cx="100" cy="100" r="88" fill="none" stroke="var(--line)" strokeWidth="1" />
        {ticks.map((deg, i) => (
          <line
            key={i}
            x1="100"
            y1="18"
            x2="100"
            y2={i % 3 === 0 ? "30" : "26"}
            stroke="var(--text-dim)"
            strokeWidth="1.5"
            transform={`rotate(${deg} 100 100)`}
          />
        ))}
        <line
          x1="100"
          y1="100"
          x2="100"
          y2="34"
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          transform={`rotate(${angle} 100 100)`}
          style={{ transition: "transform 0.8s cubic-bezier(.2,.8,.2,1)" }}
        />
        <circle cx="100" cy="100" r="6" fill={color} />
      </svg>
      <div className="gauge-readout">
        <span className="gauge-number" style={{ color }}>{clamped.toFixed(0)}</span>
        <span className="gauge-unit">/ 100</span>
      </div>
      <div className="gauge-label">{label}</div>
    </div>
  );
}
