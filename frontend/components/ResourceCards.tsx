"use client";

import { reportApi, type Resource } from "@/lib/api";

export function ResourceCards({ resources, limit }: { resources: Resource[]; limit?: number }) {
  const visible = typeof limit === "number" ? resources.slice(0, limit) : resources;
  if (!visible.length) return <div className="empty-inline">아직 실제 검색 자료가 없습니다. YouTube API와 Gemini 검색 설정을 확인해주세요.</div>;
  return (
    <div className="resource-grid">
      {visible.map((item, index) => (
        <a
          className="resource-card"
          href={item.url}
          target="_blank"
          rel="noreferrer"
          key={`${item.url}-${index}`}
          onClick={() => { if (item.id) reportApi.recordClick(item.id).catch(() => undefined); }}
        >
          <div className="resource-thumb">{item.thumbnailUrl ? <img src={item.thumbnailUrl} alt="" /> : <span>{item.type === "youtube" ? "▶" : item.type === "official" ? "📄" : "📰"}</span>}</div>
          <div>
            <div className="resource-meta"><span>{item.stanceLabel}</span><em>{item.source}</em></div>
            <h3>{item.title}</h3>
            <p>{item.recommendationReason || item.summary}</p>
            <small>관련성 {Math.round(item.relevanceScore)} · 신뢰 신호 {Math.round(item.credibilityScore)}</small>
          </div>
        </a>
      ))}
    </div>
  );
}
