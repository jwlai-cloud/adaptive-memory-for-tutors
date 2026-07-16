# Handover Document: Adaptive Memory for Tutors
### For whoever picks up the build (including a future-you after a break)

**Companion doc:** `design_doc.md` (read that first for the *why*; this doc is the *how/what's-left*)
**Architecture:** `architecture.mermaid`

---

## 1. One-paragraph summary

We're building a pluggable memory + insight layer for tutoring agents, using Zep/Graphiti (managed, existing product) as the temporal memory substrate and a GPT-5.6 reasoning layer (our actual built code) on top that decides pedagogical actions from confusion patterns. The hiragana/katakana confusable-pairs case study is a demo illustration, not the product — the product is the engine, packaged as a REST API + MCP server + embeddable widget. Target: OpenAI Build Week, Education track, deadline **Jul 21, 2026, 5:00pm PDT**.

---

## 2. Accounts / credentials needed before starting

| Service | Purpose | Notes |
|---|---|---|
| Zep Cloud account | Memory substrate | Free tier, no credit card required; get API key from dashboard |
| OpenAI API key | GPT-5.6 for insight reasoning | Requested via OpenAI Build Week resources tab — free Codex credits available, request before Jul 17 12:00pm PT cutoff if that deadline still applies, check current status |
| Vercel/Netlify account | Frontend hosting | Free tier sufficient |
| AWS or GCP account | Backend serverless (Lambda / Cloud Run) | Free tier sufficient at demo scale |
| GitHub repo (public) | Submission requirement | Must be public with clear README; MIT or Apache 2.0 license recommended |
| YouTube account | Demo video hosting | Video must be public, under 3 minutes |

---

## 3. Repo structure (proposed)

```
adaptive-memory-for-tutors/
├── README.md                  # the "quickstart as a tutor builder" pitch — see §6
├── design_doc.md
├── architecture.mermaid
├── engine/
│   ├── schema.py               # ConceptPair, ConfusionEvent, InsightLog models
│   ├── zep_client.py           # thin wrapper over Zep SDK, tenant/user scoping
│   ├── insight_engine.py       # GPT-5.6 call: reads graph state -> decision + reasoning
│   └── seed.py                 # synthetic history generator (with re-run guard!)
├── api/
│   ├── rest/                   # REST endpoints
│   └── mcp_server/              # MCP tool definitions
├── demo-ui/                    # Next.js (or similar) frontend
│   ├── pages/
│   │   ├── compare.tsx          # memory ON vs OFF panel
│   │   ├── timeline.tsx         # 3-checkpoint story + insight-log feed
│   │   └── heatmap.tsx          # multi-pair overview
│   └── widget/                  # embeddable script/iframe version
└── seed-data/
    ├── domain-japanese-kana.json
    └── domain-chemistry-notation.json   # second domain, prove genericness
```

---

## 4. Day-by-day plan (adjust to actual days remaining)

| Day | Focus | Exit criteria |
|---|---|---|
| 1 | Schema + Zep integration (§3, §4 of design doc) | Can write a `ConfusionEvent` episode and read it back for one test student |
| 2 | Insight Engine (GPT-5.6 call + decision logic) | Given seeded history, engine correctly outputs escalate/retire/no-change with reasoning string |
| 3 | REST API + MCP server (thin wrappers over Day 1–2 logic) | A judge could `curl` the API or point an MCP client at it and get a real response |
| 4 | Demo UI: compare view + timeline + insight-log feed | The 3 core demo beats (§6.3 in design doc) work end-to-end with seeded data |
| 5 | Second domain seed data + widget (if time allows) | Same schema, different domain, zero code changes, demoable in one cut |
| 6 | Record demo video, write README, deploy everything to hosting | Public repo live, demo instance live, video uploaded |
| 7 (buffer) | Fix whatever broke on Day 6 | Submission form completed before deadline |

---

## 5. Demo script (for the 3-minute video)

1. **(0:00–0:20)** The problem — generic flashcard/tutor apps don't know *why* a student keeps confusing things; even Khanmigo/Duolingo's LLM layer is reactive, not cumulative (cite the LOOM paper finding).
2. **(0:20–1:00)** Memory-off vs memory-on comparison, live, same question, side by side.
3. **(1:00–2:00)** 3-checkpoint story for the ソ/ン pair, insight-log panel narrating the agent's own reasoning as it happens.
4. **(2:00–2:30)** Zoom out: small heatmap of 3–4 tracked pairs, then the second-domain cut (same engine, chemistry notation, zero new code).
5. **(2:30–3:00)** Codex/GPT-5.6 usage callout — what Codex built (scaffolding, API, MCP server), where GPT-5.6 reasoning specifically shows up (the insight decisions).

**Before recording:** run the seed script once per demo domain, verify the re-run guard is in place (do not let Codex or a dev-server hot-reload silently re-trigger seeding — this is the main way to burn free-tier credits unnecessarily).

---

## 6. README skeleton (paste and fill in)

```markdown
## Quickstart (as a tutor builder)
1. Get an API key: [demo key — pre-loaded with seeded history]
2. Point your agent at our MCP server: mcp.yourapp.dev
3. Call `log_confusion_event` whenever your tutor sees a student mix up two concepts
4. Call `get_insight_state` before generating your next drill — it tells you what to
   emphasize and why

## What this is
A memory + insight layer, not a tutoring app. Plug it into any existing or
custom-built tutor agent to add persistent, temporal confusion tracking.

## What this is not
Not a curriculum, not a quiz bank, not a replacement for Duolingo/Khan Academy's
scoring engines — those already work well at their scale. This fills the gap
between that scoring infrastructure and a proactive, cumulative LLM tutor layer,
for builders who don't have Knewton-scale infrastructure of their own.

## Architecture
See architecture.mermaid / design_doc.md
```

---

## 7. Known limitations to disclose, not hide

- Demo student histories are synthetically seeded, clearly labeled as such.
- No real pedagogical validation of drill effectiveness — the insight engine's *behavior change* is what's being demonstrated, not teaching efficacy.
- Zep free-tier limits (~1,000 credits/month, exact figure varies by source/date — verify at getzep.com/pricing before submission) are fine for demo scale; production/school-scale would move to a paid tier, noted openly in submission materials.

---

## 8. Submission checklist (OpenAI Build Week)

- [ ] Public GitHub repo with OSS license visible in the About section
- [ ] README with setup instructions, sample data, clear run instructions
- [ ] Explicit documentation of where Codex accelerated the workflow and where key decisions were made
- [ ] `/feedback` Codex Session ID included in submission form
- [ ] Category selected: Education, with brief justification
- [ ] Text description of features/functionality
- [ ] Demo video (<3 min, public YouTube link, audio covering Codex + GPT-5.6 usage)
- [ ] Code repository URL (public, or private + shared with testing@devpost.com and build-week-event@openai.com)
- [ ] Since framed as integrable dev infrastructure: installation instructions, supported platforms, and a working demo instance / sandbox / test account so judges can test without rebuilding

---

## 9. Open decisions for whoever continues this

1. Confirm current exact Zep free-tier numbers before finalizing any cost claims in submission text.
2. Decide whether the embeddable widget (§5, design doc) is in-scope or a cut stretch goal based on actual time remaining.
