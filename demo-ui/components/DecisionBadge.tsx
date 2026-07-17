import { Insight } from "../lib/api";

const styles: Record<Insight["decision"], string> = {
  escalate: "bg-coral/15 text-coral",
  retire: "bg-teal/15 text-teal",
  no_change: "bg-sand/30 text-ink"
};

export function DecisionBadge({ decision }: { decision: Insight["decision"] }) {
  return <span className={`inline-flex rounded-sm px-2 py-1 text-xs font-bold uppercase tracking-wide ${styles[decision]}`}>{decision.replace("_", " ")}</span>;
}
