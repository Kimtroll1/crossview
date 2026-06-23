"use client";

import Link from "next/link";
import { useAuth } from "./AuthProvider";

export function NavBar() {
  const { user, loading, logout } = useAuth();
  return (
    <header className="site-header">
      <div className="nav-shell">
        <Link className="brand" href="/">CrossView</Link>
        <nav>
          <Link href="/dashboard">리포트</Link>
          <Link href="/history">분석 기록</Link>
          <Link href="/explore">다관점 자료</Link>
          <Link href="/settings">설정</Link>
          {!loading && (user ? <button className="nav-button" onClick={logout}>{user.name || "로그아웃"}</button> : <Link href="/login">로그인</Link>)}
        </nav>
      </div>
    </header>
  );
}
