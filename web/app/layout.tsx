import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AEDIFICA — Workspace",
  description: "Aedifica — ArchiOS Suisse: regulatory/project intelligence workspace.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
