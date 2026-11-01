# FreshTrace for the Meta AI Developer Hackathon
> **Three approaches, reviewed and upgraded — each with a unique feature set and a winning USP**  
> *Strategy Document — 31 Oct 2026*

---

## 1. Executive Summary

You are choosing between three directions for the same product: **Rescue** (verified stock-priority assistant), **Investigator** (AI-designed tests to find the suspect group), and **ShelfWatch** (daily produce memory). Each has been reviewed against the judging criteria on the official event page, keeping what works, trimming what was decorative, and adding one genuinely distinctive USP to each.

### Bottom Line
> **Build Rescue as the product, and use Investigator's active-sensing loop as the wow moment (“Rescue + Probe”).**  
> Rescue is the most reliable and demo-able; Investigator has the highest creativity ceiling but depends on sensor repeatability; ShelfWatch is the weakest standalone entry but supplies cheap, valuable add-ons (batch QR passport, daily data). A Day-1 sensor test decides whether the Probe is in or out.

| Item | Detail |
| :--- | :--- |
| **Official Deadline** | Submissions due **Nov 4, 2026, 9:00 PM ET = Nov 5, 7:30 AM IST**. Treat Nov 4 (IST) as your last working day; aim to submit that evening, leaving the night as buffer. |
| **Judging / Finals** | Judging Nov 4–8; closing ceremony with live finals and winners on Nov 9. |
| **Prize Pool** | $1,000,000 across two tracks (indie developer, startup). |
| **Current Timeline** | Saturday, Oct 31 — five working days including today. |

### What Changed From the Previous Version
- **Cut Muse Image from the core plan:** A generated promo background for a clearance listing is decoration, and model-count padding is not rewarded. Replaced by a practical fit-for-use hand-off action.
- **Demoted “tap a tomato and ask a question”:** Tap-to-segment is table stakes now; it supports the story but must not lead it.
- **Gave Wonder a real job:** In every approach it is the orchestrator that calls tools and keeps state, not a one-shot summarizer bolted on at the end.
- **Made the sensor's value visible in five seconds** through a side-by-side “Priority Flip” instead of describing it in a paragraph.
- **Added measurable proof** (blinded trials, lead-time metric, image-only vs sensor-only vs combined) because “whether it works” is an explicit criterion.
- **Corrected scope language:** Readings belong to a crate or a group, never to an individual item, and nothing is described as proving food safety.

---

## 2. What the Judges Are Looking For

From the official event page:
- **Indie Developer Track** (individual builders and students): Judged on **creativity**, **technical ambition**, and **whether it works**.
- **Startup Track** (teams and founders building a real product): Judged on **technical execution** and **whether it holds up in production**.
- **Theme 1 — Build for Your World:** A problem you know firsthand; make something possible that wasn't before.
- **Theme 2 — Push the Frontier:** Give a machine a new capability; understand and control a physical system; show what becomes possible when the models meet the real world.

> **Implication:** FreshTrace's hardware sensor is your strongest differentiator because it ties the models to a physical system — that is squarely **Theme 2** — while a vendor workflow is squarely **Theme 1**. The best entry shows both, and proves it works with real measured results. *(Check the track rules in the Official Rules published on Oct 26 to confirm which track fits your team).*

---

## 3. Differentiators That Apply to Any Approach

| Differentiator | What it is | Why it impresses |
| :--- | :--- | :--- |
| **Calibrated Abstention** | When camera and sensor disagree or data is thin, the agent says *“I need another test”* and names the cheapest next one. | Shows responsible AI and active reasoning instead of confident guessing. |
| **Evidence Receipt** | Every recommendation exports a JSON + QR record: photo hashes, SAM masks, sensor session, model versions, human confirmations, final decision. | Auditability and production-readiness; a buyer or inspector can scan it. |
| **Three-Way Evaluation** | Run image-only, sensor-only, and combined on the same small case set; show the table, including failures. | Directly answers *“does it work?”* with your own numbers. |
| **Baseline-Relative Scoring** | Score each reading relative to that crate's own opening reading (and a fresh reference run), not a fixed global threshold. | Handles ambient variation; signals real engineering rather than a demo trick. |
| **Honest Claims** | State the limits on screen: crate-level evidence, no food-safety guarantee, no exact expiry time. | Builds judge trust; prevents an easy takedown during Q&A. |

