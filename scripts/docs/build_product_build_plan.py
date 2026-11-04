from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/product_build_plan.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
FONT = Path("C:/Windows/Fonts")
for name, file in [("Body", "segoeui.ttf"), ("Bold", "segoeuib.ttf"), ("Italic", "segoeuii.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONT / file)))
pdfmetrics.registerFontFamily(
    "Body", normal="Body", bold="Bold", italic="Italic", boldItalic="Bold"
)
INK = colors.HexColor("#16352F")
GREEN = colors.HexColor("#087E69")
MUTED = colors.HexColor("#526862")
LIGHT = colors.HexColor("#EFF6F2")
LINE = colors.HexColor("#D9E5DE")
GOLD = colors.HexColor("#B87622")
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="BodyX", fontName="Body", fontSize=10, leading=14.5, textColor=INK, spaceAfter=8
    )
)
styles.add(
    ParagraphStyle(name="SmallX", parent=styles["BodyX"], fontSize=8.3, leading=11.5, spaceAfter=5)
)
styles.add(
    ParagraphStyle(
        name="H1X", fontName="Bold", fontSize=24, leading=28, textColor=INK, spaceAfter=14
    )
)
styles.add(
    ParagraphStyle(
        name="H2X",
        fontName="Bold",
        fontSize=12,
        leading=16,
        textColor=GREEN,
        spaceBefore=9,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        name="Kicker", fontName="Bold", fontSize=9, leading=12, textColor=GREEN, spaceAfter=9
    )
)
styles.add(
    ParagraphStyle(
        name="Cover", fontName="Bold", fontSize=39, leading=43, textColor=INK, spaceAfter=17
    )
)
styles.add(
    ParagraphStyle(
        name="Deck", fontName="Body", fontSize=16, leading=22, textColor=MUTED, spaceAfter=19
    )
)
styles.add(
    ParagraphStyle(name="TH", fontName="Bold", fontSize=8.5, leading=11.5, textColor=colors.white)
)
styles.add(ParagraphStyle(name="TD", fontName="Body", fontSize=8.5, leading=12, textColor=INK))
styles.add(
    ParagraphStyle(
        name="CodeX",
        fontName="Courier",
        fontSize=7.7,
        leading=10.5,
        textColor=INK,
        backColor=LIGHT,
        borderPadding=10,
        spaceAfter=10,
    )
)
story = []


def p(t, style="BodyX"):
    return Paragraph(t, styles[style])


def add(t):
    story.append(p(t))


def h(t):
    story.append(p(t, "H2X"))


def bullet(title, txt):
    add("<b>" + title + "</b> " + txt)


def table(headers, rows, widths):
    data = [[p(escape(str(v)), "TH") for v in headers]] + [
        [p(str(v), "TD") for v in row] for row in rows
    ]
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
            ]
        )
    )
    story.extend([t, Spacer(1, 9)])


def callout(title, txt):
    t = Table([[p(title, "H2X")], [p(txt)]], colWidths=[499])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.7, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 13),
                ("RIGHTPADDING", (0, 0), (-1, -1), 13),
                ("TOPPADDING", (0, 0), (-1, 0), 0),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
            ]
        )
    )
    story.extend([t, Spacer(1, 10)])


def page(n, title, sub=None):
    if story:
        story.append(PageBreak())
    story.append(p(n, "Kicker"))
    story.append(p(title, "H1X"))
    if sub:
        add(sub)


def code(t):
    story.append(Preformatted(t, styles["CodeX"]))


class Loop(Flowable):
    def __init__(self):
        Flowable.__init__(self)
        self.width = 499
        self.height = 132

    def draw(self):
        c = self.canv
        labels = [
            ("REMEMBER", "ShelfWatch"),
            ("PRIORITIZE", "Rescue"),
            ("INVESTIGATE", "Investigator"),
            ("ACT + LEARN", "Shared record"),
        ]
        for i, (a, b) in enumerate(labels):
            x = i * 127
            c.setFillColor(LIGHT)
            c.setStrokeColor(LINE)
            c.roundRect(x, 42, 116, 69, 8, fill=1, stroke=1)
            c.setFillColor(GREEN)
            c.setFont("Bold", 8.5)
            c.drawString(x + 9, 84, a)
            c.setFillColor(INK)
            c.setFont("Body", 9)
            c.drawString(x + 9, 64, b)
            if i < 3:
                c.setStrokeColor(GREEN)
                c.line(x + 117, 76, x + 125, 76)
        c.setStrokeColor(GREEN)
        c.line(440, 35, 440, 18)
        c.line(440, 18, 58, 18)
        c.line(58, 18, 58, 35)
        c.setFont("Body", 8)
        c.setFillColor(MUTED)
        c.drawCentredString(249, 4, "Every confirmed outcome becomes evidence for the next check.")


page("PRODUCT BUILD PLAN / STRATEGY + DELIVERY", "One product.\nOne evidence loop.")
story[-1] = p("One product.<br/>One evidence loop.", "Cover")
story.append(
    p(
        "Combine Rescue, Investigator and ShelfWatch into an inspection and stock-action assistant.",
        "Deck",
    )
)
story.append(Loop())
callout(
    "The product in one sentence (name undecided)",
    "The app remembers each produce batch, helps a vendor choose what to inspect next, guides a controlled follow-up test when evidence is unclear, and records the human-approved action for the next visit.",
)
h("What this document gives you")
add(
    "A unified approach and user journey; a screen-by-screen model map; proposed scoring and uncertainty rules; specific changes to the current React/FastAPI project; and a gated, step-by-step build and evaluation plan."
)
table(
    ["Working assumptions", "Delivery boundary"],
    [
        (
            "31 October 2026 | Version 1.0",
            "Planning document, not an implementation or validation report.",
        ),
        (
            "3 developers x 4 hours/day x 5 days = 60 hours",
            "Inherited capacity assumption; reconfirm remaining availability.",
        ),
        (
            "One intermittent crate-level device; Android phone",
            "Tomatoes first. Hosted Meta APIs; no GPU deployment required.",
        ),
        ("Submit 4 November evening IST", "Published deadline: 5 November, 7:30 AM IST. [1]"),
    ],
    [249, 250],
)
story.append(
    p(
        "Read pages 2-5 for the product, 6-13 for technical design and API setup, and 14-19 for delivery, proof and references.",
        "SmallX",
    )
)

