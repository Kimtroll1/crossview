"use client";

import { useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { ResourceCards } from "@/components/ResourceCards";
import { reportApi, type Report, type Resource } from "@/lib/api";

export default function ExplorePage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([reportApi.report("weekly"), reportApi.report("monthly")])
      .then((reports: Report[]) => {
        const seen = new Set<string>();
        setResources(reports.flatMap((item) => item.recommendedResources).filter((item) => item.url && !seen.has(item.url) && seen.add(item.url)));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "자료를 불러오지 못했습니다."));
  }, []);
  return (
    <AuthGate>
      <main className="page-shell">
        <section className="report-heading"><div><p className="eyebrow">MULTI-PERSPECTIVE EXPLORER</p><h1>다른 관점과 원문 찾기</h1><p>실제 YouTube 검색 결과와 Google Search grounding 출처 중 현재 시청 흐름을 보완할 자료를 모았습니다.</p></div></section>
        {error && <div className="error-banner">{error}</div>}
        <section className="panel"><ResourceCards resources={resources} /></section>
      </main>
    </AuthGate>
  );
}