---

## 4. Approach 1 — FreshTrace Rescue: “Which stock needs attention first?”

**Pitch:** A vendor photographs a crate, adds a sensor reading, and gets a prioritized stock plan with the evidence behind it. *(The household version — “which stored vegetables should I inspect and use first?” — is a wording change, not a second build).*

### USP — “Eyes First, Then Nose”: Priority Flip + Evidence Receipt
FreshTrace shows, on one screen, what the camera alone would decide, what the sensor alone would decide, and the fused decision — and highlights the exact moment the sensor flips a crate's priority. Every decision then ships with a scannable Evidence Receipt.  
**One-line claim:** *A produce assistant that knows when its camera isn't enough, and shows its receipts.*

### Revised Workflow
1. Vendor photographs the crate and asks (voice or text): *“Which stock should I prioritize today?”*
2. **SAM 3.1** segments visible produce; **Muse Spark** records visible observations (discoloration, surface damage) linked to masks.
3. Vendor places the existing sensor in the crate; the app runs a timestamped session (baseline, measure, recovery) and logs temperature/humidity.
4. **Priority Flip:** Spark fuses image + sensor evidence. If they conflict, it requests a second photo or a repeat measurement.
5. **Attention Queue:** Routine monitoring / prioritize inspection / hold for inspection, with evidence shown.
6. **Action Pack via Muse Wonder:** Day plan across crates; for stock the vendor confirms fit for sale, a discount listing at the vendor's price, or a surplus hand-off note; Evidence Receipt generated.

### New Unique Features
| Feature | What it does | Est. Effort |
| :--- | :--- | :--- |
| **Priority Flip Card** | Three-column view (camera-only / sensor-only / fused) with a visible “flipped by sensor” badge and one-sentence reason. | ~5 h |
| **Crate Baseline Fingerprint** | Scores each reading relative to the crate's own opening reading and an optional fresh reference run. | ~6 h |
| **Evidence Receipt (QR)** | Hash-linked JSON of photos, masks, sensor session, model versions, human confirmations, and decision. | ~5 h |
| **Conflict-Driven Re-test** | Agent requests the next-best evidence instead of guessing when signals disagree. | ~4 h |
| **Vendor-Language Voice** | Muse Voice Transcribe tested on your target languages on Day 1 (do not assume support); fall back to text if weak. | ~3 h |
| **Fit-for-Use Hand-off** | Replaces the Muse Image promo: vendor-approved discount text or a hand-off note for unsold, vendor-confirmed stock. | ~4 h |

### Model Roles
- **SAM 3.1:** Segmentation and tap selection (no calibrated freshness score).
- **Muse Spark:** Image interpretation, evidence fusion, tool calls to your FastAPI backend, explanations.
- **Muse Wonder:** Multi-crate stock planner with tools such as `get_crate_history` and `schedule_remeasure`.
- **Muse Voice Transcribe:** Spoken requests and confirmations.
- **Muse Image:** Optional, only after everything else works.

### Three-Minute Demo Script
| Time | Beat |
| :--- | :--- |
| **0:00–0:20** | **The problem:** A small vendor, several crates, no time to inspect everything. |
| **0:20–0:50** | Photograph two crates; SAM overlay; camera-only verdict reads “routine” for both. |
| **0:50–1:40** | Sensor sessions on both crates; **Priority Flip** moves one crate to “prioritize inspection” with the reason on screen. |
| **1:40–2:15** | A conflicting case: The agent asks for a repeat measurement and resolves it. |
| **2:15–2:40** | Wonder's day plan, the Action Pack, and a scan of the Evidence Receipt QR. |
| **2:40–3:00** | Your three-way evaluation table, plus a clear split of pre-existing hardware vs work built in the event. |

### Risks and Mitigations
- **Sensor signal is weak:** Still demonstrates conflict handling and honest abstention; lean on the Receipt and evaluation table.
- **Demo-day failure:** Pre-record one clean take and keep cached model responses for the live path.