page("01 / THE COMBINED APPROACH", "Remember, inspect, resolve")
add(
    '<b>Primary user:</b> a small produce vendor with several batches and limited time to inspect them. <b>Primary question:</b> "I can check one crate now. Which one, and what should I do next?"'
)
table(
    ["Capability", "Its role in the single product", "What the user sees"],
    [
        (
            "ShelfWatch / memory",
            "Keeps batch identity, prior photos, valid sensor sessions, quantities and follow-up tasks.",
            "A Batch Passport and a due-check list.",
        ),
        (
            "Rescue / daily decision",
            "Uses current and historical evidence to order inspection work and prepare approved stock actions.",
            "Today's attention queue and an action card.",
        ),
        (
            "Investigator / uncertainty resolution",
            "Offers a repeat, another photo or a controlled A/B group comparison when justified.",
            'A guided "Resolve uncertainty" task inside the batch.',
        ),
        (
            "Shared evidence / closure",
            "Records why a task changed, who confirmed an action and what happened afterwards.",
            "One timeline, one receipt and a recorded outcome.",
        ),
    ],
    [104, 219, 176],
)
h("The unified USP")
add(
    '<b>"The app knows when a photo is not enough, asks for the next useful check, and remembers what the vendor did."</b> The distinguishing feature is the complete decision loop, supported by an instrument and an evidence history.'
)
h("A complete first release includes all three")
add(
    "Every batch has memory; every day has a prioritized queue; every unclear case has a bounded investigation path. Group localization is conditional on physical feasibility. If A/B testing fails its gate, Investigator still provides guided retesting and an explicit unresolved result."
)
h("Scope that keeps the product coherent")
add(
    "One vendor workflow, one produce type, still photos, one sensor queue, one A/B split at most, in-app due items and manual outcome confirmation. Household language, extra produce types, background push and image generation belong after the core loop works."
)
callout(
    "What success means",
    "A vendor can register a batch, complete a valid check, understand its inspection priority, resolve or acknowledge uncertainty, confirm an action and find the same record on the next visit.",
)

page("02 / USER JOURNEY", "From a new crate to the next visit")
table(
    ["Step", "User action", "System behavior and saved evidence"],
    [
        (
            "1. Register",
            "Create batch T-03; enter quantity, optional purchase date and price.",
            "Assign permanent batch_id and QR. Record location and produce type. The opening reading is a reference, not a fresh label.",
        ),
        (
            "2. Photograph",
            "Take a whole-crate photo. Confirm visible objects or correct selection.",
            "SAM produces masks; Spark records observable appearance with photo/mask references. Hidden items remain unobserved.",
        ),
        (
            "3. Ask / plan",
            'Enter "I have 10 minutes and one device."',
            "Wonder reads history and valid evidence, proposes tasks under time/device limits. Code validates and persists the plan.",
        ),
        (
            "4. Measure",
            "Follow warm-up, baseline, sample and recovery steps.",
            "Session controller locks the device, records telemetry and decides validity. Code produces numerical features.",
        ),
        (
            "5. Compare",
            "Read camera-only, sensor-only and combined cards.",
            "Deterministic policy sets inspection priority. Spark explains the actual evidence; a priority change is shown only if it occurs.",
        ),
        (
            "6. Investigate",
            "If needed, choose retake, repeat or a validated A/B test.",
            "Wonder proposes an allowed next step. Invalid tests cannot update rankings. Stop at the time/test limit.",
        ),
        (
            "7. Confirm action",
            "Inspect stock; record retain, further inspection, remove or eligible clearance.",
            "Prepare text at the vendor's chosen price only after confirmation. Log quantities and approval.",
        ),
        (
            "8. Return",
            "Scan QR at the next visit; complete due checks.",
            "ShelfWatch shows changes and missing/stale evidence. Outcomes update remaining quantity and the next plan.",
        ),
    ],
    [43, 166, 290],
)
callout(
    "One identity across the journey",
    "A batch can have many observations, sensor sessions, investigations and outcomes. A device is a reusable instrument, not the batch identity. A new group test must keep the parent batch and its group membership.",
)

page("03 / A WORKED EXAMPLE", "A single story that uses all three")
add(
    "The example below is illustrative, not a measured result. The point is to show the product behavior before implementation."
)
h("Morning: ShelfWatch gives context")
add(
    "The vendor opens three tomato batches. T-01 has a recent complete check; T-02 has a new visible concern; T-03 has an old photo and an incomplete sensor session. The app preserves capture times and shows T-03 as needing evidence rather than calling it fresh."
)
h("Rescue chooses a useful action")
add(
    "The vendor has one short inspection window. The queue highlights T-02 for inspection and T-03 for a new check. Wonder proposes measuring T-02 if that result could change the action within the available time; the interface explains the choice."
)
h("A real result can change the plan")
add(
    "T-02's new photo is visually ambiguous, but a valid sensor session has a stronger relative response than its recorded reference. The combined policy flags disagreement and requests human inspection. Camera-only, sensor-only and combined cards show their own missing data and reasons."
)
h("Investigator resolves or stops")
add(
    'If the physical group-testing gate has passed, the vendor confirms two balanced groups on the image, then measures them using the same setup. A meaningful valid difference identifies which group to inspect first. A weak difference produces "inconclusive"; it does not identify a rotten tomato.'
)
h("An action becomes tomorrow's memory")
add(
    "The vendor inspects the group, removes a recorded quantity and confirms whether the remaining stock is eligible for a chosen action. The app logs the result, updates quantity and schedules an in-app follow-up. Tomorrow, ShelfWatch uses this exact record."
)
callout(
    "The story does not require a dramatic flip",
    "The sensor may preserve the camera-based priority, conflict may remain unresolved, and no early warning may appear in the pilot. A useful plan with explicit limits is still a valid completed workflow.",
)

