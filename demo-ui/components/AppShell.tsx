import Head from "next/head";
import Link from "next/link";
import { ReactNode } from "react";

const links = [
  ["/compare", "Compare"],
  ["/timeline", "Timeline"],
  ["/heatmap", "Heatmap"]
] as const;

export function AppShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <>
      <Head><title>{title} · Adaptive Memory</title></Head>
      <main className="mx-auto min-h-screen max-w-6xl px-5 py-8 sm:px-8">
        <header className="mb-10 flex flex-col gap-5 border-b border-ink/20 pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-teal">Tutor infrastructure demo</p>
            <h1 className="font-serif text-3xl font-bold tracking-tight text-ink sm:text-4xl">Adaptive Memory</h1>
          </div>
          <nav aria-label="Demo pages" className="flex gap-4 text-sm font-semibold">
            {links.map(([href, label]) => <Link key={href} className="underline decoration-2 underline-offset-4 hover:text-coral" href={href}>{label}</Link>)}
          </nav>
        </header>
        {children}
      </main>
    </>
  );
}