---

## 5. Approach 2 — FreshTrace Investigator: “Something is wrong in this crate.”

**Pitch:** The camera can't resolve the problem, so the agent designs a physical test, uses a real instrument, and narrows the suspect group. This is the strongest fit for “Push the Frontier”: a machine gains a new real-world capability.

### USP — “Binary-Search the Rot”: Adaptive Group Testing with a Physical Instrument
Instead of measuring everything, the agent splits suspects into groups (SAM proposes the groups), measures them with the sensor, updates a live Suspect Board, and splits the winning group again — in principle about $\log_2(n)$ rounds (3 rounds for 8 items if the signal were perfectly reliable; noise will add rounds). A reference control and a carryover guard make the measurements trustworthy. The finale is a blinded challenge: a teammate secretly plants one visibly degraded item among normal ones and the app finds it.  
**One-line claim:** *The first produce assistant that runs its own experiments.*

### Revised Workflow
1. Photo plus a crate-level sensor session shows an alert while the camera sees no clear culprit.
2. **Wonder (orchestrator)** writes a Test Plan: SAM clusters visible produce into groups; the plan states which split is expected to narrow the suspects most.
3. **Carryover Guard:** The app enforces recovery-to-baseline and a blank run between measurements, and measures a known-fresh reference sample in the same session to cancel drift.
4. Vendor measures group A then B using one consistent procedure; the Suspect Board updates after each test.
5. Next round splits the leading group; the loop stops at a round budget or when the leading group is clear, or reports “unresolved.”
6. **Closing step:** A human inspects the narrowed group and records the true outcome, which feeds the hit-rate table.

### New Unique Features
| Feature | What it does | Est. Effort |
| :--- | :--- | :--- |
| **Suspect Board** | Live bars of baseline-corrected group responses, labelled a relative suspect score (not a probability) unless you calibrate it. | ~6 h |
| **Test Design Card** | Explains in one sentence why the next split was chosen and what result would change the plan. | ~4 h |
| **Carryover Guard + Blank Run** | Refuses to proceed until the sensor has recovered; shows why it is waiting. | ~5 h |
| **Reference Control** | A known-fresh sample measured in the same session to cancel environmental drift. | ~3 h |
| **Blinded Challenge Harness** | Teammate plants one visibly degraded item; run $n$ trials; report the hit rate. Optionally let a judge choose the crate live. | ~6 h |
| **Hands-Free Steps** | Voice confirmation (“group A done”) so both hands stay on the crate. | ~3 h |

### Model Roles
| Model | Purpose |
| :--- | :--- |
| **SAM 3.1** | Propose and mark the groups on the camera view. |
| **Muse Spark** | Interpret photos, compare group results, explain uncertainty. |
| **Muse Wonder** | Own the investigation state; choose the next test; stop or declare unresolved. |
| **Voice Transcribe** | Hands-free confirmations and questions. |

### Three-Minute Demo Script
| Time | Beat |
| :--- | :--- |
| **0:00–0:25** | The crate looks fine, yet the sensor alerts. The camera cannot decide. |
| **0:25–1:00** | Agent produces the Test Plan; SAM marks groups A and B; reference control and blank run. |
| **1:00–2:00** | Measure A and B; Suspect Board shifts; the leading group splits again; the agent narrows to a small set. |
| **2:00–2:30** | **Reveal:** The human inspection confirms (or honestly refutes) the narrowed group. |
| **2:30–3:00** | Blinded-trial hit rate across $n$ runs, plus a clear statement of what the sensor can and cannot do. |

### Risks and Mitigations
- **Main risk — Repeatability:** Gas carryover, airflow, humidity, and recovery time can swamp the group signal.
- **Day-1 go/no-go test:** Measure visibly normal and visibly degraded samples repeatedly under identical conditions. Suggested internal bar: the degraded sample separates from normal in most repeat pairs (e.g., 8 of 10). If it fails, drop group localization and demonstrate repeat testing and uncertainty handling only.
- Never present a higher group response as proof that a specific item is rotten.

---

## 6. Approach 3 — FreshTrace ShelfWatch: “Remember my produce and tell me what changed.”

