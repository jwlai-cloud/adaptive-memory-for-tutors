import { ReactNode } from "react";

export function AsyncPanel({ loading, error, children }: { loading: boolean; error: string | null; children: ReactNode }) {
  if (loading) return <div aria-busy="true" className="animate-pulse border border-ink/15 bg-white p-6 text-sm">Loading live memory…</div>;
  if (error) return <div role="alert" className="border-l-4 border-coral bg-white p-5 text-sm text-ink"><strong>Live API unavailable.</strong><br />{error}</div>;
  return <>{children}</>;
}
