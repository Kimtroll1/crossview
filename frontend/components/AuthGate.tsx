"use client";

import Link from "next/link";
import { useAuth } from "./AuthProvider";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <main className="page-shell"><div className="empty-state">사용자 정보를 불러오는 중입니다.</div></main>;
  if (!user) return (
    <main className="page-shell auth-required">
      <div className="panel auth-card">
        <p className="eyebrow">LOGIN REQUIRED</p>
        <h1>개인 리포트를 보려면 로그인하세요.</h1>
        <p>로그인하면 확장 프로그램의 시청 기록이 사용자 계정에 저장되고 주간·월간 리포트를 받을 수 있습니다.</p>
        <Link className="primary-button inline-button" href="/login">로그인하기</Link>
      </div>
    </main>
  );
  return <>{children}</>;
}