**Pitch:** Every batch gets a memory. FreshTrace compares each new scan with that batch's own history and tells the vendor or household what changed and what to handle first.

### USP — “Early-Warning Lead Time” + Batch Passport
Each batch gets a QR Batch Passport (photos, masks, sensor sessions, notes, usage log). A simple change-point detector flags when the sensor response departs from that batch's own baseline. You then measure the lead time: hours between that sensor flag and the first visible change recorded by Spark and by a human annotator. If the lead time is positive across your batches, that single number is your headline; if not, you report it honestly as a pilot result.  
**One-line claim:** *Does the nose notice before the eye does? We measured it.*

### Revised Workflow
1. **Register a batch:** Photo, label/QR, purchase date if known, initial sensor session (baseline).
2. **Daily tracking:** New photo (SAM segments visible produce), optional sensor check; Spark compares with the previous session.
3. **Change report:** Visible appearance, sensor deviation from own baseline, and inspection priority.
4. **Cross-batch prioritization:** Wonder compares histories, flags stale or missing measurements, prepares the action list.
5. **Household mode:** A “use these first” list and a usage log (used, shared, discarded).

### New Unique Features
| Feature | What it does | Est. Effort |
| :--- | :--- | :--- |
| **Batch Passport (QR)** | One scannable timeline per batch. Reusable as the Evidence Receipt in Approach 1. | ~5 h |
| **Own-Baseline Change-Point Detector** | Simple deviation or CUSUM rule against the batch's first-day baseline; framed as monitoring, not prediction. | ~5 h |
| **Lead-Time Scoreboard** | Hours between sensor change-point and first visible change; report $n$ and negative results honestly. | ~4 h |
| **Mask Timelapse** | Day-by-day photo strip with SAM masks (identity is only tracked within a session, not across rearranged days). | ~4 h |
| **Stale-Evidence Flags** | Warns when a batch's last measurement is too old to trust the ranking. | ~2 h |

### Three-Minute Demo Script
| Time | Beat |
| :--- | :--- |
| **0:00–0:25** | The vendor has several batches bought on different days; every check today starts from zero. |
| **0:25–1:15** | Scan a Batch Passport QR; show the timelapse and sensor curve from the real days collected. |
| **1:15–2:00** | Change-point flag appears before visible change; lead-time scoreboard shows measured hours. |
| **2:00–2:40** | Wonder ranks batches and produces the action list; log what was used or sold. |
| **2:40–3:00** | Limits: Change tracking and prioritization, not shelf-life prediction. |

### Risks and Mitigations
- **Little data:** A few days of tomatoes only supports a pilot claim. Start collecting today, whichever approach you choose.
- **Slower, less dramatic demo:** Pre-collected timelapse plus one live scan of the final day.
- Do not say *“expires in 18 hours”*; that exceeds what your data can validate.

---

## 7. Side-by-Side Comparison & Revised Ranking

Scores are estimated (1–5) after adding USPs, evaluated against indie-track criteria and themes:

| Criterion | 1. Rescue | 2. Investigator | 3. ShelfWatch |
| :--- | :---: | :---: | :---: |
| **Creativity** | 4 | 5 | 3 |
| **Technical Ambition** | 4 | 5 | 3 |
| **Works Reliably in Demo** | 5 | 3 *(sensor-dependent)* | 4 |
| **Fit: Build for Your World** | 5 | 3 | 4 |
| **Fit: Push the Frontier** | 3 | 5 | 2 |
| **Demo Clarity in 3 Minutes** | 5 | 4 | 3 |
| **Effort within ~60 Person-Hours** | Comfortable | Tight | Comfortable |
| **Overall Rank** | **1st** | **2nd** *(1st if Day-1 gate passes)* | **3rd** standalone; best as add-ons |

### Recommended Final Build: “Rescue + Probe”
- **Product:** Rescue (Priority Flip, Evidence Receipt, Action Pack).
- **Wow Moment:** A one-round Probe from Investigator (A/B split with reference control and blank run) when camera and sensor conflict.
- **Cheap Borrow from ShelfWatch:** The Batch Passport QR doubles as the Evidence Receipt, and daily data collected from today becomes a bonus slide.
- *Fallback:* If the Day-1 gate fails, ship Rescue with conflict-driven re-test as the active-reasoning moment and skip the Probe.

