import type { Metadata } from "next";
import { Inter, Crimson_Text } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });
const crimson = Crimson_Text({
  weight: ['400', '600', '700'],
  subsets: ["latin"],
  variable: '--font-crimson'
});

export const metadata: Metadata = {
  title: "IndoGovRAG - Indonesian Government Legal Database",
  description: "Professional legal research platform for Indonesian government regulations and policies",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id">
      <body className={`${inter.className} ${crimson.variable} bg-slate-50 text-slate-900 antialiased`}>
        {children}
      </body>
    </html>
  );
}