page("04 / PRODUCT SURFACES", "Five screens, one continuous task")
table(
    ["Screen", "Essential components", "Primary next action"],
    [
        (
            "Today",
            "Inspection queue, due checks, evidence-age labels, available time and device state. Separate priority from evidence completeness.",
            "Open batch / start next check.",
        ),
        (
            "Batch Passport",
            "Quantity, QR, dated photo strip, observations, valid/invalid sessions, environmental context and confirmed outcomes.",
            "Add observation / view receipt.",
        ),
        (
            "Capture + Measure",
            "Camera preview, SAM overlay, manual correction, sampling protocol, live stabilization/recovery state and session progress.",
            "Confirm image / start authorized session.",
        ),
        (
            "Resolve Uncertainty",
            "Reason for investigation, allowed tests, A/B groups, baseline/recovery guard, relative-response comparison and stop state.",
            "Perform next test / stop unresolved.",
        ),
        (
            "Decision + Action",
            "Camera/sensor/combined cards, linked evidence, policy version, proposed action, human confirmation and quantity log.",
            "Confirm outcome / set next check.",
        ),
    ],
    [100, 269, 130],
)
h("Navigation and interaction")
add(
    "Today opens the batch; the batch opens a capture or investigation task; completion returns to the same timeline. Keep developer logs and raw diagnostics behind an Evidence details panel. Use mobile-friendly controls and a text input before adding voice."
)
h("Important empty and failure states")
add(
    "<b>No history:</b> invite an opening reference check. <b>No valid sensor data:</b> label camera-only evidence and request a check. <b>Device busy:</b> show the current task and wait queue. <b>Model unavailable:</b> keep saved evidence and offer retry. <b>Batch moved:</b> confirm identity before writing a session."
)
h("On-screen language")
add(
    'Use "routine monitoring," "prioritize inspection," "hold for human inspection" and "needs evidence." Display inspection-priority points as a heuristic, never a spoilage probability. Show uncertainty in words and give a specific next step.'
)

page("05 / MODEL INTEGRATION MAP", "Give every model a defined job")
table(
    ["Model / placement", "Input", "Output and trigger"],
    [
        (
            "SAM 3.1<br/><b>sam-3.1</b><br/>Capture and group selection",
            'Photo + short object phrase such as "tomato"; optional validated point/box prompt.',
            "Masks and boxes tied to this image. Call on a new image or corrected prompt. It does not grade freshness. [2,4]",
        ),
        (
            "Muse Spark<br/><b>muse-spark-1.3</b><br/>Visual evidence and explanations",
            "Photo/crops, mask IDs, prior image when relevant; later, validated session summary and policy result.",
            "Observable appearance, visibility limits, evidence-linked explanation. Call after new evidence; numerical scoring stays in code. [2,5]",
        ),
        (
            "Muse Wonder<br/><b>muse-wonder-1.0</b><br/>Today and Investigator",
            "Batch summaries, current state, task/time budget and allowlisted tools.",
            "Proposed tool calls and bounded next-step plan. Call for a planning task or a new investigation result. Backend validates transitions. Preview availability must be smoke-tested. [2]",
        ),
        (
            "Voice Transcribe<br/><b>muse-voice-transcribe-1.0</b><br/>Optional input",
            "User-recorded request or confirmation, with consent.",
            "Transcript displayed for confirmation. Add only after target-language testing. Text remains available. [2]",
        ),
    ],
    [150, 160, 189],
)
h("What remains normal application code")
add(
    "Batch identity, time alignment, device locking, signal features, session validity, scoring, quantity arithmetic, task persistence and action authorization. Model prose never overwrites these values."
)
h("What about Muse Image and local models?")
add(
    "Muse Image is unnecessary for this inspection workflow: retain the original evidence photos. Spark Open/Glimmer or self-hosted SAM are later options, not prerequisites. The $150 credit path uses hosted inference; no model weights need to be loaded on the laptop."
)
callout(
    "Call only when evidence changes",
    "Cache SAM by image hash + prompt + model, and Spark by the full evidence/prompt version. Reuse saved observations in Wonder summaries. Never invoke the models for every incoming sensor packet.",
)

page("06 / ARCHITECTURE", "Build around the existing platform")
code(
    "Android browser / React\n  -> FastAPI: batch, photo, task and session endpoints\n     -> evidence store + database + image storage\n     -> Meta adapter -> SAM / Spark / Wonder\n     -> session controller -> existing telemetry pipeline\n     -> policy engine -> decision + human-approved outcome\n  <- saved task state + status updates + evidence timeline"
)
table(
    ["Current project area", "Recommended change"],
    [
        (
            "frontend/src/App.jsx",
            "Reuse React/Vite shell. Extract Today, BatchPassport, CaptureMeasure, Investigation and DecisionAction components. Keep existing charts inside evidence details.",
        ),
        (
            "src/backend/api/routes.py",
            "Retain telemetry/status routes. Add batch/task/media routes before the final static frontend mount. Keep model calls server-side.",
        ),
        (
            "src/backend/persistence/models.py",
            "Add Batch, Observation, MediaAsset, Investigation, Task, Decision, Outcome and ModelCall records. Link sensor sessions explicitly to batch_id.",
        ),
        (
            "src/backend/processing/ and ingestion/",
            "Reuse raw ingestion and processing after verification. Add a session-summary adapter and device reservation; do not replace hardware transport.",
        ),
        (
            "src/backend/fusion/risk.py; biochemical/; rul/",
            "Keep old experimental outputs internal until validated. Add a separate inspection policy; remove public default percentages and exact remaining-life claims.",
        ),
        (
            "scripts/ and data/",
            "Add real API smoke tests, controlled-trial capture and evaluation exports. Separate fixture, replay and live records.",
        ),
    ],
    [202, 297],
)
h("New modules proposed for the build")
add(
    "<b>src/backend/meta/</b>: client.py, segmentation.py, vision.py, planner.py.<br/><b>src/backend/workflows/</b>: sessions.py, investigation.py, policy.py, tasks.py.<br/><b>src/backend/contracts/</b>: batch.py, observation.py, decision.py.<br/><b>frontend/src/components/</b>: the five product screens plus EvidenceDetails."
)
story.append(
    p(
        "Repository review is static: existing telemetry, persistence, SSE and dashboard code were inspected; their runtime/cloud behavior was not tested for this document. Paths above are relative to the current meta_2026 project.",
        "SmallX",
    )
)

