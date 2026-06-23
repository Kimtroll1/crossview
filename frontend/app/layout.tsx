import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/AuthProvider";
import { NavBar } from "@/components/NavBar";

export const metadata: Metadata = {
  title: "CrossView",
  description: "유튜브 관점 분석, 다관점 탐색, 개인 미디어 소비 리포트",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <AuthProvider>
          <NavBar />
          {children}
        </AuthProvider>
        <footer className="site-footer">CrossView는 판단을 대신하지 않고, 더 많은 근거와 관점을 확인하도록 돕습니다.</footer>
      </body>
    </html>
  );
}
