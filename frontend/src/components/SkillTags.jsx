import React from "react";

export default function SkillTags({ title, tags, tone = "neutral" }) {
  if (!tags || tags.length === 0) return null;
  return (
    <div className="tag-block">
      <div className="tag-title">{title}</div>
      <div className="tag-row">
        {tags.map((t) => (
          <span key={t} className={`tag tag-${tone}`}>{t}</span>
        ))}
      </div>
    </div>
  );
}