page("07 / DATA AND API CONTRACTS", "Make evidence traceable from day one")
table(
    ["Record", "Minimum fields and invariant"],
    [
        (
            "Batch / MediaAsset",
            "batch_id, label, produce_type, quantity/unit; media_id, storage key, SHA-256, captured_at, uploaded_at, dimensions. Original photo retained; QR contains an opaque batch link.",
        ),
        (
            "Observation",
            "observation_id, batch_id, media_id, SAM response/mask IDs, Spark observations, visibility limits, model/prompt version. Item IDs valid only inside the image/session.",
        ),
        (
            "SensorSession",
            "session_id, batch_id, optional investigation/group_id, device_id, operator, phase timestamps, raw-log reference, environment, protocol_version, validity and reasons. One active reservation/device.",
        ),
        (
            "Decision / Task",
            "decision_id, evidence IDs, policy_version, component values, evidence status, priority and reason; task_id, due_at, allowed action, status, revision and owning batch.",
        ),
        (
            "Outcome / ModelCall",
            "Outcome: actor, confirmation time, action, quantity, notes, decision_id. ModelCall: model ID, provider response ID, prompt version, usage, latency, status and retry count.",
        ),
    ],
    [103, 396],
)
h("Suggested FastAPI surface - proposed, not yet implemented")
code(
    "POST /batches                     GET /batches/{id}\nPOST /batches/{id}/observations    GET /batches/{id}/history\nPOST /batches/{id}/sensor-sessions\nPOST /sensor-sessions/{id}/complete\nPOST /plans                       POST /tasks/{id}/confirm\nPOST /batches/{id}/investigations\nPOST /investigations/{id}/advance\nPOST /decisions/{id}/outcomes      GET /batches/{id}/receipt"
)
h("Receipt and access")
add(
    "Export a versioned JSON snapshot plus a readable summary. Include photo hashes, sensor-session references, model IDs, policy version and human confirmations. A hash helps detect changes; it does not certify food condition. Keep raw photos and business details behind access control; a public QR should expose only an intentionally redacted view."
)

page("08 / AGENT CONTROL", "Wonder plans; the backend executes")
add(
    "Keep authoritative state in the database. Wonder receives a compact snapshot and proposes one allowed next step. The application validates it, executes the tool and returns its real result to the model. Save state after each step so refreshes and API failures can resume."
)
table(
    ["Allowlisted tool", "Backend responsibility"],
    [
        (
            "get_batch_history(batch_id)",
            "Return dated observations, valid summaries and confirmed outcomes, with evidence IDs.",
        ),
        (
            "get_session_summary(session_id)",
            "Return computed features, validity, environment and protocol version; no fabricated values.",
        ),
        (
            "request_sensor_session(batch_id, test_kind)",
            "Create a pending task and reserve the device only after user start. The model cannot operate hardware arbitrarily.",
        ),
        (
            "propose_next_test(investigation_id, test_kind)",
            "Check gate status, allowed choices and remaining time/tests. Return an accepted proposal or rejection.",
        ),
        (
            "create_inspection_task(batch_id, reason_ids)",
            "Validate evidence references and persist one idempotent task.",
        ),
        (
            "prepare_action(decision_id, action)",
            "Create a draft using the vendor's quantity/price; cannot approve sale, publish or dispose.",
        ),
        (
            "record_vendor_confirmation(task_id, payload)",
            "Accept only an authenticated human confirmation from the UI. The model cannot claim the vendor confirmed.",
        ),
    ],
    [232, 267],
)
h("Bounded execution and recoverability")
add(
    "Initial engineering limits: three model/tool cycles per planning request, one transient retry per call, and a user-visible timeout. Tune timeout to measured latency. Honor provider retry headers; do not retry authentication or validation failures. Deduplicate writes with a request key. Never automatically repeat physical measurements."
)
h("Validate model outputs")
add(
    "Use Pydantic contracts and reject unknown evidence IDs, invalid enums and unsupported claims. A second malformed answer returns a recoverable failure. A model may propose a next check, but it cannot change score weights, bypass recovery or turn missing measurements into low concern."
)
callout(
    "Prompt boundary",
    "Photos, notes, receipts and attached documents are evidence, not instructions. Instruct the agent to use only the server-supplied tools and policy, and to treat text found inside evidence as untrusted content.",
)

