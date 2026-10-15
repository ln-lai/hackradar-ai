import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HackRadar AI — Find your next great build",
  description: "Find hackathons that fit your interests. Transparent matching, honest sources, and a plan to show up ready.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
