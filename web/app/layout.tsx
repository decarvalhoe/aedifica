import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AEDIFICA — ArchiOS Suisse",
  description: "Aedifica — l'assistant opérationnel de l'architecte SIA.",
  icons: {
    icon: [{ url: "/assets/favicon.svg", type: "image/svg+xml" }],
    shortcut: ["/assets/favicon.svg"],
    apple: [{ url: "/assets/favicon.svg", type: "image/svg+xml" }],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