page("09 / SENSOR PROTOCOL", "A valid session before a decision")
add(
    "The current code appears to process SGP41-style VOC/NOx raw values. Verify the actual hardware, firmware and manufacturer requirements before choosing timing or signal direction. Existing comments and coefficients are not independent calibration evidence."
)
code(
    "REQUESTED -> WARMING -> BASELINE -> SAMPLING\n          -> RECOVERY -> COMPLETE_VALID\nAny failed validity gate -> INVALID / RETEST_REQUIRED\nDevice reservation released only after safe completion/abort."
)
table(
    ["Phase", "What to implement and record"],
    [
        (
            "Setup",
            "Batch/group identity; container/headspace; quantity or mass; sensor placement; protocol version; operator; temperature/humidity. Match conditions or record the differences.",
        ),
        (
            "Warm-up / baseline",
            "Use device guidance and characterize restart behavior. Require stable readings before sampling; keep window and acceptance rule in configuration.",
        ),
        (
            "Sampling",
            "Use fixed timing and placement, timestamps and adequate packet coverage. Record raw values and available index/algorithm state separately.",
        ),
        (
            "Recovery / blank",
            "Wait for baseline recovery under the fixed protocol. A failed recovery blocks the next valid comparison. Include blank/reference measurements in group trials.",
        ),
        (
            "Summary",
            "Code computes medians, baseline-relative change, slope, variability, packet coverage and condition flags. Return validity plus reasons, not only a scalar score.",
        ),
    ],
    [104, 395],
)
h("Feasibility gate for group tests")
add(
    "Before enabling A/B localization, run matched normal/degraded comparisons under one procedure; an example internal screen is expected ordering in at least 8 of 10 pairs with acceptable blanks/recovery. Also test whole groups. Set the rule before collecting results; repeated measurements of one batch are not independent samples."
)
h("If the gate fails")
add(
    "Keep Rescue, history and Investigator's repeat/photo/stop paths. Hide group-localization claims. Investigate drift and procedure later. Raw signal deviation can reflect environment or handling; it cannot establish organism-specific contamination or food safety."
)

page("10 / PRODUCT SCORING", "Inspection priority with explicit uncertainty")
add(
    "There are two different scores in this plan: <b>operational priority</b> tells the vendor what to inspect; <b>strategy scoring</b> on page 17 assesses the hackathon build. Neither is a probability of spoilage."
)
h("Proposed v0 policy - an engineering heuristic to freeze and test")
table(
    ["Component", "Provisional definition"],
    [
        (
            "V: visible concern, 0-100",
            "Map validated Spark observation categories to fixed values: none observed=0, mild=35, clear concern=70, severe visible concern=100. An unusable photo is missing, never zero. Human correction is recorded.",
        ),
        (
            "S: sensor deviation, 0-100",
            "Compute x from a valid, baseline-relative session feature with characterized direction. S=100*clip((x-L)/(H-L),0,1). L/H come from development measurements for the same protocol; no S if H is not greater than L or the reference is unreliable.",
        ),
        (
            "D: historical change, 0-100",
            'With comparable prior V/S: D=min(100, 2*max(0,V_now-V_prev,S_now-S_prev)). Use available comparable channels only. An opening reference gives D=0 with "no trend yet."',
        ),
        (
            "P: combined priority",
            "When V/S/D prerequisites hold: P=0.40V + 0.40S + 0.20D. These weights are proposed, uncalibrated and versioned. If a required channel is missing, show a provisional single-channel result; do not silently renormalize.",
        ),
    ],
    [125, 374],
)
h("Decision gates come before the queue")
add(
    'Provisional bands: P&lt;30 routine monitoring; 30-59 prioritize inspection; P&gt;=60 hold for human inspection. Severe visible concern forces human inspection regardless of P. If |V-S|&gt;=40, show disagreement and an investigation task. Invalid, stale or missing evidence yields "needs evidence" and cannot clear an earlier unresolved hold.'
)
h("How to rank work")
add(
    "First surface unresolved holds and urgent inspection tasks; then acquisition tasks for missing/stale evidence; then routine checks. Within comparable tasks, sort by priority or overdue time, with value at stake as a visible tie-breaker. Wonder selects a feasible sequence within the vendor's time/device budget; code enforces these constraints."
)
story.append(
    p(
        "Example only: V=35, S=80, D=30 gives P=52. The disagreement gate still requests inspection/retest. Camera-only V and sensor-only S are separate baselines, not substitutes for the fused score. Thresholds must be revised from trials, then frozen before held-out evaluation.",
        "SmallX",
    )
)

page("11 / INVESTIGATOR + SHELFWATCH", "Investigate now; remember for later")
h("Investigator: a bounded branch of the batch workflow")
add(
    "<b>Trigger:</b> disagreement, invalid repeat or a vendor request. Wonder chooses among another photo, whole-crate repeat, validated A/B comparison or stop. It names what evidence could change the decision and the expected time cost."
)
add(
    "<b>A/B procedure:</b> SAM supplies visible masks; code suggests two practical groups; the vendor confirms membership and physically separates them. Record group quantity/mass and container conditions. Measure sequentially with one device and require recovery between tests. Alternate/randomize order in evaluation."
)
add(
    "<b>Relative suspect index:</b> compare valid group features x_A and x_B under matched conditions. The larger response ranks first only if |x_A-x_B| exceeds a development-derived repeatability margin epsilon. If epsilon or comparable valid sessions are unavailable, return inconclusive. Optional bars may show baseline-relative responses; they are not probabilities."
)
add(
    "<b>Stop rules:</b> one A/B split; at most one repeated comparison if budget remains; stop on invalid recovery, expired time budget, insufficient separation or a human stop. Never promise logarithmic search or individual-item chemical attribution. Human inspection closes the task."
)
h("ShelfWatch: memory that drives the next check")
add(
    "Start separately labeled batches immediately. Reuse the same photo setup and intermittent measurement procedure where possible. Preserve actual capture times, reference dates and environment. Batch identity persists; SAM object identities do not persist across rearranged photos."
)
add(
    "At every visit, compare new evidence with earlier observations available at that time. Initially use a simple reference-relative rule, not a claimed calibrated change-point detector. Suggest the next in-app check from unresolved status, evidence age and vendor availability; record a due time and reason."
)
add(
    "Log retained, removed, sold or otherwise disposed quantities with actor/time. Enforce stock arithmetic and prevent duplicate outcome submissions. A prepared listing is not a sale; stock value under review is not money recovered."
)
callout(
    "Longitudinal evidence may be limited",
    "If a sensor flag precedes a recorded visual change, report the observation intervals and batch count. Five days may show no event. Demonstrate history-driven follow-up without claiming an exact early-warning lead time.",
)

