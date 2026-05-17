# Architecture Decisions

Short notes on each meaningful technical choice, in chronological order. Each entry: what was chosen, what was considered, why.

---

## D001 — Routing engine: custom Python (osmnx + networkx)

**Date:** 2026-05-17

**Decision:** Build the routing engine in Python using `osmnx` to load OpenStreetMap data and `networkx` for a custom A\* implementation with scooter-specific edge weights.

**Alternatives considered:**

- **OSRM with custom Lua profiles** — industry-standard C++ routing engine. Faster, more "production". Rejected because: (a) requires Docker Desktop on Windows, more setup friction; (b) the interesting logic ends up in Lua scripts inside the engine's runtime — less of "my own code" visible in the repo.
- **GraphHopper with custom model** — clean declarative profile DSL. Rejected because: (a) requires Java install; (b) similar issue — the rules end up as configuration, not as code.

**Why this:**

- All routing logic lives in our own Python files — readable, defensible in an interview, the kind of "I built it" story that matters more than "I configured a known engine".
- Same Python environment as the Week 3 ML notebook — coherent stack, shared data.
- `osmnx` is well-regarded in academic transportation research, which complements the AI/CS framing.
- Zero JVM, zero Docker. One Python install handles everything.

**Tradeoff accepted:** Pure-Python A\* is slower than OSRM or GraphHopper. For a local-only portfolio demo on Amsterdam-scale data this is fine; in any production future this would need to be rewritten.

---

## D002 — Frontend: vanilla HTML + MapLibre GL via CDN

**Date:** 2026-05-17

**Decision:** Single-page vanilla HTML + JS frontend, loading MapLibre from a CDN. No Node.js, no build step.

**Alternatives considered:**

- **Next.js / React** — industry-standard, looks "real". Rejected because: (a) a build step adds friction without buying anything for a single-page demo; (b) the React story doesn't help a Business + AI + CS application — the routing and the ML are what should be the centre of attention.

**Why this:**

- Anyone can run this with `python -m http.server`. Trivial to demo.
- No `package-lock` weirdness, no install errors, no version mismatches over the 4-week timeline.
- The HTML and JS are short and readable — a reviewer can see exactly how the app works.

---

## D003 — Project scope: local-only, three artifacts, IE Madrid admissions

**Date:** 2026-05-17

**Decision:** Optimize the project for a single goal: impress IE Madrid admissions for the Dual Degree in Business + Computer Science & AI. Local-only is fine; no deployment, no real users.

**The three artifacts:**

1. **Product (CS)** — the working app + custom routing engine.
2. **Analysis (AI)** — Jupyter notebook quantifying the problem, plus a trained ML model.
3. **Business case** — written case + pitch deck.

**Timeline:** 4 weeks (May 17 → June 14 2026).

**Why this:**

- IE is business-school-first with holistic admissions — the narrative and the pitch matter as much as the technical depth.
- A reviewer will spend 5–10 minutes on the portfolio. The README, screenshots, and demo video carry most of that weight.
- All three of Business / AI / CS must be visibly demonstrated, not just claimed.

---
