# Databricks notebook source
"""
Commercial Pharma Workshop -- Synthetic commercial PDF corpus for Knowledge Assistant (KA).

Generates five extensive, operationally realistic PDF documents on the Unity Catalog volume
``/Volumes/serverless_stable_uwu9jo_catalog/wsp_commercial/documents``.

Requires network access for ``pip install`` on first run.
"""

import subprocess

subprocess.check_call(["pip", "install", "fpdf2"])

from fpdf import FPDF
import os
from datetime import date
from typing import Callable, List, Sequence, Tuple

dbutils.widgets.text("catalog", "pharma_workshop", "Catalog Name")
CATALOG = dbutils.widgets.get("catalog").strip()
assert CATALOG, "ERROR: Please provide a catalog name in the widget above before running."
SCHEMA = "wsp_commercial"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/documents"


class CommercialPDF(FPDF):
    """A4 portrait PDF with titled footer page x / {nb}; built-in fonts only."""

    def __init__(self, footer_tag: str) -> None:
        super().__init__()
        self.footer_tag = footer_tag
        self.set_margins(12, 12, 12)
        self.set_auto_page_break(auto=True, margin=16)
        self.alias_nb_pages()
        self._in_footer = False

    def footer(self) -> None:
        self._in_footer = True
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        txt = f"{self.footer_tag}  |  Page {self.page_no()}/{{nb}}"
        self.cell(0, 10, txt, new_x="LMARGIN", new_y="NEXT", align="C")
        self._in_footer = False


def _ensure_volume() -> None:
    os.makedirs(VOLUME_PATH, exist_ok=True)


def _out_pdf(name: str) -> str:
    return os.path.join(VOLUME_PATH, name)



def _p(pdf: CommercialPDF, text: str, size: int = 9) -> None:
    pdf.set_font("Times", "", size)
    pdf.multi_cell(0, 4.4, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.0)


def _h1(pdf: CommercialPDF, title: str) -> None:
    pdf.ln(2.5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 6.5, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)


def _h2(pdf: CommercialPDF, title: str) -> None:
    pdf.ln(1.8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 5.5, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.0)


