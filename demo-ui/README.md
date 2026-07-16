# Demo UI (placeholder)

Not yet scaffolded. Per docs/handover_doc.md Day 4, this should contain:

- `compare.tsx` — memory ON vs memory OFF panel (the strongest single demo beat)
- `timeline.tsx` — 3-checkpoint story + insight-log feed for one confusable pair
- `heatmap.tsx` — multi-pair overview
- `widget/` — embeddable script/iframe version (stretch goal, see design_doc.md §5)

Recommended stack: Next.js + Tailwind, deployed to Vercel (see docs/design_doc.md §8
for the hosting rationale — scale-to-zero, no VM).