page("12 / API ACCESS + CREDIT USE", "Start with a server-side smoke test")
add(
    "Your screenshot shows $150 free credits in use. Create the key under the credited Meta team/project and confirm its expiry terms in the dashboard. Use the hosted API at <b>https://api.meta.ai/v1</b>. Keep the key in the backend environment; never in a VITE_ frontend variable or QR. [2,3]"
)
code(
    '# PowerShell, in an activated project environment\npython -m pip install --upgrade openai\n$env:MODEL_API_KEY = "your-key-entered-locally"'
)
code(
    '# Minimal access check; not production workflow code\nimport os\nfrom openai import OpenAI\nclient = OpenAI(\n    base_url="https://api.meta.ai/v1",\n    api_key=os.environ["MODEL_API_KEY"],\n)\nr = client.responses.create(\n    model="muse-spark-1.3",\n    input="Reply with: API access works",\n)\nprint(r.output_text)'
)
h("Wire the models in this order")
add(
    "<b>1.</b> Spark text call, then one real tomato photo. <b>2.</b> SAM stream with model sam-3.1, a noun prompt and input_image. Decode the special-token output with meta-sam-parser or @meta-sam/parser; persist real masks and render an overlay. <b>3.</b> Spark image/crops with mask IDs, validated against the observation schema. <b>4.</b> Wonder with one read-only history tool, then task proposals. [3-5]"
)
h("Important SAM integration detail")
add(
    "SAM's streamed text contains encoded segmentation, not ready-to-render plain JSON. Use the documented parser and check completion/diagnostics before saving geometry. Align mask dimensions to the oriented original image and convert scaled tap coordinates. If parsing fails, preserve the photo and offer manual selection clearly labeled as such. [4]"
)
h("Access failures should be visible")
add(
    "401/403: check the key, project and permissions. 429: bounded backoff with provider headers. Missing model access: keep a recorded fallback; Spark may temporarily run the planner with the same tool contracts. A fixture can support development but must be labeled simulated."
)

page("13 / BUILD PLAN: FOUNDATION", "Steps 1-4: get one real path working")
add(
    "Roles below are work allocations for the assumed three-person team. Keep code integration continuous; use the existing checkout and deployment only after local verification."
)
table(
    ["Step / owner / effort", "Concrete work", "Done when"],
    [
        (
            "1. Access and scope<br/>Backend 2 h + sensor 2 h",
            "Confirm credits, Spark/SAM/Wonder access and package/runtime versions. Create three batch labels, recruit pilot users and begin real photos. Record existing-versus-new work.",
            "Real API response IDs saved; at least one photo and batch record; explicit go/no-go checklist.",
        ),
        (
            "2. Sensor feasibility<br/>Sensor 4 h",
            "Characterize warm-up/baseline/recovery. Run matched trials and whole-group feasibility; preserve invalid runs. Set a protocol and decide if A/B ships.",
            "Written protocol + raw trial log; A/B enabled only on passing evidence. Stop at budget and report actual n.",
        ),
        (
            "3. Data foundation<br/>Backend 3 h + UI 2 h",
            "Add Batch/Observation/Session links and migrations. Add media storage/hashes, capture form and QR identity. Lock one device per session.",
            "Refreshing the phone preserves batch/history; one session cannot belong to the wrong batch or group.",
        ),
        (
            "4. Perception path<br/>Backend 3 h + UI 3 h",
            "Add Meta adapter, SAM parsing and canvas overlay; Spark observation schema. Validate and persist image-linked observations; allow correction.",
            "Real photo -> saved masks -> evidence observations -> batch timeline; parser/model failures recover.",
        ),
    ],
    [113, 237, 149],
)
h("Calendar gates")
add(
    "<b>31 October:</b> access checks, feasibility and first data collection. <b>1 November:</b> one real photo-to-session-to-decision path works. These are milestone targets; carry incomplete work forward explicitly rather than labeling it finished."
)
callout(
    "First vertical slice",
    "Register one batch, upload one image, save real SAM/Spark output, attach one valid sensor session and render an evidence-linked provisional inspection decision. Finish this before broadening the interface.",
)

page("14 / BUILD PLAN: COMPLETE THE LOOP", "Steps 5-9: decisions, follow-up and release")
table(
    ["Step / owner / effort", "Concrete work", "Done when"],
    [
        (
            "5. Session + policy<br/>Backend 4 h + sensor 4 h",
            "Implement validity summaries, conflict gates and three-way cards. Replace offline/default readings with missing states. Remove unsupported life/safety claims, including the SNS alert template in routes.py.",
            "Invalid/stale sessions cannot look normal; a decision references actual evidence and policy version.",
        ),
        (
            "6. Agent + history<br/>Backend 3 h + UI 3 h",
            "Wonder history/task tools, bounded loop, persistent due checks and replayable trace. Add vendor confirmation, quantity ledger and receipt.",
            "A real new observation changes or preserves a persisted plan; confirmed outcome appears next visit.",
        ),
        (
            "7. Investigation branch<br/>Sensor 2 h + UI 2 h",
            "Always ship guided repeat/photo/stop. Add one A/B split only if gate passed; group membership, recovery and stop rules enforced.",
            "Invalid result rejected; clear comparison or inconclusive shown. Optional voice replaces polish time only.",
        ),
        (
            "8. Evaluation + user trial<br/>All roles 10 h total",
            "Freeze policy. Run held-out same-case ablations and chronological checks; record vendor tasks, failures, latency, usage and actual sample counts.",
            "Results include wrong/unresolved cases and denominators; no development batches leak into held-out set.",
        ),
        (
            "9. Demo + release<br/>All roles 8 h total",
            "Fix critical failures, record a three-minute story, prepare setup/limitations and sanitize evidence. Test phone access and published setup.",
            "Fresh install/deployed path checked; demo and submission assets ready with clearly labeled replays.",
        ),
    ],
    [113, 237, 149],
)
h("Remaining calendar")
add(
    "<b>2 November:</b> complete queue, human actions and due-check history; freeze evaluation policy. <b>3 November:</b> trials, pilot tasks and only already-stable optional features. <b>4 November:</b> feature freeze by midday, fix and record; submit that evening IST. Deadline: 5 November, 7:30 AM IST. [1]"
)
story.append(
    p(
        "Steps 1-9 total 55 person-hours; retain 5 hours of shared buffer = 60. This is a constrained prototype target. If the team has fewer remaining hours, cut A/B localization, voice and visual polish first; keep batch memory, inspection workflow, retest path and outcome closure.",
        "SmallX",
    )
)