---

## 8. Models, Budget and Sensor Protocol

Target four runtime models (**SAM**, **Spark**, **Voice Transcribe**, **Wonder**). Add **Muse Image** only if everything else is finished. There is no requirement to use every model; meaningful integration beats model count.

| Model | Published Example Pricing *(verify on dev.meta.ai)* |
| :--- | :--- |
| **SAM 3.1** image segmentation | $2.50 per 1,000 images |
| **Muse Spark 1.3** standard | $1.25 / 1M input tokens; $4.25 / 1M output tokens |
| **Muse Wonder** | $4.00 / 1M input tokens; $20.00 / 1M output tokens |
| **Muse Voice Transcribe** | $0.18 per hour |
| **Muse Image** | $0.01 per image |

> **Budget Safety ($150 limit):** Use still photos first, cache repeated results, send summarized sensor sessions rather than raw streams, call Wonder once per planning task, and measure the real cost of the first full session before scaling tests. Muse Glimmer (open weights) is an optional local-fallback experiment after the main demo is done; partner credits (Baseten, Modal, Fireworks) apply only to open-weights models and are separate from your Meta API credits.

### Sensor Protocol (Evidence is only as good as the procedure)
1. **Create a session record:** Batch ID, timestamp, produce type, photos, raw readings, device alert, temperature/humidity.
2. **Follow sensor warm-up & recovery:** Characterize your device rather than assuming universal duration.
3. **Consistency:** Keep container, quantity, placement, and procedure consistent; log every deviation.
4. **Controlled comparisons:** Start with one produce type (tomatoes) and repeat normal-versus-degraded comparisons.
5. **Data hygiene:** Keep original photos and human notes. Call the result a small demonstration dataset, not laboratory ground truth.

---

## 9. Five-Day Plan (IST)

| Day | Deliverables |
| :--- | :--- |
| **Sat 31 Oct** | Confirm API access; smoke-test SAM and Spark on real photos; run the sensor repeatability gate; test voice languages; start daily batch collection. |
| **Sun 1 Nov** | Android-friendly capture UI, SAM overlays, batch IDs, session-to-batch linking, baseline fingerprint. |
| **Mon 2 Nov** | Spark fusion, Priority Flip, conflict-driven re-test, Evidence Receipt. |
| **Tue 3 Nov** | Voice input, Wonder planner and Action Pack; Probe (if gate passed); test with a real vendor; run the three-way evaluation and blinded trials. |
| **Wed 4 Nov** | Feature freeze around midday; fix failures; record the demo; write the README; submit that evening (hard deadline is 7:30 AM IST on Nov 5). |

> **Suggested Split:** Mobile interface / Meta backend integration / sensor experiments and evaluation. Build on your existing React and FastAPI platform; a native Android app would not strengthen the core demo.

---

## 10. Submission Checklist and Claims to Avoid

- Public repository and demo that clearly separate pre-existing hardware/dashboard from work built during the event.
- Three-minute video following one of the scripts above; include the evaluation table with failures.
- Measured latency and cost per session; a short limitations slide.
- Confirm the track and any rule changes in the Official Rules published on Oct 26; dates may change at Meta's discretion.

### Claims Guidance
| Avoid Saying | Say Instead |
| :--- | :--- |
| *“The sensor proves this tomato is rotten.”* | *“This crate or group showed a stronger response; inspect it first.”* |
| *“Safe to eat” / “fresh for 18 more hours.”* | *“Inspection priority based on visible and sensor evidence.”* |
| *“95% accurate.”* | Report observed results on your own cases, with $n$ and failures. |
| *“AI waste reduction achieved.”* | *“Designed to help prioritize stock; outcomes pending real-world trials.”* |

---

*Sources: Event page · SAM 3.1 · Muse Spark · Muse Wonder · Voice Transcribe · Muse Image. Model pricing and capabilities are as published at the time of writing and may change.*
