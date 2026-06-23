"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: { client_id: string; callback: (response: { credential: string }) => void }) => void;
          renderButton: (element: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

export default function LoginPage() {
  const router = useRouter();
  const { user, login, register, googleLogin } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const googleButton = useRef<HTMLDivElement>(null);
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

  useEffect(() => {
    if (user) router.replace("/dashboard");
  }, [user, router]);

  useEffect(() => {
    if (!googleClientId || !googleButton.current) return;
    const render = () => {
      if (!window.google || !googleButton.current) return;
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async ({ credential }) => {
          try {
            setBusy(true);
            await googleLogin(credential);
            router.push("/dashboard");
          } catch (err) {
            setError(err instanceof Error ? err.message : "Google 로그인에 실패했습니다.");
          } finally {
            setBusy(false);
          }
        },
      });
      googleButton.current.innerHTML = "";
      window.google.accounts.id.renderButton(googleButton.current, {
        theme: "outline",
        size: "large",
        width: 360,
        text: "continue_with",
        locale: "ko",
      });
    };
    const existing = document.querySelector<HTMLScriptElement>('script[src="https://accounts.google.com/gsi/client"]');
    if (existing) {
      existing.addEventListener("load", render, { once: true });
      render();
      return;
    }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = render;
    document.head.appendChild(script);
  }, [googleClientId, googleLogin, router]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") await register(name, email, password);
      else await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "로그인에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page-shell login-shell">
      <section className="login-copy">
        <p className="eyebrow">CROSSVIEW ACCOUNT</p>
        <h1>시청 기록을 나만의 리포트로 연결하세요.</h1>
        <p>로그인 후 확장 프로그램을 연결하면 영상별 편향 신호, 다른 관점 탐색, 주간·월간 리포트가 사용자별로 저장됩니다.</p>
        <div className="login-benefits">
          <span>✓ 사용자별 시청 기록</span>
          <span>✓ 웹·확장 프로그램 연결</span>
          <span>✓ 이메일·Slack·Discord 리포트</span>
        </div>
      </section>
      <section className="panel login-panel">
        <div className="mode-tabs">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>로그인</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>회원가입</button>
        </div>
        <form className="form-stack" onSubmit={submit}>
          {mode === "register" && <label>이름<input value={name} onChange={(event) => setName(event.target.value)} required minLength={1} /></label>}
          <label>이메일<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
          <label>비밀번호<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} /></label>
          {error && <p className="form-error">{error}</p>}
          <button className="primary-button form-submit" disabled={busy}>{busy ? "처리 중…" : mode === "register" ? "계정 만들기" : "로그인"}</button>
        </form>
        {googleClientId && <><div className="form-divider"><span>또는</span></div><div ref={googleButton} className="google-button" /></>}
        {!googleClientId && <p className="form-hint">Google 로그인을 사용하려면 frontend/.env.local과 backend/.env에 Google Client ID를 설정하세요.</p>}
      </section>
    </main>
  );
}