page("15 / VERIFICATION", "Prove the complete loop, including failures")
table(
    ["Question / experiment", "Protocol and report"],
    [
        (
            "Does the instrument separate conditions?",
            "Target 10 matched pairs if feasible, with blanks/recovery and whole-group checks. Log batch count, repeats, order and invalid runs. This is feasibility evidence, not validation accuracy.",
        ),
        (
            "Does combining inputs help?",
            "Aim for 12-20 distinct-batch cases if available. Freeze policy first; split by batch. Compare image-only, sensor-only and combined against a blinded human inspection checklist. Report correct/wrong/unresolved counts and coverage on all cases.",
        ),
        (
            "Does investigation help?",
            "Compare adaptive test choices with a fixed A/B procedure. Report group identification, unresolved rate, number of measurements and full elapsed time including recovery. Reveal hidden assignment only afterwards.",
        ),
        (
            "Does memory change follow-up?",
            "Evaluate decisions chronologically using only evidence available then. Compare age-only FIFO, fixed schedule and evidence-based queue. Record whether due checks completed and which actions were confirmed.",
        ),
        (
            "Can a vendor use it?",
            "Aim for 2 vendors x 3 tasks if access permits. Record completion, time, corrections and feedback. Use a counterbalanced usual-process comparison where practical. Teammates are proxy users, not vendors.",
        ),
        (
            "Will the demo recover?",
            "Exercise timeout, malformed model response, missing photo, stale session, duplicate confirmation, device contention and disconnect. Record observed recovery and latency/cost per completed task.",
        ),
    ],
    [160, 339],
)
h("Small results table to publish")
code(
    "Variant       Correct   Wrong   Unresolved   Total   Median time\nImage-only      TBD      TBD       TBD        TBD       TBD\nSensor-only     TBD      TBD       TBD        TBD       TBD\nCombined        TBD      TBD       TBD        TBD       TBD"
)
add(
    "Do not fill these cells with target scores. Human inspection is a proxy reference for prioritization, not microbial ground truth. Include actual n when targets are missed. With few tasks, publish raw timings/median rather than an unstable p95. Report observed disposition, not inferred waste reduction."
)

page("16 / STRATEGY SCORECARD", "A unified target without invented results")
add(
    "Retain the source document's planning rubric: Impact, Tooling, Depth and Demo on 0-10. Assumed total = <b>0.30 Impact + 0.20 Tooling + 0.25 Depth + 0.25 Demo</b>. These are editorial weights, not verified organizer weights. The official event page describes broader track criteria. [1]"
)
table(
    ["Approach", "Impact", "Tooling", "Depth", "Demo", "Target total"],
    [
        ("Rescue / source target", "9.0", "9.0", "9.0", "9.8", "9.20"),
        ("Investigator / source target", "8.5", "9.2", "9.5", "9.0", "9.03"),
        ("ShelfWatch / source target", "9.0", "8.8", "8.8", "9.0", "8.90"),
        ("Unified product / conditional", "9.0", "9.2", "9.3", "9.8", "9.32"),
    ],
    [164, 62, 65, 62, 62, 84],
)
add(
    "The combined target deliberately stays at the earlier Rescue + validated Probe target. Adding full batch memory improves coherence; it does not automatically raise the score. The current implementation remains unscored until tested."
)
table(
    ["Metric", "What earns the unified target", "What lowers it"],
    [
        (
            "Impact / 9.0",
            "Vendor completes a useful priority-to-action task and a follow-up. Publish observed task benefit and quantities.",
            "Only proxy users; no completed action; hypothetical savings.",
        ),
        (
            "Tooling / 9.2",
            "Real SAM masks, Spark evidence and Wonder tool loop with persistent state, validation and recovery.",
            "Decorative model calls; fabricated tool results; no failure path.",
        ),
        (
            "Depth / 9.3",
            "Controlled sensor protocol, valid A/B branch, same-case ablation and chronological memory checks.",
            "No group feasibility or held-out cases; hidden unresolved results.",
        ),
        (
            "Demo / 9.8",
            "Clear three-minute end-to-end task, real evidence, approved action and concise results.",
            "Unexplained replay, unstable flow or too many disconnected screens.",
        ),
    ],
    [89, 223, 187],
)
h("How to use the scorecard")
add(
    "Re-score after trials with a short evidence link for each metric. If A/B fails, lower Depth rather than preserving 9.32 by assertion. If follow-up data is absent, describe ShelfWatch as functioning memory with longitudinal evidence pending. For an individual/student team, Indie appears aligned; confirm accepted track and submission rules in the participant portal."
)

