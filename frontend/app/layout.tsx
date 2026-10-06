import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppLayout } from "../components/layout/AppLayout";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Spotter Freight Rate Predictor | Enterprise ML SaaS",
  description:
    "Production-grade Machine Learning spot freight cost prediction engine powered by LightGBM, CatBoost & XGBoost Ensemble.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} min-h-full bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 antialiased`}>
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