def _bullets(pdf: CommercialPDF, items: Sequence[str], size: int = 9) -> None:
    pdf.set_font("Helvetica", "", size)
    for it in items:
        pdf.multi_cell(0, 4.3, f"- {it}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _title_page(
    pdf: CommercialPDF, main: str, subtitle: str, lines: Sequence[str]
) -> None:
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_x(15)
    pdf.ln(32)
    pdf.set_font("Times", "B", 21)
    pdf.multi_cell(0, 9, main, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 5.5, subtitle, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(16)
    pdf.set_font("Helvetica", "", 9)
    for ln in lines:
        pdf.multi_cell(0, 5, ln, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(
        0,
        4.5,
        f"Confidential -- Commercial Operations -- Synthetic workshop artifact -- {date.today().isoformat()}",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )


def _toc_pages(pdf: CommercialPDF, entries: Sequence[Tuple[str, int]]) -> None:
    pdf.add_page()
    _h1(pdf, "Table of Contents")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        0,
        4.5,
        "This table of contents lists major sections with opening page numbers. Pagination follows the footer on each "
        "page for full traceability during MLR and SOX-controlled distribution.",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)
    pdf.set_font("Courier", "", 9)
    for title, pg in entries:
        entry = f"{title}{'.' * max(1, 92 - len(title) - len(str(pg)))}{pg}"
        pdf.multi_cell(0, 4.2, entry[:110], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(
        0,
        4,
        "Note: Subsection headings appear in the body text beneath each major section and inherit the same governance ID.",
        new_x="LMARGIN",
        new_y="NEXT",
    )


def _two_pass(
    filename: str,
    footer_tag: str,
    title_main: str,
    title_sub: str,
    title_lines: Sequence[str],
    sections: Sequence[Tuple[str, Callable[[CommercialPDF], None]]],
) -> str:
    """First pass records section start pages; second pass inserts accurate TOC after title."""

    def run_body(pdf: CommercialPDF, log_starts: bool) -> dict:
        starts = {}
        pdf.add_page()
        for sec_title, renderer in sections:
            if log_starts:
                starts[sec_title] = pdf.page_no()
            _h1(pdf, sec_title)
            renderer(pdf)
        return starts

    p1 = CommercialPDF(footer_tag)
    _title_page(p1, title_main, title_sub, title_lines)
    starts = run_body(p1, True)
    del p1

    p2 = CommercialPDF(footer_tag)
    _title_page(p2, title_main, title_sub, title_lines)
    _toc_pages(p2, [(t, starts[t] + 1) for t, _ in sections])
    p2.add_page()
    for sec_title, renderer in sections:
        _h1(p2, sec_title)
        renderer(p2)

    path = _out_pdf(filename)
    p2.output(path)
    return filename


def build_launch_playbook() -> str:
    fn = "Commercial_Pharma_Product_Launch_Playbook.pdf"

    def s01_exec(pdf: CommercialPDF) -> None:
        _h2(pdf, "North Star, revenue model, and cross-functional accountability")
        _p(
            pdf,
            "This playbook defines the 0-36 month commercialization pathway for Nexara (fictional small-molecule JAK1 "
            "preferential inhibitor) in moderate-to-severe rheumatoid arthritis (RA), anchored on illustrative U.S. "
            "ASO revenue of $412M in launch Year 1 escalating to $1.05B by Year 3 under a base case where FDA approval "
            "lands in August 2026 with a Risk Evaluation and Mitigation Strategy (REMS) limited to hepatotoxicity "
            "monitoring rather than full Elements to Assure Safe Use (ETASU). The franchise leadership team (FLT) "
            "operates under a Stage-Gate governance matrix with sign-off from Medical Affairs (MA), Global Value "
            "& Access (GV&A), Legal, Compliance, Regulatory Advertising and Promotion (RAP), and Finance. Portfolio "
            "scenario work completed in December 2025 assigned Nexara a probability-adjusted net present value (PA-NPV) "
            "of $2.4B against a hurdle rate of 9.5% real, with downside sensitivity to gross-to-net (GTN) bleed "
            "exceeding 64% and upside tied to acceleration of biologic switch rates in Medicare Advantage (MA) "
            "specialty tiers.",
        )
        _p(
            pdf,
            "The strategic imperatives for launch are: (1) secure favorable American College of Rheumatology (ACR) "
            "guideline-adjacent scientific partnerships, EULAR-aligned symposia presence, and high-quality continuing medical "
            "education (CME) relationships that reinforce positioning as an oral with efficacy approaching certain IL-6 "
            "inhibitors in MTX-inadequate responders; (2) operationalize a hub-lite patient services model projected to "
            "reduce time-to-therapy by 38% versus legacy prior authorization (PA) call center routing; and (3) defend "
            "market access through contracting tactics that preserve weighted average net price within +/-4.2% of the "
            "$3,214 WAC pack price at launch, inclusive of mandated 340B carve complexity and Medicaid best price (BP) "
            "guardrails. Competitive war-gaming in Q4 2025 concluded that two entrenched oral JAK competitors and one "
            "oral TYK2 agent will collectively retain 47% share-of-voice (SOV) unless we increase digital non-personal "
            "promotion (NPP) TRx lift by at least 11 percentage points in deciles 7-10 rheumatologists.",
        )
        _p(
            pdf,
            "Commercial readiness is scored quarterly using the Launch Excellence Index (LEI), a 62-item rubric spanning "
            "medical/legal review cycle time, sales training competency assessments, sampling chain-of-custody audits, "
            "and payer pull-through metrics. A composite LEI above 86% is required to unlock Wave 2 geography expansion "
            "beyond 142 U.S. territories. Historical analogs from three sister launches (2019-2023) show that each "
            "5-point LEI shortfall at Month -3 correlated with a 2.3 Nielsen TRx index deficit by Month +6. The "
            "program management office (PMO) consolidates RAID logs, including 27 active risks such as FDA class-wide "
            "label changes for major adverse cardiovascular events (MACE), which could compress the treatable population "
            "by 19% if mirrored language is adopted.",
        )
        _p(
            pdf,
            "Franchise governance includes a monthly Launch Steering Committee (LSC), weekly integrated deployment calls "
            "for field reimbursement managers (FRMs) aligned 1:4 with primary care overlay in select accountable care "
            "organization (ACO) hotspots, and daily command-center coverage for the first 120 days post-DEA schedule "
            "confirmation. Forecasting uses a Bayesian dynamic elasticity model calibrated to weekly specialty pharmacy "
            "shipments, with posterior updates to gross demand whenever switch matrices from IQVIA LAAD shift more than "
            "80 basis points versus prior week.",
        )
        _bullets(
            pdf,
            [
                "Year-1 operating plan assumes 64% gross-to-net after rebates, vouchers, and PAP leakage -- stress-test at "
                "69% still clears hurdle NPV by $180M due to mix shift toward commercial lives.",
                "Medical strategy prioritizes symposia on hepatic monitoring algorithms co badged with hepatology KOLs in eight "
                "tertiary clusters where ALT elevation reporting sensitivity is historically high.",
                "Omnichannel allocation: 41% personal promotion, 28% digital/NPP, 17% congress and peer-to-peer, 14% access "
                "enablement tools.",
                "Forecast band (P10-P90) for Week 26 TRx ranges from 11.4K to 18.9K scripts under FDA approval timing "
                "variance alone.",
            ],
        )

    def s02_market(pdf: CommercialPDF) -> None:
        _h2(pdf, "Sizing, segmentation, and growth drivers")
        _p(
            pdf,
            "The addressable U.S. RA biologic/oral advanced therapy market is modeled at $18.7B in 2026E revenue at "
            "manufacturer level, growing at a 4.1% CAGR through 2030 before patent cliffs for two anti-TNFs flatten "
            "mix. Nexara's immediate serviceable obtainable market (SOM) focuses on 1.05M diagnosed adults with "
            "moderate-to-severe disease activity (DAS28-CRP >5.1 or CDAI >22) who have failed conventional synthetic "
            "DMARDs; within this universe, approximately 410K are actively treated with targeted therapy and 218K rotate "
            "or augment annually, representing the primary switch pool for oral agents. Epidemiology triangulation uses "
            "both claims (Komodo closed-claim corridor) and EMR haystacks calibrated to CDC NHANES-derived prevalence.",
        )
        _p(
            pdf,
            "Segmentation is a K-means++ clustering on 14 attributes including prior biologic class exposure, steroid "
            "burden, seropositivity, payer channel, urbanicity, digital channel affinity, and hub friction score. The "
            "four commercial segments are: (A) Biologic-experienced rapid switchers (31% of target, highest potential); "
            "(B) cDMARD-holdouts with cardiovascular comorbidity flags (22%); (C) Medicaid-heavy safety-net panels (15%, "
            "access-constrained); (D) Integrated delivery network (IDN) leverage accounts where formulary control is "
            "centralized (32%). Segment A is projected to generate 56% of gross margin despite representing under a third "
            "of patients due to persistence curves showing 71% still on therapy at month 9 versus 58% in segment C.",
        )
        _p(
            pdf,
            "Share trajectory modeling incorporates dual elasticity: promotional response (decile-level call detail "
            "attribution) and access friction (PA reversal rates by plan). Elasticity priors were informed by analog "
            "launches revealing TRx lift of 0.84% per additional high-value touch in RA oral introductions post-2020. "
            "Payer concentration is top-heavy: the top 12 pharmacy benefit managers (PBMs) influence roughly 78% of "
            "commercial covered lives for specialty tiers, with three accounts requiring outcomes-based contracting pilots "
            "for any preferred formulary slot.",
        )
        _p(
            pdf,
            "International reference pricing pressure is not binding at Day 1 but flagged as Year 2 risk if CMS "
            "International Price Index demonstration breadth expands; internal sovereign pricing corridors already bound "
            "US net to remain >=128% of blended EU5 net to avoid Most Favored Nation knock-on exposure under political "
            "stress scenarios.",
        )
        _bullets(
            pdf,
            [
                "Baseline peak TRx share assumption: 7.8% within advanced oral sub-class by Week 52 under mid access.",
                "Competitor count with active direct-to-consumer (DTC) in RA adjacency: 3 brands elevating unaided awareness "
                "benchmark to 41%.",
                "Specialty distribution: 68% limited distribution network (LDN), 22% open, 10% cash/off-channel leakage "
                "containment through voucher redesign.",
            ],
        )

    def s03_position(pdf: CommercialPDF) -> None:
        _h2(pdf, "Core creative, claims architecture, MLR traceability")
        _p(
            pdf,
            "Positioning centers on precision oral immunomodulation with a differentiated hepatic monitoring protocol "
            "versus legacy JAK class perceptions. The scientific narrative stack ladders from mechanism (selective JAK1 "
            "inhibition with 27-fold functional selectivity over JAK2 in ex vivo assays per Technical Monograph 3.2) to "
            "clinical outcomes (ACR20/50/70 at Week 24 of 68%/44%/24% versus placebo-adjusted increments of 21%/19%/16% "
            "in the pivotal RA-ARROW study, N=1,842 randomized). Claims inventory is tiered: Tier 1 = label-faithful "
            "efficacy statements; Tier 2 = health economic / humanistic (Work Productivity and Activity Impairment "
            "Questionnaire -- WPAI) with required disclaimers; Tier 3 = contextual background only. Every asset carries "
            "a Structured Content ID in Veeva PromoMats, lineage-linked to reference packets that include annotated "
            "prescribing information, statistical analysis plan excerpts, and fair balance modules.",
        )
        _p(
            pdf,
            "Competitive differentiation messaging avoids direct comparative superiority language unless supported by "
            "head-to-head data; per Legal guidance, immunogenicity and certain infection rate deltas may be conveyed "
            "only in a balanced FAQ intended for MSL use with scientific exchange guardrails. Emotional resonance testing "
            "(n=180 rheumatologists, Q4 2025) showed highest motivation lift from 'confidence in predictable ALT recovery "
            "patterns' (+14 points on 0-100 motivation scale) versus functional lifestyle imagery alone (+6 points). "
            "Accordingly, visual identity pairs calm clinical palette (azure/sterling) with modular explanatory graphics on "
            "hepatic lab cadence, not fear-based creative.",
        )
        _p(
            pdf,
            "Core message pillars: (1) Durable disease activity control with sustained ACR responses through Week 52 in "
            "completers; (2) Oral convenience without infusion center burden for appropriate biologic-experienced patients; "
            "(3) Established monitoring protocol integrated into EMR order sets--rollout with Epic SmartSets in 11 "
            "IDNs covering 19% of target specialists by Month +2.",
        )
        _bullets(
            pdf,
            [
                "Scientific platform approval velocity target: <=96 hours from submission to MLR provisional stamp for Tier 1 "
                "modular blocks.",
                "Message recall at Month +3: aided brand linkage >=52% among targeted deciles; corrective training if <48%.",
                "Label-bound fair balance must accompany any efficacy claim in omnichannel bursts >=30 seconds consumer "
                "attention.",
            ],
        )

    def s04_hcp(pdf: CommercialPDF) -> None:
        _h2(pdf, "Affinity, prioritization, and channel orchestration")
        _p(
            pdf,
            "Target HCP universe: 9,420 U.S. adult rheumatologists and 4,850 high-volume advanced-practice providers "
            "(APPs) operating in co-management models; of these, 3,310 are designated Priority A with behavioral "
            "signals of oral switch openness (Rx detail-level preference scores >0.62). Affinity scoring blends "
            "Share-of-Switch potential (40%), scientific engagement depth (25%), access climate in top plans (20%), and "
            "historical sales force effectiveness (15%). Inside 41 major metro areas, decile bucketing is refreshed every "
            "28 days using prescription cuts not older than 17 days lag.",
        )
        _p(
            pdf,
            "Personal promotion footprint launches with 196 specialty reps (headcount) and 48 clinical nurse educators "
            "(CNEs) deployed to academic centers exceeding 340 complex RA patients annually. Call plan frequency targets: "
            "Priority A @ 7.2 effective calls per rotation (ECR) per quarter, Priority B @ 4.1, Priority C sampled via "
            "hybrid remote. Budgeted speaker bureau delivers 1,420 promotional programs Year 1 with 63% live virtual to "
            "contain travel compliance variance and Sunshine aggregation optics.",
        )
        _p(
            pdf,
            "Non-personal promotion stack leverages programmatic endemic display (Doximity, Medscape), high-intent search, "
            "and sequenced email journeys gated by engagement state machines; suppression rules honor opt-out flags within "
            "15 minutes SLA. Peer-to-peer mini-fellowships (45 minutes) with asynchronous case submission show 18% higher "
            "intent-to-prescribe deltas in pilot versus classic dinner programs, supporting scaled rollout.",
        )
        _bullets(
            pdf,
            [
                "MSL alignment: 1 MSL per 62 Priority A rheumatologists; unsolicited request documentation rate audited "
                "quarterly at <=0.35% error.",
                "Digital decile overlay increases NPP reach by 3.1x without violating Anti-Kickback routing if fair market "
                "value FMV caps respected on sponsored clinical tools.",
            ],
        )

    def s05_prelaunch(pdf: CommercialPDF) -> None:
        _h2(pdf, "Readiness gates, alignment forums, distribution stress tests")
        _p(
            pdf,
            "Pre-launch readiness pursues nine formal gates from G-6 months to G-Day 0. Gate 5 (completed January 2026) "
            "validated 340B duplicate discount prevention logic in ERP, confirming ASP reporting compatibility and "
            "alternate inventory tagging for contract pharmacy leakage <0.7%. Gate 7 executes a full-scale distribution "
            "simulation with two specialty wholesalers and one alternate site-of-care aggregator, achieving cold-chain "
            "exception rate below 0.04% across 1,200 simulated shipments.",
        )
        _p(
            pdf,
            "Internal alignment forums include Voice-of-Customer playback sessions synthesizing 62 advisory board transcripts, "
            "with thematic coding around safety anxiety (42% of remarks), reimbursement anxiety (31%), and competitive "
            "oral crowding (19%). Field advisory boards sign confidentiality addenda with 24-month survivorship. Training "
            "includes spaced learning micro-modules achieving 91% first-pass certification; poor performers enter "
            "remediation within 5 business days.",
        )
        _p(
            pdf,
            "Packaging artwork, lot serialization, and pedigree data interchanges were validated against DSCSA 2025 "
            "stabilization guidance; Serialization Event Reporting packet time is targeted <35 minutes average per batch "
            "release.",
        )
        _bullets(
            pdf,
            [
                "SOX control: SDN screening attestation for all HCP-facing contractors prior to sampling authorization.",
                "Affiliate readiness: Puerto Rico import license verification and localized adverse-event routing to "
                "pharmacovigilance queue PR-12.",
            ],
        )

    def s06_launch_exec(pdf: CommercialPDF) -> None:
        _h2(pdf, "Cadence, sales quality management, and omnichannel surge")
        _p(
            pdf,
            "Launch execution follows a 120-day surge model with tiered command-center staffing: Days 0-30 emphasize "
            "distribution continuity, pharmacovigilance intake pacing, and triangulation of early switch velocity against "
            "weekly TRx benchmarks. The first-fill target is 4,200 patients by Day 28 assuming LDN fill rates of 91% and "
            "hub-assisted benefit verification turnaround under 38 hours median. Daily stand-ups review signals from "
            "specialty pharmacy switches, payer edit rejections (>4.1% triggers escalation), and HCP teledetail "
            "attendance versus plan. Wave 1 deploys to Great Lakes, Mid-Atlantic, and Pacific Northwest clusters where "
            "prior market research indicated 14% higher willingness-to-switch among biologic-fatigued patients.",
        )
        _p(
            pdf,
            "Sales Quality Management (SQM) uses recorded sample interactions and Veeva CRM call notes scored with NLP "
            "classifiers calibrated on 22,000 historic RA encounters; call quality index (CQI) must remain >=46 to avoid field "
            "audit flags. Coaching loops close within 72 hours for any CQI below 40. Omnichannel surge budgets allocate "
            "incremental $18.4M between Weeks 2-10 to endemic content and paid search where unaided awareness lags "
            "forecast by more than 6 points in monitored metros. Promotional tempo respects Anti-Kickback safe harbor for "
            "samples and ensures HCP meals remain under FMV caps with attendee lists pre-cleared by Compliance.",
        )
        _p(
            pdf,
            "Issues management for launch includes proactive media monitoring and scientific rumor abatement; any "
            "Twitter/X clinician thread exceeding 50,000 impressions with safety keywords routes to Medical Communications "
            "within 90 minutes. Supply continuity playbooks outline allocation if a manufacturing site deviation constrains "
            "inventory such that weeks on hand fall below 4.2 (WOH) -- priority patients identified by prescriber attestation under "
            "ethical prioritization principles endorsed by Bioethics Council review.",
        )
        _p(
            pdf,
            "International launch sequence is gated: Canada and Australia trail US by 6-9 months pending pricing; no "
            "gray-market diversion controls are relaxed despite early demand pull from cross-border clinics. Affiliate "
            "monthly business reviews compare TRx per rep equivalent versus US pace with normalized access difficulty "
            "indices.",
        )
        _bullets(
            pdf,
            [
                "Early TRx share checkpoints: Week 4 >=1.2%, Week 12 >=3.8%, Week 26 >=6.4% in modeled universe.",
                "SQM: >=98% of representatives complete adverse event reporting simulation with zero critical errors before "
                "sampling privilege renewal.",
                "Digital surge cap: frequency caps at 18 impressions/week/HCP in endemic to prevent creative fatigue.",
            ],
        )

    def s07_access(pdf: CommercialPDF) -> None:
        _h2(pdf, "Payer contracting, channel economics, and pull-through")
        _p(
            pdf,
            "Market access strategy sequences P&T submissions to the 38 plans representing 71% of covered commercial "
            "specialty lives, with pharmacoeconomic dossiers highlighting incremental cost per ACR responder and "
            "work-loss day reduction modeled at 11.3 days annually versus prior oral comparators in maintenance. Proposed "
            "rebate constructs cluster around 38-44% off WAC for preferred positioning with step-through policies softened "
            "where prior authorization data shows 63% reversal burden on competing orals. Medicaid AMP/BP forecasts embed "
            "a 7.2% statutory discount stack and conservative URA assumptions; any state with carve-out risk triggers "
            "supplemental government affairs playbooks within 10 business days.",
        )
        _p(
            pdf,
            "Medicare Part D scenario analysis maps coinsurance exposure under specialty tiers; patient out-of-pocket "
            "support utilizes copay cards capped at $15 per fill for commercially eligible with income attestation, while "
            "foundation assistance routes observe OIG guidance and segregated ledger controls. 340B integrity includes "
            "duplicate discount checks and carve-in language for contract pharmacy subnetworks where chargeback error "
            "historically reached 1.4% in legacy portfolios.",
        )
        _p(
            pdf,
            "Pull-through integrates FRM co-call coaching with live ePA widgets surfaced in EHR where approved; plan-level "
            "win rates tracked weekly with heat maps fed to Key Account Directors. Gross-to-net stress tests at 66% and "
            "71% severities model EBITDA sensitivity and inform tail rebate escape clauses tied to market share hurdles "
            "below 4.5% at Month +9.",
        )
        _p(
            pdf,
            "Value-based contracting pilots are scoped with two national payers covering 12M lives, using retrospective "
            "cohorts for flare-related medical spend; data sharing via HIPAA-compliant tokenization preserves member "
            "privacy while enabling 95% confidence interval overlap on intent-to-treat cohorts at 18 months.",
        )
        _bullets(
            pdf,
            [
                "Target formulary win rate by Day 180: >=62% unrestricted or favorable tier on top national formularies.",
                "Hub cost-to-serve modeled at $138 per initiated patient in Year 1; continuous improvement Kaizen aims for "
                "-11% by Year 2.",
                "PAP eligibility aligns with IRS Section 501(r) community benefit reporting for any hospital-owned plans in "
                "pilot corridors.",
            ],
        )

    def s08_kpis(pdf: CommercialPDF) -> None:
        _h2(pdf, "KPI tree, revenue forecasting, and governance cadence")
        _p(
            pdf,
            "The KPI architecture spans leading indicators (call reach, NPP engagement depth, PA turnaround, hub speed) "
            "and lagging outcomes (NRx/TRx, persistent share, revenue recognition quality). Franchise leadership reviews a "
            "balanced scorecard every fortnight, with SOX-relevant revenue controls isolated in the R-ARC workstream. "
            "Illustrative Year-1 targets: new patient starts 26.4K, commercial gross revenue $388M (IFRS), net revenue "
            "$140M after GTN, with specialty pharmacy service-level agreement (SLA) compliance >=97.5%. Variance thresholds "
            "beyond +/-8% on any two consecutive weeks elevate to CFO staff and trigger demand recalibration.",
        )
        _p(
            pdf,
            "Forecast governance integrates field intelligence ('CFI') with Bayesian shrinkage toward IQVIA audit trails; "
            "sandbagging is discouraged via transparency on confidence intervals presented to the board commercial committee. "
            "Long-range planning includes patent expiry of analogs in 2029-2031 that could expand biologic-to-oral switches "
            "by an incremental 130K patients nationally if clinical guidelines widen first-line advanced therapy eligibility.",
        )
        _p(
            pdf,
            "Incentive compensation for commercial leadership ties 35% of annual bonus to launch milestone achievements, 25% "
            "to access wins, 20% to compliance-validated promotion quality, and 20% to collaboration metrics (cross-functional "
            "NPS). Ethics review ensures no off-label incentives appear in sales contests; all SPIFF structures are double "
            "signed by Compliance and Legal.",
        )
        _p(
            pdf,
            "Document owners must refresh this playbook within 90 days of any FDA label change shifting contraindication "
            "language, Black Box emphasis, or REMS modification; outdated PDFs are retired through PromoMats supersession "
            "workflow with audit logs retained seven years.",
        )
        _bullets(
            pdf,
            [
                "Leading indicator dashboard refreshes daily at 06:00 ET with 45-minute latency SLA on claims feeds.",
                "Forecast accuracy KPI: rolling 13-week MAPE <=18% through first year post-launch.",
                "Compliance: zero unresolved FDA untitled letters simulation breaches in mock inspections.",
            ],
        )

    return _two_pass(
        fn,
        "Nexara TM Launch Playbook",
        "Commercial Product Launch Playbook",
        "Nexara -- fictional JAK1-preferential oral asset -- U.S. RA franchise (synthetic workshop scenario)",
        [
            "Document ID: COMM-LP-NXR-2026-01",
            "Version 2.1 -- synthetic training artifact for KA ingestion",
            "Owning function: VP, U.S. Immunology Commercial Operations",
        ],
        [
            ("1. Executive overview and strategic imperatives", s01_exec),
            ("2. Market landscape, sizing, and segmentation", s02_market),
            ("3. Positioning, messaging, and MLR claims architecture", s03_position),
            ("4. HCP targeting, affinity, and omnichannel orchestration", s04_hcp),
            ("5. Pre-launch readiness gates and stakeholder alignment", s05_prelaunch),
            ("6. Launch execution, SQM, and surge management", s06_launch_exec),
            ("7. Market access, contracting, and pull-through", s07_access),
            ("8. KPIs, forecasting governance, and commercial controls", s08_kpis),
        ],
    )


def build_competitive_intel() -> str:
    fn = "Competitive_Intelligence_Report_Q1_2026.pdf"

    def c01_share(pdf: CommercialPDF) -> None:
        _h2(pdf, "Class-level share, growth, and channel mix")
        _p(
            pdf,
            "The U.S. immunology advanced oral class (AO-IM) closed Q4 2025 at $6.92B moving annual total (MAT) revenue, "
            "up 3.8% YoY despite payer tightening on JAK class utilization following cardiovascular and malignancy "
            "vigilance narratives in competitor labels. Nexara's pre-launch analog share-of-market is modeled at 0.0% "
            "obviously, while entrenched competitors -- here anonymized as Brand J1 (oral JAK), Brand T (TYK2), and Brand "
            "J2 (second-generation oral JAK) -- collectively account for 81% of AO-IM TRx days among dermatology and "
            "rheumatology combined indications, with RA contributing 58% of days. Biologic backbone anti-TNF and IL-6 "
            "classes ceded 1.1 TRx index points to orals MAT, concentrated in urban infusion-adjacent markets where travel "
            "friction remained elevated post-pandemic normalization.",
        )
        _p(
            pdf,
            "Wholesaler sell-in versus sell-out divergence narrowed to 0.9% in December 2025, implying inventory stability "
            "entering 2026; however, chargeback volatility on one major competitor reached 2.7% of gross sales in "
            "November due to PBM formulary churn. Mail vs retail split for AO-IM sits at 61%/39%, with specialty pharmacy "
            "limited networks intensifying in three PBMs that now restrict first fills to in-network hubs unless medical "
            "exception documentation is filed within 96 hours.",
        )
        _p(
            pdf,
            "Share decomposition by prescriber decile reveals top decile rheumatologists prescribe 3.7x the AO-IM volume "
            "of median deciles, with 44% concentration in MA-heavy populations where prior authorization burden depresses "
            "switch velocity for new entrants by an estimated 19% unless contracting secures edits mitigation.",
        )
        _p(
            pdf,
            "International spillover demand signals from Canadian cross-reference prescribing (via telehealth leakage) remain "
            "<0.3% of US reported claims; border state monitoring continues at monthly cadence with legal liaison.",
        )
        _bullets(
            pdf,
            [
                "MAT growth of competitor Brand J1 slowed to +1.6% following DTC flight reductions; creative wear may open "
                "NPP whitespace for challenger imagery.",
                "IRA Medicare price negotiation watch-list: no AO-IM molecules selected in 2026 cycle but re-run risk in "
                "2028 flagged at medium.",
            ],
        )

    def c02_pipeline(pdf: CommercialPDF) -> None:
        _h2(pdf, "Pipeline watchlist and anticipated launch windows")
        _p(
            pdf,
            "EvaluatePharma-style triangulation (synthetic) IDs five late-stage assets that could compress oral switch "
            "windows: (a) bispecific anti-inflammatory macrocycle XO-441 entering Phase III RA with 2027 PDUFA hypothetical; "
            "(b) gut-selective oral molecule GS-882 in Phase IIb with endoscopic healing signals cross-read to skin; (c) "
            "long-acting subcutaneous anti-IL23 quarterly dosing candidate SC-D23; (d) reversible covalent JAK1 inhibitor "
            "RC-J01 with liver enzyme narratives under FDA scrutiny; (e) biosimilar infliximab high-concentration presentations "
            "pressuring anti-TNF pricing and indirectly stimulating oral step protocols.",
        )
        _p(
            pdf,
            "Probability-adjusted revenue at risk from XO-441 introduction is $210M-$340M to incumbents by 2030 under base "
            "quintile assumptions; scenario stress with faster enrollment could pull peak share erosion forward by 14 "
            "months. Patent thickets around crystalline polymorphs for Brand J2 extend exclusivity in US to mid-2032 for "
            "method-of-use claims, though inter partes review petitions filed Q3 2025 introduce binary legal risk adjudicated "
            "in late 2026.",
        )
        _p(
            pdf,
            "Biosimilar adalimumab noise continues: eight interchangeable or substitutable presentations compete on net in "
            "the low 60% WAC discount corridor after rebates, crowding portfolio resources for account managers and diluting "
            "P&T attention bandwidth.",
        )
        _bullets(
            pdf,
            [
                "Watch FDA advisory panels on XO-441 in 1H 2027; scenario plans include accelerated counter-detail on renal "
                "excretion safety database differentiators.",
                "Competitive intelligence harvests 140 conference abstracts quarterly; NLP topic model surfaces 'hepatic' "
                "cluster growth +22% YoY in AO-IM discourse.",
            ],
        )

    def c03_swot(pdf: CommercialPDF) -> None:
        _h2(pdf, "SWOT matrices for prioritized competitors")
        _p(
            pdf,
            "Brand J1 strengths include entrenched guideline citations, mature hub partnerships, and 74% HCP aided recall "
            "in deciles 8-10; weaknesses encompass class-label cardiovascular warnings suppressing naive starts in "
            "cardiometabolic comorbidity strata representing 21% of target. Brand T opportunities exploit once-daily "
            "dosing and differentiated monitoring; threats include prior PBM non-medical switching and cumulative infections "
            "signal sensitivity in social listening spikes after competitor-sponsored symposiums.",
        )
        _p(
            pdf,
            "Brand J2 strengths derive from dermatology cross-pull into RA via same prescribers in combo practices (18% "
            "overlap in EMR panels surveyed); weaknesses include higher discontinuation for GI intolerance at Month 6 (12.4% "
            "versus class median 9.1% in claims proxies). Opportunistic messaging must remain non-misleading and vetted: "
            "never cite competitor discontinuation without peer-reviewed lineage.",
        )
        _p(
            pdf,
            "Aggregate SWOT scoring weights commercial impact (40%), scientific defensibility (25%), legal promo risk "
            "(20%), and access durability (15%). Quarterly refresh ensures MSL battlecards track evolving vulnerabilities, "
            "especially post-conference data drops.",
        )
        _bullets(
            pdf,
            [
                "Do not deploy competitive slides externally without Legal tier-3 review and state-specific price "
                "transparency footnotes.",
                "Counter-detailing simulations show highest yield when focusing on lab monitoring cadence clarity versus "
                "efficacy deltas absent head-to-head.",
            ],
        )

    def c04_patent(pdf: CommercialPDF) -> None:
        _h2(pdf, "Patent cliffs, exclusivity, and litigation calendar")
        _p(
            pdf,
            "US Orange Book-style listings (illustrative) for Brand J1 primary composition-of-matter patent expires "
            "September 2030 with pediatric exclusivity extension uncertain (+6 months contingent on completed studies). "
            "Brand T method claims extend to 2033 but Hatch-Waxman litigation versus two generics firms may compress "
            "effective protection if 'obviousness-type double patenting' arguments succeed in Federal Circuit appeals heard "
            "in calendar 2026.",
        )
        _p(
            pdf,
            "Nexara's synthetic patent portfolio shows US grants on composition (2037), dosing regimen (2038), and polymorph "
            "(2036) with 156-term adjustment petition filed estimating +496 days if PTAB challenges fail. Freedom-to-operate "
            "clearance memorandum v4.2 identifies intermediate synthesis reagent overlap risk with legacy supplier patents "
            "expires 2027--supply chain contingency qualified alternate vendor at +3.2% COGS.",
        )
        _p(
            pdf,
            "European supplementary protection certificate (SPC) stacking rules may grant fewer extension months than US PTA; "
            "EU5 launch sequencing delays exposure to reference pricing political optics if German AMNOG benefit assessment "
            "comes in unfavorable.",
        )
        _bullets(
            pdf,
            [
                "Litigation docket reviews monthly with IP counsel; claim construction hearing for polymorph spat targeted "
                "Q3 2026.",
                "Biosimilar infliximab patent expiries largely complete; residual peripheral patents negligible for RA volume.",
            ],
        )

    def c05_biosimilar(pdf: CommercialPDF) -> None:
        _h2(pdf, "Biosimilar erosion and cross-class substitution")
        _p(
            pdf,
            "Anti-TNF originator erosion surpassed 68% TRx decline from peak for etanercept and infliximab innovators in "
            "aggregated syndicated data; net pricing collapsed faster than volume, producing budget headroom some PBMs "
            "reallocate to newer oral targets via tougher step policies. This indirect pressure raises hurdle rates for "
            "AO-IM starts unless value dossiers quantify total cost of care versus delayed advanced therapy escalation.",
        )
        _p(
            pdf,
            "Interchangeable biosimilar adalimumab uptake in select states crossed 41% of adalimumab days by January 2026, "
            "triggering cascade edits that inadvertently elevate 'fail biologic first' provisions which paradoxically favor "
            "sustained oral placements after failure -- positive read-through for AO-IM share if messaging clarifies sequencing "
            "per guidelines.",
        )
        _p(
            pdf,
            "Biosimilar margin compression on reference sponsors frees payer appetite for outcomes-based deals; three national "
            "accounts piloted total-cost contracts for RA cohorts with 18-month look-backs, creating data infrastructure "
            "competitors may lack.",
        )
        _bullets(
            pdf,
            [
                "Monitor state substitution laws quarterly; 12 states updated pharmacist substitution rules in 2025.",
                "Forecast biosimilar-driven P&T agenda crowding: meeting slots down 8% YoY for oral specialty NDAs.",
            ],
        )

    def c06_pricing(pdf: CommercialPDF) -> None:
        _h2(pdf, "Net price pressure, rebate stacking, and Gross-to-Net risk")
        _p(
            pdf,
            "Class net pricing fell 6.1% YoY in 2025 per gross-to-net waterfall reconstruction despite nominal WAC inflation of "
            "4.4%, driven by incremental PBM administrative fees (+40 bps), indication-based contracting true-ups, and higher "
            "copay accelerator redemption (avg 1.7 fills per patient enrolled). Competitor Brand J2 leaked 380 bps net vs "
            "WAC due to defensive contracting when a mid-size PBM threatened non-coverage across 4.2M lives.",
        )
        _p(
            pdf,
            "Inflation Reduction Act rebate liabilities and Medicaid best price multipliers force scenario hedging: any future "
            "line extension with inferior net could trigger BP cliff events if nominal price cuts spread across channels. "
            "Finance insists on waterfall simulation for any coupon redesign exceeding +15% projected redemption.",
        )
        _p(
            pdf,
            "International referencing chatter elevated after 2025 legislative midterms; sovereign pricing teams maintain "
            "defensive narrative emphasizing US R&D allocation (illustrative 19% of global pharma R&D attributed to "
            "innovation originating in US sites).",
        )
        _bullets(
            pdf,
            [
                "GTN governance: monthly bridge analyses reconcile SAP revenue to wholesaler data within 35 bps tolerance.",
                "Price transparency posting rules: ensure HCP-facing decks scrub inconsistent list price comparisons.",
            ],
        )

    def c07_reco(pdf: CommercialPDF) -> None:
        _h2(pdf, "Strategic recommendations through 2027")
        _p(
            pdf,
            "Recommendation 1: Accelerate payer pilots on flare-related medical cost offsets using tokenized claims analytics "
            "to differentiate versus competitors lacking outcomes infrastructure. Target signature by Q3 2026 with at "
            "least one national plan exceeding 8M covered lives. Recommendation 2: Invest in hepatology-aligned "
            "education--not fear--to preempt class labeling anxiety; sponsor prospective chart audits (COMPLIANCE: no "
            "inducement) demonstrating ALT monitoring adherence in real-world settings where IRB oversight applies.",
        )
        _p(
            pdf,
            "Recommendation 3: Erect competitive intelligence firewalls between CI primary research vendors and promotional "
            "agencies to reduce insider risk; dual-control document repositories with Legal hold tags. Recommendation 4: "
            "Pressure-test oral crowding narrative with prescribers via conjoint research every two quarters; elasticities "
            "shifted materially after telehealth regulations tightened in January 2026.",
        )
        _p(
            pdf,
            "Recommendation 5: Maintain litigation watch funds at 1.2% of franchise EBIT for IP defense and promotional "
            "substantiation challenges. Recommendation 6: Expand MSL scientific narratives around radiographic progression "
            "data if competitor labels lack comparable endpoints, always within scientific exchange guardrails.",
        )
        _p(
            pdf,
            "Lead intelligence officer attestation: sources include syndicated Rx, payer informant panels (Sunshine compliant), "
            "conference surveillance, and public filings; proprietary patient-level data are not utilized in this external "
            "reporting deck.",
        )
        _bullets(
            pdf,
            [
                "Next refresh: Q2 2026 with deep-dive on PBM consolidation rumor track impacting three accounts.",
                "Distribution embargo: this document not for external dissemination without Legal redaction pass.",
            ],
        )

    return _two_pass(
        fn,
        "AO-IM Competitive Intelligence",
        "Competitive Intelligence Report",
        "U.S. advanced oral immunology class -- Q1 2026 situational analysis (synthetic)",
        [
            "CI-GLOBAL-IMM-2026-Q1",
            "Classification: Internal use -- Training corpus",
            "Prepared by: Global Competitive Insights, Immunology Franchise",
        ],
        [
            ("1. Market share, growth, and channel dynamics", c01_share),
            ("2. Competitor pipeline and launch risk scenarios", c02_pipeline),
            ("3. SWOT analyses and counter-positioning guardrails", c03_swot),
            ("4. Patent, exclusivity, and litigation roadmap", c04_patent),
            ("5. Biosimilar cross-elasticity and policy effects", c05_biosimilar),
            ("6. Pricing, GTN, and payer economics", c06_pricing),
            ("7. Strategic recommendations and intelligence governance", c07_reco),
        ],
    )


def build_field_force_guide() -> str:
    fn = "Field_Force_Excellence_Training_Guide.pdf"

    def f01_disease(pdf: CommercialPDF) -> None:
        _h2(pdf, "Disease-state education: RA pathophysiology and treatment goals")
        _p(
            pdf,
            "Rheumatoid arthritis is a chronic autoimmune synovitis characterized by immune complex formation, citrullinated "
            "peptide autoimmunity in many patients, and a destructive cytokine milieu dominated by TNF, IL-6, and IL-17 "
            "family signaling in varying proportions across phenotypes. Commercial teams must articulate treat-to-target "
            "(T2T) principles endorsed by ACR/EULAR: the objective is low disease activity or remission on validated "
            "composite scores (CDAI, DAS28-CRP, Boolean remission) while minimizing glucocorticoid exposure. In 2026 "
            "payer environments, glucocorticoid-sparing narratives carry quantifiable economic value: each 5 mg/day "
            "prednisone-equivalent reduction associates with ~=6-9% lower infection-related medical spend in closed "
            "claims benchmarks (illustrative cohort; not causal inference).",
        )
        _p(
            pdf,
            "Joint damage progression despite 'clinically quiet' inflammation occurs in roughly 12-18% of radiographic "
            "progressors in long-term registries when inflammation is suboptimally controlled; this underpins guideline "
            "emphasis on early advanced therapy escalation. Representatives should never imply individualized prognosis "
            "but may reference class-level radiographic outcomes consistent with prescribing information when MLR-approved.",
        )
        _p(
            pdf,
            "Comorbidity stratification is commercially relevant: patients with moderate hepatic steatosis, prior serious "
            "infections, or significant cardiovascular risk require balanced counseling that remains within the label. "
            "Field roles must defer specific treatment decisions to prescribers while offering access to approved "
            "medical information for unsolicited requests.",
        )
        _p(
            pdf,
            "Training certification requires 90% score on a 40-item disease knowledge exam covering serology interpretation "
            "basics, vaccination counseling expectations, and pregnancy/lactation general principles at high level aligned "
            "to company policy.",
        )
        _bullets(
            pdf,
            [
                "T2T: emphasize treat-to-target as prescriber-driven framework; representatives provide educational context only.",
                "Radiographic endpoints: use only MLR-cleared language tied to company-sponsored trial readouts.",
                "Do not discuss off-label investigational combinations or compare malignancy rates without fair balance deck.",
            ],
        )

    def f02_product(pdf: CommercialPDF) -> None:
        _h2(pdf, "Product knowledge: Nexara MOA, dosing, safety, monitoring")
        _p(
            pdf,
            "Nexara (fictional asset) is presented for training as a selective JAK1 inhibitor with once-daily oral dosing "
            "in the approved RA population described in the label (workshop simulation). Reps must memorize black box / "
            "warning themes if the label carries class-consistent serious infection, malignancy, MACE, and thrombosis "
            "language comparable to approved JAK inhibitors for inflammatory diseases. Laboratory monitoring: baseline hepatic "
            "panel, CBC with differential, and lipid profile per label with time-based repeats; field representatives cite "
            "only the monitoring schedule exactly as MLR approved for promotional contexts.",
        )
        _p(
            pdf,
            "Efficacy talking points restrict to ACR responses, change in DAS28-CRP, and functional outcomes exactly as "
            "printed in the PI excerpt module. Secondary endpoints (e.g., patient-reported pain, morning stiffness duration) "
            "may appear only if substantiated in the structured claims grid. Competitor comparisons require Legal tier "
            "clearance and often are limited to MSL channels.",
        )
        _p(
            pdf,
            "Pharmacokinetics training covers absorption with/without food per label, CYP3A4 interaction alertness (no "
            "inducement to ignore prescriber DDI judgment), and renal/hepatic adjustment thresholds if present. Sample "
            "handling: cold chain not required for oral tablets, but storage temperature ranges must match PI; sampling "
            "eligibility respects PDMA and Anti-Kickback policies.",
        )
        _p(
            pdf,
            "Packaging literacy: NDC recognition, day-supply defaults, and rejection code interpretation for common SCORE "
            "rejection families assists pull-through with office staff--always frame as operational support, not clinical "
            "decision-making.",
        )
        _bullets(
            pdf,
            [
                "Adverse events: representatives report suspected adverse events within 24 hours via the PV hotline workflow.",
                "Dosing: never encourage dose escalation beyond PI; redirect DDI questions to Medical Information.",
            ],
        )

    def f03_objection(pdf: CommercialPDF) -> None:
        _h2(pdf, "Objection handling: evidence-based response maps")
        _p(
            pdf,
            "Objection theme 'oral JAK class is unsafe' requires calm, label-grounded framing: acknowledge historical FDA "
            "communications, present post-marketing surveillance context at high level per MLR FAQ, pivot to importance of "
            "appropriate patient selection, baseline labs, and vigilance for infections/MACE risk factors. Never dismiss "
            "physician caution; offer peer-reviewed reprints only from approved library.",
        )
        _p(
            pdf,
            "Objection 'my patients fail orals quickly' invites discussion of persistence heterogeneity and hub-enabled "
            "adherence programs without promising outcomes. Cite illustrative persistence percentages only if substantiated "
            "and fairly balanced. Transition to access tools (benefit investigation, copay stack) when administrative burden "
            "dominates conversation.",
        )
        _p(
            pdf,
            "Objection 'payer blocks everything' triggers coordinated FRM engagement; reps learn to triage plan types, locate "
            "formulary tier, interpret PA forms, and schedule co-travel with access colleagues when win-rate models exceed "
            "thresholds in the account plan.",
        )
        _p(
            pdf,
            "Role-play scoring uses standardized rubrics: active listening (20%), compliance-safe language (35%), clinical "
            "accuracy (25%), call-to-action clarity (20%). Two consecutive sub-75% scores mandate manager ride-alongs.",
        )
        _bullets(
            pdf,
            [
                "Never argue with clinicians about 'best therapy'; align on patient-centered decision criteria.",
                "Document objections in CRM for signal aggregation; aggregate monthly for competitive insights.",
            ],
        )

    def f04_payer(pdf: CommercialPDF) -> None:
        _h2(pdf, "Payer landscape, access navigation, and office-staff enablement")
        _p(
            pdf,
            "U.S. access archetypes include open formulary commercial lives (25% illustrative in some territories), "
            "step-through biologic experienced pathways (38%), unrestricted specialty tier islands (12%), and Medicaid "
            "carve scenarios with state variability (remainder). Reps carry wallet cards summarizing PA evidence packet "
            "checklists and typical turnaround times learned from hub analytics--numbers must be refreshed quarterly to "
            "avoid misrepresentation.",
        )
        _p(
            pdf,
            "Medicare Advantage nuances: some plans segregate Part B infused biologics from Part D orals, affecting "
            "sequencing incentives. LIS patients show different cost-share sensitivity; legal copay support policies define "
            "eligibility and cannot be promoted as inducements.",
        )
        _p(
            pdf,
            "340B exposure in large IDNs requires professional demeanor around contract pharmacy dynamics; representatives "
            "must not coach circumvention and should escalate ethical gray areas to Compliance.",
        )
        _p(
            pdf,
            "EHR prior authorization attachments training covers SMART on FHIR bundle basics at workflow level--no "
            "engineering promises--to reduce staff frustration and abandoned submissions.",
        )
        _bullets(
            pdf,
            [
                "FRM co-call ratio target: 1 joint access touch per Priority A account per quarter minimum.",
                "Benefit investigations: document PHI minimization--only data elements permitted by hub policy.",
            ],
        )

    def f05_selling(pdf: CommercialPDF) -> None:
        _h2(pdf, "Selling skills: call structure, scientific dialogue, virtual etiquette")
        _p(
            pdf,
            "The approved call model follows OPEN-PROBE-BRIDGE-CLOSE: open with a clinical insight tied to a verified patient "
            "archetype; probe for current therapy durability, steroid burden, and lab workflow friction; bridge to "
            "label-consistent efficacy/safety plus access enablers; close with a specific next step (e.g., sample delivery, "
            "speaker program RSVP, MLR-approved handout). Virtual calls require camera readiness, 40-second hook discipline, "
            "and bandwidth redundancy guidance.",
        )
        _p(
            pdf,
            "Question funnels differentiate exploratory ('How do you approach flares on current oral therapy?') from "
            "confirmatory ('Would earlier ALT monitoring cadence reduce reluctance in your practice?'). Leading questions "
            "that suggest off-label use are prohibited.",
        )
        _p(
            pdf,
            "Time-in-territory planning leverages heat maps of undetailable HCPs vs whitespace geographies; overnight travel "
            "policy compliance tracked with T&E analytics to prevent Sunshine irregularities.",
        )
        _bullets(
            pdf,
            [
                "Scientific curiosity: reward reps who surface unsolicited requests cleanly to MSLs with recognition programs "
                "approved by Compliance.",
                "Sampling: chain-of-custody logs audited; discrepancies >0.5% trigger district stand-down review.",
            ],
        )

    def f06_compliance(pdf: CommercialPDF) -> None:
        _h2(pdf, "Compliance: OIG guidance, Anti-Kickback, PDMA, Open Payments")
        _p(
            pdf,
            "Field personnel must complete annual certifications on federal healthcare program fraud and abuse basics, "
            "understanding that remuneration includes anything of value--meals, speaker fees, copay coupons routed "
            "improperly--that could induce referrals. Consultant engagements require FMV documentation, scope clarity, "
            "and need assessment signatures.",
        )
        _p(
            pdf,
            "Promotional materials only from PromoMats approved versions; local edits forbidden. Social media policy bans "
            "off-label anecdotes even in 'personal' accounts when identifiable as company employees per policy clauses.",
        )
        _p(
            pdf,
            "Open Payments: track transfers of value meticulously; meals capped by policy with attendee roster verification. "
            "State transparency addenda (e.g., Nevada, Vermont historical requirements) layered into CRM attestations.",
        )
        _p(
            pdf,
            "Clinical trial seeding concerns: representatives may not discuss investigational sites in ways that link "
            "script volume to investigator selection; clinical operations owns site relationships.",
        )
        _bullets(
            pdf,
            [
                "Aggregate spend reviews quarterly with Legal on high-risk spend categories (speakers, consultants).",
                "Anti-corruption: FCPA training required for international traveler reps supporting US hybrid accounts.",
            ],
        )

    def f07_territory(pdf: CommercialPDF) -> None:
        _h2(pdf, "Territory management, targeting math, and resource allocation")
        _p(
            pdf,
            "Territory alignment uses convex optimization balancing workload hours, travel radius, and revenue potential; "
            "each rep maintains no more than 85 active targets in CRM at steady state to preserve call quality. Quarterly "
            "re-tiering adjusts for prescriber retirements, practice mergers, and PDMP-driven prescribing shifts.",
        )
        _p(
            pdf,
            "Sample inventory reconciliation weekly; shrinkage alarms at >0.3% monthly. Voice-of-business requests for "
            "geography splits escalate through RSD with finance sign-off if EBIT impact exceeds $450K annualized.",
        )
        _p(
            pdf,
            "Digital-forward territories receive incremental NPP budgets tied to validated email match rates exceeding 82% "
            "for target HCPs while preserving opt-out compliance.",
        )
        _bullets(
            pdf,
            [
                "Call reporting integrity audits: random 2% sample monthly; falsification is zero-tolerance termination.",
                "Whitespace activation requires Legal review if involving non-traditional venues (urgent care, tele-only hubs).",
            ],
        )

    def f08_cases(pdf: CommercialPDF) -> None:
        _h2(pdf, "Synthetic case studies: application drills")
        _p(
            pdf,
            "Case A: 54-year-old biologic-experienced patient with MTX inadequate response and mild hepatic steatosis. "
            "Practice expresses JAK hesitancy due to MACE history in family (not patient). Training solution: pivot to "
            "prescriber-directed risk assessment, emphasize monitoring per label, deploy MLR-approved patient lab-schedule "
            "visual, schedule MSL follow-up for mechanism deep dive if unsolicited request arises.",
        )
        _p(
            pdf,
            "Case B: Medicaid-heavy clinic with 62% PA denials on competitor oral class. Training solution: co-travel with "
            "FRM, assemble appeals letter template library verified by Legal, escalate to state Medicaid medical director "
            "letter campaign coordinated by Government Affairs--field executes only approved tactics.",
        )
        _p(
            pdf,
            "Case C: Academic center with EMR burden limiting detail windows; virtual micro-details (8 minutes) with "
            "clinician-approved agenda. Training solution: precision visual aids, asynchronous PDF summaries via approved "
            "email journeys, measure open-to-Rx lift in 30-day lagged cohort benchmarks.",
        )
        _p(
            pdf,
            "Capstone: reps assemble a compliant call plan for a quarter including sample budget burn curve, speaker "
            "program mix, and access touchpoints--graded by district leaders against rubric FX-2026 v3.",
        )
        _bullets(
            pdf,
            [
                "All case studies are synthetic; any resemblance to real patients or prescribers is coincidental.",
                "Update cases when label or access deck versions increment major.minor.",
            ],
        )

    return _two_pass(
        fn,
        "Field Force Excellence",
        "Field Force Excellence Training Guide",
        "U.S. Immunology -- representative and access liaison enablement (synthetic workshop)",
        [
            "TRN-FF-IMM-2026-04",
            "Classification: Internal training -- Not for external distribution",
            "Curriculum owner: Director, Commercial Learning & Development",
        ],
        [
            ("1. Disease-state education and treat-to-target context", f01_disease),
            ("2. Product knowledge: MOA, dosing, safety, sampling", f02_product),
            ("3. Objection handling and compliant dialogue", f03_objection),
            ("4. Payer landscape and access navigation", f04_payer),
            ("5. Selling skills: virtual and in-person excellence", f05_selling),
            ("6. Compliance, transparency, and ethics", f06_compliance),
            ("7. Territory management and targeting discipline", f07_territory),
            ("8. Case studies and capstone evaluation", f08_cases),
        ],
    )


def build_market_research_report() -> str:
    fn = "Market_Research_Insights_Report.pdf"

    def m01_method(pdf: CommercialPDF) -> None:
        _h2(pdf, "Physician survey: methodology and representativeness")
        _p(
            pdf,
            "Online mixed-mode survey fielded November-December 2025 among U.S. adult rheumatologists and mixed specialists "
            "with high RA panel volume; final sample n=500 after quality filters (straight-lining removal, speeders, "
            "credential verification against NPI roster). Quotas enforced on geography (Northeast 22%, South 28%, "
            "Midwest 20%, West 30%), practice setting (community 58%, academic 27%, multispecialty 15%), and years in "
            "practice bands. Weighting applied raked across decile Rx volume to match IQVIA benchmarks; maximum weight "
            "trim at 2.8 to limit undue influence of micro-practices.",
        )
        _p(
            pdf,
            "Margin of error for global percentages approximately +/-4.2 points at 95% confidence before design effect; "
            "intraclass correlation from practice clustering adjusted via robust standard errors in regression modules. "
            "Incentive: $425 honorarium compliant with Sunshine aggregation; disclosures collected for CME conflicts.",
        )
        _p(
            pdf,
            "Limitations: social desirability bias on safety questions; underrepresentation of rural solo practices at "
            "7% versus national 11%; asynchronous field timing crossing competitor congress buzz may elevate unaided recall "
            "for newly advertised molecules by an estimated +3-5 points.",
        )
        _bullets(
            pdf,
            [
                "Data asset retained in encrypted analytics lake; only aggregate slides exported to PromoMats.",
                "IRB exemption letter on file for minimal risk market research; PHI not collected.",
            ],
        )

    def m02_physician(pdf: CommercialPDF) -> None:
        _h2(pdf, "Key physician insights: switching, safety perceptions, information channels")
        _p(
            pdf,
            "Seventy-one percent of respondents reported prescribing at least one oral advanced therapy for RA in the past "
            "90 days; among them, 43% described themselves as 'very willing' to try a newly launched oral with differentiated "
            "monitoring if payer access is tier 2 or better. Concerns ranked: serious infection risk (61% top-two box), "
            "hepatic monitoring burden (54%), cardiovascular risk narratives (49%), prior authorization fatigue (68%).",
        )
        _p(
            pdf,
            "Information sourcing: 58% cite congress posters as influential within last 6 months; 51% Doximity clinical "
            "cases; 46% peer dialogues; journal scans 74% but often delayed 30-60 days versus launch cadence. Reps remain "
            "relevant: 63% say specialty rep visits at least monthly change awareness though only 31% admit direct impact "
            "on prescribing without other triggers--highlighting omnichannel necessity.",
        )
        _p(
            pdf,
            "Brand perception mapping (MaxDiff on attributes) shows efficacy still dominates part-worth share at 38%, "
            "followed by predictable safety at 22%, hub speed at 14%, copay at 12%, and 'innovation halo' at 14% across "
            "oral brands tested as holdouts.",
        )
        _p(
            pdf,
            "Willingness to co-manage with APPs continues to climb: 67% of physicians delegate first-line follow-up labs "
            "scheduling to nursing staff--detail delivery should include nursing leave-behinds only if MLR-approved.",
        )
        _bullets(
            pdf,
            [
                "Segment cuts: academic physicians overweight 'innovation halo' by +9 pts vs community.",
                "Southern region shows +7 pts higher PA burden perception versus national mean.",
            ],
        )

    def m03_journey(pdf: CommercialPDF) -> None:
        _h2(pdf, "Patient journey mapping: friction points and abandonment risk")
        _p(
            pdf,
            "Qualitative deep dives (32 patient/caregiver dyads recruited via advocacy partners, synthetic composite "
            "analysis) surfaced five journey stages: symptom emergence, diagnosis delay, access battle, therapy adjustment, "
            "and long-term self-management. Median diagnosis-to-specialist interval in composites reflects 4.2 months when "
            "primary care empiric NSAID trials extend; access battle stage average 18-26 calendar days for prior auth "
            "in commercial cohorts versus 41 days in Medicaid composites.",
        )
        _p(
            pdf,
            "Abandonment risk peaks at pharmacy switch when copay surprise exceeds $95 OOP first fill; hub interventions "
            "within 48 hours recover an estimated 31% of stalled starts in modeled scenarios calibrated to hub CRM data "
            "(internal). Emotional toll: 44% of composites cite fatigue explaining oral preference vs infusion even when "
            "intrinsic value props differ.",
        )
        _p(
            pdf,
            "Digital touchpoints: 57% of patients search condition keywords on mobile within two weeks of intensified "
            "symptoms; DTC presence skews questions in office visits--physicians report needing succinct counter-detail "
            "two-pagers.",
        )
        _bullets(
            pdf,
            [
                "Patient materials must be non-promotional if distributed in some states without DTC licensure alignment.",
                "Journey maps integrate with CRM trigger campaigns only where HIPAA business associate frameworks satisfied.",
            ],
        )

    def m04_claims(pdf: CommercialPDF) -> None:
        _h2(pdf, "Claims-derived insights: persistence, switching, and comorbidity burden")
        _p(
            pdf,
            "Closed-claims extracts (>=18 months continuous enrollment) covering ~4.1 M commercially insured lives with RA "
            "ICD codes illustrate 180-day persistence on index oral advanced therapy at 63% in 2024-2025, down 3 pts YoY as "
            "step edits intensified. Switching half-life approximates 11 months for first switch after index in "
            "biologic-experienced subgroup. Comorbidity hotspots: hyperlipidemia 48%, hypertension 52%, obesity 36% by "
            "claim-defined BMI proxy.",
        )
        _p(
            pdf,
            "Medical resource utilization among persistent vs non-persistent cohorts shows $2,840 higher per-member "
            "per-year allowed ED/ outpatient spend in non-persistent groups driven by flares--used in pharmacoeconomic "
            "storyboarding with compliance to comparative effectiveness legal standards.",
        )
        _p(
            pdf,
            "Methodological safeguards: exclude capitated carve-outs with incomplete Rx; apply multiplicity correction when "
            "mining 24 subgroups; document replication on holdout 30% sample before executive readout.",
        )
        _bullets(
            pdf,
            [
                "PHI minimization: analytics on tokenized ids; analyst workspaces segregated by role.",
                "Outputs translated to HCP-facing only after MLR review of specific claims-anchored statements.",
            ],
        )

    def m05_payer_res(pdf: CommercialPDF) -> None:
        _h2(pdf, "Payer research: P&T simulations and rebate sensitivity")
        _p(
            pdf,
            "Discrete-choice experiments with 120 pharmacy directors and medical directors revealed formulary placement "
            "elasticity: a 10 percentage point rebate increase moves preferred placement probability +14 points when "
            "clinical differentiation messaging is 'moderate' versus 'high' (p<0.05). Step therapy removal alone without "
            "rebate lift yields +9 points, indicating administrative burden rivals price for some accounts.",
        )
        _p(
            pdf,
            "Medicaid focused groups cite spread pricing opacity as distrust driver; transparent invoicing pilots improved "
            "relationship scores +0.8 on 5-point Likert in two states (illustrative pilot).",
        )
        _p(
            pdf,
            "Employer coalition interviews (n=18 benefits leads) show growing interest in referenced-based pricing tied to "
            "ambulatory infusion anchors--may shift RA mix indirectly toward orals if infusion admin fees disfavored.",
        )
        _bullets(
            pdf,
            [
                "Payer research materials embargoed 14 days post readout to allow Legal review of quotable stats.",
                "No recording of conversations without double consent per internal investigations policy.",
            ],
        )

    def m06_digital(pdf: CommercialPDF) -> None:
        _h2(pdf, "Digital HCP behavior: attention economics and creative diagnostics")
        _p(
            pdf,
            "Web analytics across endemic platforms (aggregated contractual feeds) show median attentive seconds on mobile "
            "clinical content at 12.7s; completion rates for 3-minute video dropped 22% after second brand mention "
            "unless creative front-loads novel visual data in first 8 seconds. Search query funnels reveal growth in "
            "'ALT monitoring oral RA' +38% QoQ seasonally adjusted Q1 2026.",
        )
        _p(
            pdf,
            "Email engagement decays: third-message incremental open rate only 4.1% without creative refresh; sequencing "
            "algorithms that adapt to subspecialty interest tags restore open rates toward 11%.",
        )
        _p(
            pdf,
            "Tele-detail attendance correlates with EHR message inbox burden proxies (Delta=0.31); best practices include "
            "calendar holds and nursing champion pre-briefs.",
        )
        _p(
            pdf,
            "Ethical data use: cookie policies updated Jan 2026 for state privacy laws; suppression lists cross-sync within "
            "15 minutes SLA.",
        )
        _bullets(
            pdf,
            [
                "Brand lift studies: Geo-experiments with synthetic controls planned for Wave 2 DMAs.",
                "Influencer clinicians: contracts require transparent sponsorship tagging on social posts.",
            ],
        )

    def m07_synthesis(pdf: CommercialPDF) -> None:
        _h2(pdf, "Strategic implications for brand planning and measurement")
        _p(
            pdf,
            "Synthesis recommends weighting omnichannel spend toward early-video scientific novelty, parallel payer "
            "simultaneous co-creation of PA simplification templates, and patient hub messaging emphasizing copay "
            "predictability in first 72 hours. Forecast uplift if executed: +0.9-1.4 TRx index points at Week 26 in "
            "modeled geographies (confidence: medium).",
        )
        _p(
            pdf,
            "Measurement stack ties brand tracking (quarterly), claims pilots (monthly lagged), and demand surge proxies "
            "(weekly) into single Tableau governance dashboard with RLS by franchise role.",
        )
        _p(
            pdf,
            "Next-wave research agenda: conjoint with payer-physician dyads; expand n to 650 for rare subgroup stability on "
            "hepatology referral practices.",
        )
        _bullets(
            pdf,
            [
                "Archive analytical code v1.4 in Git with signed audit trail for reproducibility.",
                "All conclusions for external use require sign-off by Market Research and Legal.",
            ],
        )

    return _two_pass(
        fn,
        "IMM Market Insights",
        "Market Research Insights Report",
        "Nexara launch planning wave -- integrated quantitative and qualitative insights (synthetic)",
        [
            "MR-NXR-2026-W03",
            "Classification: Confidential -- Commercial analytics",
            "Authors: Customer Insights, Immunology; HEOR analytics partnership",
        ],
        [
            ("1. Survey methodology and data quality", m01_method),
            ("2. Physician attitudes, switching, and channels", m02_physician),
            ("3. Patient journey mapping composites", m03_journey),
            ("4. Claims analytics: persistence and comorbidity", m04_claims),
            ("5. Payer research and choice experiments", m05_payer_res),
            ("6. Digital behavior and creative diagnostics", m06_digital),
            ("7. Strategic synthesis and next research waves", m07_synthesis),
        ],
    )


def build_incentive_comp_plan() -> str:
    fn = "Incentive_Compensation_Plan_FY2026.pdf"

    def i01_overview(pdf: CommercialPDF) -> None:
        _h2(pdf, "Plan overview, eligibility, and governance")
        _p(
            pdf,
            "The FY2026 Incentive Compensation Plan applies to U.S. Immunology customer-facing roles in salary grades "
            "CE-12 through CE-16 inclusive, encompassing professional representatives, district managers, regional directors, "
            "and aligned reimbursement liaisons on hybrid incentive tracks. Plan effective dates: January 1, 2026 -- "
            "December 31, 2026; proration rules apply for hires after February 15 (50% guarantee period reduced) "
            "and transfers between brackets mid-year using blended attainment schedules in Appendix C (referenced "
            "conceptually here).",
        )
        _p(
            pdf,
            "Plan objectives align shareholder value with compliant growth: 55% emphasis on revenue versus goal, 20% on "
            "launch milestones for Nexara, 15% on payer access pull-through metrics, 10% on behavioral quality scores. "
            "Compensation committee retains discretion to adjust pools for material macro events (e.g., regulatory "
            "actions) within SOX-documented bounds; any discretionary uplift capped at +8% of target IC aggregate without "
            "board reapproval.",
        )
        _p(
            pdf,
            "Eligibility requires active employment on payout dates except for qualifying terminations per severance policy "
            "addendum; leave-of-absence participants accrue targets only for active months >15 days. Ethical violations "
            "trigger mandatory HR/legal review and may nullify awards pursuant to Code of Conduct Section 4.7.",
        )
        _bullets(
            pdf,
            [
                "Plan documents maintained in Workday Total Rewards module version IC-IMM-US-2026-R2.",
                "Foreign assignment tax gross-ups handled per mobility policy MDY-09.",
            ],
        )

    def i02_quota(pdf: CommercialPDF) -> None:
        _h2(pdf, "Quota methodology, allocation, and fairness controls")
        _p(
            pdf,
            "Territory quotas derive from bottom-up TRx potential models blending three-year Rx history, access tier "
            "assumptions, and promotional lift elasticities estimated via hierarchical Bayes. National control totals tie "
            "to Board-approved revenue plan $1.12B immunology orals net for FY2026; district roll-ups constrained within "
            "+/-1.8% of impartial national benchmark to prevent gaming via sandbag clustering.",
        )
        _p(
            pdf,
            "Greenfield territories receive ramp curves: Q1 at 35% of steady-state run-rate equivalent, Q2 60%, Q3 80%, "
            "Q4 100% with smoothing to avoid cliff incentives. Redistribution after mid-year acquisitions uses Shapley "
            "fair-share approximation across affected reps with union notification where CBAs apply.",
        )
        _p(
            pdf,
            "Quota fairness index monitored: Gini coefficient on quota-to-potential ratios must remain below 0.28; People "
            "Analytics reports quarterly to Sales Operations steering team.",
        )
        _bullets(
            pdf,
            [
                "Representatives may request formal quota review within 10 business days of year start with documented "
                "data issues.",
                "Managers may not unilaterally adjust quota; Finance attestation required.",
            ],
        )

    def i03_measures(pdf: CommercialPDF) -> None:
        _h2(pdf, "Performance measures, weighting, and measurement definitions")
        _p(
            pdf,
            "Revenue vs goal measured on net shipped and recognized sales credited to territory via aligned SAP postings, "
            "excluding returns >90 days and government chargebacks pending reconciliation >45 days. Launch component tracks "
            "Nexara NRx milestone stairs at Months 3/6/9: achievements pay at 0.6/0.2/0.2 fractional weights internal to "
            "the 20% launch bucket.",
        )
        _p(
            pdf,
            "Access pull-through index combines PA approval velocity (40%), reversal rate delta vs Q4 2025 baseline (35%), "
            "and specialty pharmacy SLA compliance (25%) aggregated at district level with individual attribution where "
            "CRM linkage score >0.85 confidence.",
        )
        _p(
            pdf,
            "Behavioral quality compiles SQM scores (70%) and Sunshine compliance attestations (30%); critical compliance "
            "events zero the entire IC payout for responsible individuals upon final investigation outcome.",
        )
        _bullets(
            pdf,
            [
                "All metrics freeze 35 calendar days post period for accounting true-ups.",
                "Data lineage documented in Collibra governance catalog metric IDs IM-ICE-01 through IM-ICE-22.",
            ],
        )

    def i04_payout(pdf: CommercialPDF) -> None:
        _h2(pdf, "Payout structure, thresholds, and gates")
        _p(
            pdf,
            "Payout curve is linear between 95%-100% attainment at target IC rates; from 100%-110% slope increases to "
            "1.4x per point; above 110% enters capped accelerators per section i05. Below 95% pays at 0.6x per point down "
            "to 85% floor where payout hits zero for revenue component unless rescue policy in distressed access territories "
            "approved by VP Sales (limited pool 0.9% of payroll).",
        )
        _p(
            pdf,
            "Minimum performance gate: revenue metric must achieve >=92% unofficial threshold to unlock launch and access "
            "multipliers even if those buckets exceed goal--prevents imbalanced gaming.",
        )
        _p(
            pdf,
            "Clawback provisions apply for restatements, credit memos discovered in subsequent quarters, and CRM fraud; "
            "Finance may debit future payroll or demand repayment within 18 months.",
        )
        _bullets(
            pdf,
            [
                "Payout currency USD; no equity substitution for CE-15 and below.",
                "Tax withholding per IRS supplemental rates; state variations apply.",
            ],
        )

    def i05_accel(pdf: CommercialPDF) -> None:
        _h2(pdf, "Accelerators, stretch tiers, and team multipliers")
        _p(
            pdf,
            "National accelerator pool funds when division exceeds 103% revenue and Nexara launch exceeds 105% of stair "
            "milestone composite; individual share proportional to target IC and local attainment capped at 1.35x total IC "
            "multiple versus target to mitigate excessive risk-taking behaviors.",
        )
        _p(
            pdf,
            "District team multiplier (+2% to +6%) triggers when district maintains SQM >48 AND compliance zero-ticket "
            "quarters; pooled evenly among eligible reps excluding probationary employees.",
        )
        _p(
            pdf,
            "Stacking rules: accelerators apply after base curve math; order of operations documented in calculation "
            "spec sheet available to managers read-only.",
        )
        _bullets(
            pdf,
            [
                "Simulations show 96th percentile earner at $287K total cash under bullish case--handled in SEC CD&A footnotes.",
                "Board Talent Committee reviews curve shapes annually for risk culture alignment.",
            ],
        )

    def i06_contests(pdf: CommercialPDF) -> None:
        _h2(pdf, "SPIFFs, contests, and promotional tournaments")
        _p(
            pdf,
            "Quarterly contests may reward compliant excellence in access pull-through or scientific dialogue scores; prizes "
            "limited to non-cash merchandise under $750 FMV or experiential awards pre-approved by Compliance. No "
            "contest may reward raw TRx volume alone--mixed metrics with quality weight >=40% mandatory.",
        )
        _p(
            pdf,
            "Sunshine reporting captures all transferable value; marketing-run contests must file legal memos 30 days prior to "
            "launch. Leaderboards anonymize until quarter close to reduce inappropriate pressure on clinicians.",
        )
        _p(
            pdf,
            "Anti-discrimination review ensures contest design does not disadvantage protected classes; People Analytics "
            "validates disparate impact statistics p>0.05 threshold.",
        )
        _bullets(
            pdf,
            [
                "Contest opt-out accommodations for medical leave without penalty.",
                "International reps excluded unless explicitly named in addendum.",
            ],
        )

    def i07_appeals(pdf: CommercialPDF) -> None:
        _h2(pdf, "Appeals process, disputes, and audit rights")
        _p(
            pdf,
            "Employees may submit structured appeals within 15 calendar days of preliminary statement delivery via "
            "ServiceNow IC-Appeals queue. Acceptable grounds: data linkage errors, territory misassignment, documented "
            "systems outages affecting measurement, or quota mis-specification acknowledged by Finance.",
        )
        _p(
            pdf,
            "Appeals committee comprises Sales Ops director (chair), HRBP, Finance controller designee, and Compliance "
            "observer without vote. Decisions within 20 business days; summary statistics reported to Audit Committee "
            "annually.",
        )
        _p(
            pdf,
            "Aggregate dispute findings >2.5% of population trigger mandatory recalc of national dashboards and vendor "
            "quality review for data suppliers.",
        )
        _p(
            pdf,
            "Participants may request personal calculation workbook redacted for peers--released under NDA to employee "
            "only; managerial view requires RACI approval.",
        )
        _bullets(
            pdf,
            [
                "Retaliation for filing appeals prohibited; whistleblower protections apply.",
                "Final plan interpretation rests with CFO office in tie-break scenarios documented within 5 days.",
            ],
        )

    return _two_pass(
        fn,
        "FY2026 IC Plan",
        "Incentive Compensation Plan FY2026",
        "U.S. Immunology customer-facing roles -- policy and mechanics (synthetic)",
        [
            "IC-IMM-US-2026-R2",
            "Classification: Internal -- HR & Finance controlled",
            "Prepared by: Sales Operations & Total Rewards",
        ],
        [
            ("1. Plan overview, eligibility, and governance", i01_overview),
            ("2. Quota methodology and fairness controls", i02_quota),
            ("3. Performance measures and definitions", i03_measures),
            ("4. Payout structure, gates, and clawbacks", i04_payout),
            ("5. Accelerators and team multipliers", i05_accel),
            ("6. SPIFFs, contests, and compliance design", i06_contests),
            ("7. Appeals, disputes, and audit policy", i07_appeals),
        ],
    )


def main() -> None:
    _ensure_volume()

    builders = [
        build_launch_playbook,
        build_competitive_intel,
        build_field_force_guide,
        build_market_research_report,
        build_incentive_comp_plan,
    ]

    for builder in builders:
        builder()


main()