page("17 / BUDGET + DEMONSTRATION", "Spend credits on proof and useful calls")
table(
    ["Model usage", "Published standard price [6]", "Illustrative quantity / cost"],
    [
        ("SAM image segmentation", "$2.50 / 1,000 images", "1,000 image requests = $2.50"),
        ("Muse Spark tokens", "$1.25 input; $4.25 output / 1M", "1M input + 0.2M output = $2.10"),
        ("Muse Wonder tokens", "$4 input; $20 output / 1M", "0.3M input + 0.1M output = $3.20"),
        ("Voice Transcribe / optional", "$0.18 / audio hour", "2 hours = $0.36"),
    ],
    [139, 188, 172],
)
add(
    "The example workload totals <b>$8.16</b>, not a forecast: count image tokenization, actual reasoning/output usage and retries from provider records. Set an internal development budget of $25, evaluation $50, demo/recovery $25 and reserve $50. These are planning envelopes, not spending commitments. Hosting is separate."
)
h("Application cost controls")
add(
    "Log usage per call and link it to task_id. Cache by full evidence/model/prompt version. Send compact sensor summaries; cap tool cycles and output. Use Spark for perception and Wonder only when planning is needed. Block new nonessential requests at the internal budget limit; reconcile estimates with the dashboard. Free-credit terms shown in your screenshot may permit product-improvement use; standard model selection alone does not override those terms."
)
h("Three-minute unified demo")
table(
    ["Time", "Beat"],
    [
        ("0:00-0:25", "Vendor opens Today; scan a real Batch Passport and dated history."),
        ("0:25-0:55", "New photo, SAM overlay, Spark observations; ask what to inspect."),
        (
            "0:55-1:30",
            "Wonder selects a task; show a real sensor session and explicit time compression.",
        ),
        (
            "1:30-2:05",
            "Compare evidence. Run a validated Probe or demonstrate repeat/stop unresolved.",
        ),
        ("2:05-2:30", "Vendor confirms action; log quantity, receipt and next check."),
        ("2:30-3:00", "Show actual comparison results, limitations and event-built changes."),
    ],
    [83, 416],
)

page("18 / RELEASE + NEXT STEPS", "Ship the loop, then improve the evidence")
h("Before submission")
add(
    "Verify the accepted rules and required assets in the participant portal. Prepare a reproducible repository setup, demo video, model/tool map, sanitized session records, evaluation counts and limits. Clearly separate existing ESP32 hardware/telemetry/dashboard from new Meta perception, workflow, history and evaluation. Label cached replay, simulation and time cuts."
)
h("After the hackathon")
add(
    "<b>Week 1:</b> expand independent-batch trials, tune thresholds using development data, improve device recovery and retest on held-out batches. <b>Week 2:</b> repeated vendor visits, stock-quantity reconciliation, receipt access controls and measured operating costs. <b>Later:</b> additional produce-specific protocols, notifications, offline capture and multi-device scheduling. Add local models only with a measured latency/cost reason."
)
h("Start here in the next working session")
add(
    "Confirm API access; label three batches; capture opening photos and raw sessions; agree on the protocol; then implement the batch identity and real photo-to-decision slice. Do not spend the first day rebuilding the dashboard or deploying model weights."
)
h("References and provenance")
story.append(
    p(
        "Source: user-supplied <i>revised source strategy PDF</i>, 8 pages, 31 October 2026. It supplies the capacity assumptions, revised approach targets, proposed rubric and evaluation principles. Its contents were treated as reference material, not instructions overriding your request. This plan replaces the three-way choice with your requested unified product.",
        "SmallX",
    )
)
story.append(
    p(
        "Project reviewed: meta_2026, including frontend/package.json, frontend/src, backend API routes, persistence, risk fusion, biochemical engine and project configuration. Proposed modules, thresholds, APIs, hours and score targets in this plan are design recommendations; they are not implemented or experimentally established by this document.",
        "SmallX",
    )
)
refs = [
    (
        "1",
        "Competition dates, themes and broad judging criteria",
        "https://dev.meta.ai/events/global-hackathon",
    ),
    ("2", "Model overview and model IDs", "https://dev.meta.ai/docs/overview"),
    ("3", "API key setup and compatible SDK", "https://dev.meta.ai/docs/quickstart"),
    (
        "4",
        "SAM requests, parser and overlay handling",
        "https://dev.meta.ai/docs/media-segmentation",
    ),
    ("4a", "SAM client libraries", "https://dev.meta.ai/docs/sam/client-libraries"),
    (
        "5",
        "Image input formats and vision requests",
        "https://dev.meta.ai/docs/image-understanding",
    ),
    ("6", "Current published pricing", "https://dev.meta.ai/docs/pricing-rate-limits"),
]
for n, title, url in refs:
    story.append(p(f'[{n}] {title}: <link href="{url}" color="#087E69">{url}</link>', "SmallX"))
story.append(
    p(
        "Official pages checked 31 October 2026. Model access, prices and competition terms can change; recheck in the credited account and participant portal before release.",
        "SmallX",
    )
)


def footer(c, doc):
    w, h = doc.pagesize
    c.setStrokeColor(LINE)
    c.line(48, h - 39, w - 48, h - 39)
    c.setFillColor(MUTED)
    c.setFont("Body", 8)
    c.drawString(48, h - 29, "PRODUCT BUILD PLAN  /  NAME TO BE DECIDED")
    c.line(48, 40, w - 48, 40)
    c.drawString(48, 27, "31 OCT 2026  |  PROPOSED DESIGN - EVIDENCE BEFORE CLAIMS")
    c.setFont("Bold", 8)
    c.drawRightString(w - 48, 27, str(doc.page))


doc = SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=48,
    leftMargin=48,
    topMargin=58,
    bottomMargin=55,
    title="Product Build Plan",
    author="Project team",
    subject="Rescue, Investigator and ShelfWatch: unified workflow, model integration and delivery plan",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
