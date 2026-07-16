# Design Document: Adaptive Memory for Tutors
### A pluggable temporal-memory insight layer for tutoring agents

**Status:** Draft for OpenAI Build Week submission
**Track:** Education
**Last updated:** 2026-07-16

---

## 1. Problem Statement

### 1.1 The market gap (researched, not assumed)

Large ed-tech platforms already have adaptive-learning infrastructure:

- Duolingo personalizes lesson difficulty and content based on proficiency and learning patterns.
- Khan Academy adjusts exercise difficulty via adaptive assessments and tracks individual progress.
- Knewton/DreamBox run large-scale adaptive engines (DreamBox: 8,000 schools, 3M K–8 students, measurable NWEA MAP score gains).

However, a documented and current gap exists between that adaptive-scoring infrastructure and the *new* conversational LLM tutoring layer these same companies have bolted on:

> Khan Academy's Khanmigo and Duolingo's GPT-4 integration "remain largely reactive — responding to user prompts without maintaining a persistent model of the learner's goals or progress. They rarely intervene proactively or scaffold cumulative understanding." — *LOOM paper, arXiv 2511.21037*

This is the gap we target. We are not competing with Duolingo/Khan Academy's proprietary scoring engines — they don't need us. Our customer is the **long tail**: indie tutor-bot builders, small ed-tech startups, and schools building custom LLM tutors (e.g. with Codex/GPT-5.6) who have none of that infrastructure and would otherwise have to build a Knewton-scale pipeline from scratch just to get basic persistent memory.

### 1.2 What we are NOT building

We are explicitly **not** building a real tutoring app, curriculum, or quiz content engine. The hiragana/katakana confusable-pairs example is an illustrative case study, not the product. The product is the memory + insight layer underneath. We prove genericness by re-running the identical schema against a second, unrelated domain with zero code changes (see §6.3).

---

## 2. Core Concept

A **temporal knowledge graph** (via Zep/Graphiti) tracks confusion events per student over time. Facts are never overwritten — they are invalidated and superseded, preserving full history natively. On top of that substrate, a **GPT-5.6 reasoning layer** periodically inspects the graph's current and historical state and decides a pedagogical action (escalate drilling, retire a resolved confusion, no change), writing that decision back as an auditable insight.

The split of responsibility is the whole point:

| Layer | Owns | Built by |
|---|---|---|
| Zep/Graphiti (existing product) | Ground truth of what changed and when (bi-temporal edges, invalidation, point-in-time queries) | Not us — integrated as-is |
| Insight Engine (our product) | The reasoning about what to *do* with that signal | Us, via Codex + GPT-5.6 |

---

## 3. Why Zep/Graphiti Specifically

### 3.1 Bi-temporal model maps directly onto "improvement over time"

Every edge carries two clocks: event time (when the fact was true) and ingestion time (when the system learned it). When new information contradicts old, Graphiti **invalidates the old edge (`invalid_at` set) rather than deleting it** — preserving full history automatically.

Mapped onto our use case:
- Week 1 episode → edge `ConfusionState(pair: ソ/ン, severity: high)`
- Week 3 episode (student now correct 5x running) → new edge `ConfusionState(severity: resolved)`, old edge auto-invalidated at week 3

This gives us a **native point-in-time query** ("what was true about this student's confusion as of week 2") with no custom versioning code required.

### 3.2 Multi-tenancy and scale (validated, not assumed)

- One graph per student (`user_id`), fully isolated — "all graphs are completely isolated from each other with no shared state."
- Isolation is native: a query against one user's graph never surfaces another user's data.
- Scale target explicitly supports "many millions of users per account," with retrieval scaling in near-constant time regardless of dataset size.
- No limit on number of graphs or graph size.

This means: **a class of 30 students and a district of 30,000 are architecturally the same problem** — N isolated graphs, not one giant shared structure to partition ourselves.

### 3.3 Known trade-offs (stated honestly, for Production Readiness judging criterion)

- Zep Cloud (managed) is credit-metered: free tier ≈ 1,000 credits/month (some sources cite 2,500 messages + 2.5MB graph data — pricing pages have shown variation), no credit card required, renews monthly (not a time-limited trial).
- Credits are consumed on **write** (episode ingestion) only — memory, retrieval, storage, and number of users are unmetered.
- Self-hosting Graphiti directly (bypassing Zep Cloud) requires operating Neo4j/FalkorDB/Kuzu yourself — a real ops burden we are deliberately avoiding for this build. Zep's own Community Edition (self-hosted) has been deprecated.
- **Decision:** use Zep Cloud managed free tier for the hackathon build. At school-district production scale, the paid Flex tier (~$25–125/mo depending on source/date) is the realistic pricing point — noted in submission material rather than glossed over.

---

## 4. Data Model

```
ConceptPair
  id
  tenant_id      # school / tutor org — opaque, no PII required
  domain         # e.g. "japanese-kana", "chemistry-notation"
  label_a
  label_b
  description

ConfusionEvent (ingested as a Zep episode)
  tenant_id
  pair_id
  student_ref    # opaque string supplied by integrator — never real student PII
  timestamp
  correct: bool
  context

InsightLog (derived — may live as Graphiti edges directly, see §3.1)
  tenant_id
  pair_id
  timestamp
  decision       # escalate | retire | no_change
  reasoning      # one-line GPT-5.6-generated explanation
```

`student_ref` is intentionally opaque — the integrating tutor supplies any string they like. We never need or store real student identity, which removes a data-privacy concern for judges and for real schools evaluating adoption.

---

## 5. Integration Surfaces (packaging)

Three surfaces, same underlying engine — cheap to ship all three once the core exists:

1. **REST API** — baseline, works with any stack.
   `POST /v1/events`, `GET /v1/insights/:pairId`, `GET /v1/pairs?domain=X`
2. **MCP server** — the primary audience. Exposes `log_confusion_event`, `get_insight_state`, `get_confusion_heatmap` as MCP tools so any Codex/Claude-built tutor agent adopts memory-augmented tutoring by adding one server URL — no custom integration code.
3. **Embeddable widget** — a `<script>` tag / iframe rendering the insight-log feed or confusion heatmap directly inside a third party's own dashboard. Used in the demo to prove "same engine, different UI" cheaply, without building a second real app.

Build order for the week (cheapest-to-most-valuable given time risk):
1. Core engine + multi-tenant schema
2. REST API
3. MCP server (thin wrapper over #1–2)
4. Our own demo tutor UI (hiragana case study)
5. Embeddable widget — stretch goal, cuttable if time runs short (MCP server alone already proves pluggability)

---

## 6. Demo Strategy

### 6.1 The problem with "show a student's whole learning history"

Impossible in 3 minutes and not actually convincing. We solve this with seeded synthetic history plus a sharp, narrow narrative — see below.

### 6.2 Seeded synthetic history

A seeding script generates 8–10 fake past sessions with realistic timestamps spread across weeks before recording. This is disclosed openly, not hidden — judges get a "Generate 2 weeks of practice history" button in a demo mode so they can create their own believable history in one click during live testing, satisfying the requirement that judges be able to test the project without rebuilding it from scratch. **Safeguard:** this button must be explicitly gated (not run on every dev reload) to avoid burning Zep free-tier credits accidentally during Codex-assisted iteration.

### 6.3 The four demo beats

1. **Memory ON vs memory OFF, side by side** (the single strongest moment): identical question asked to a stateless agent vs. one with 3 weeks of seeded history. Generic drill vs. "you've mixed up ソ/ン six times in the last two weeks, most often at the end of a word — here's a drill targeting exactly that position."
2. **3-checkpoint story for one confusable pair**: week 1 (flagged) → week 2 (not improving, strategy adjusts) → week 3 (resolved, retired). A simple accuracy-over-time chart with an annotation at each checkpoint carries this.
3. **Insight-log panel**: a timestamped feed of the agent's own memory-driven decisions ("Detected: confusion persisting 3 sessions → escalating drill frequency"). This is the visual centerpiece — the thing a stateless LLM cannot produce.
4. **Second-domain proof of generality**: same schema, zero new code, re-run against an unrelated domain (e.g. confusable chemistry notation) — one cut in the video, strongest signal that this is infrastructure, not a one-off flashcard app.

### 6.4 Live "as-of" query as a judge-facing party trick

Because Graphiti preserves invalidated facts, we can run a genuine point-in-time query live on stage — "confusion state as of two weeks ago" vs. "now" — returning two different real answers from the same live data, rather than a pre-rendered chart.

---

## 7. Competitive Positioning (for submission narrative)

Do **not** claim "we invented adaptive learning." Claim:

> "Duolingo and Khan Academy solved this at massive scale with years of proprietary infrastructure and still haven't connected it to their own LLM tutors. We're the memory layer that gives any smaller builder both — instantly, in one API call."

This is more credible than an invention claim and directly answers "why not build it themselves" (because building it themselves means recreating Knewton-scale infrastructure).

---

## 8. Hosting Architecture

See `architecture.mermaid` for the full diagram. Summary:

| Component | Hosting | Notes |
|---|---|---|
| Demo UI + embeddable widget | Vercel / Netlify | Static + edge functions, zero ops |
| Ingestion + Insight Engine backend | AWS Lambda or Cloud Run | Scale-to-zero, no idle cost, no VM to babysit during judging window |
| Memory substrate | Zep Cloud (managed) | No self-hosted graph DB to operate |

**Total hosted surfaces: 2 frontends (can share one deploy), 1 backend serverless function, 1 managed memory service — zero VMs.** This matters because the hackathon requires the project to run *consistently* through the judging window; scale-to-zero serverless removes the risk of an unattended VM silently failing between submission and judging.

---

## 9. Hackathon Submission Notes

- **Target:** OpenAI Build Week (Education track). Deadline: Jul 21, 2026, 5:00pm PDT. Requires demonstrated Codex + GPT-5.6 usage, a public repo, and — since we're framing this as integrable dev infrastructure — a way for judges to test without rebuilding (demo instance / API key / sandbox).
- This is a single-hackathon submission. No CockroachDB dependency, no dual-submission plan — Zep/Graphiti is the memory substrate, full stop.

---

## 10. Risks and Open Questions

- Zep free-tier credit consumption during iterative Codex development — mitigate with a seeding-script guard (see §6.2).
- Pricing figures for Zep's free tier vary slightly across sources/dates — confirm current numbers on getzep.com/pricing before finalizing submission claims.
- No real pedagogical validation — explicitly out of scope; the case study exists to demonstrate the engine, not to claim teaching efficacy.
- Second-domain seed data (chemistry notation or similar) needs to be prepared in advance, not improvised during recording.
