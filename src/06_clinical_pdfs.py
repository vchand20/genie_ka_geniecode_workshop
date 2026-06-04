# Databricks notebook source
"""
Clinical Pharma Workshop -- Synthetic Clinical PDF Corpus for Knowledge Assistant RAG

Generates five extensive, medically realistic PDF documents under Unity Catalog volume
``/Volumes/<catalog>/<schema>/documents``.

Requires network access for ``pip install`` on first run.
"""

import subprocess

subprocess.check_call(["pip", "install", "fpdf2"])

import os
from datetime import date
from typing import List, Sequence

from fpdf import FPDF

# --- Configuration ---
dbutils.widgets.text("catalog", "pharma_workshop", "Catalog Name")
CATALOG = dbutils.widgets.get("catalog").strip()
assert CATALOG, "ERROR: Please provide a catalog name in the widget above before running."
SCHEMA = "wsp_clinical"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/documents"



# ---------------------------------------------------------------------------
# PDF foundation (built-in fonts only: Helvetica, Times, Courier)
# ---------------------------------------------------------------------------


class ClinicalPDF(FPDF):
    """A4 portrait PDF with titled footer page x / {nb}."""

    def __init__(self, footer_tag: str) -> None:
        super().__init__()
        self.footer_tag = footer_tag
        self.set_margins(14, 14, 14)
        self.set_auto_page_break(auto=True, margin=18)
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



def _p(pdf: ClinicalPDF, text: str, size: int = 10) -> None:
    pdf.set_font("Helvetica", "", size)
    pdf.multi_cell(0, 4.8, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.2)


def _h1(pdf: ClinicalPDF, title: str) -> None:
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _h2(pdf: ClinicalPDF, title: str) -> None:
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.multi_cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _h3(pdf: ClinicalPDF, title: str) -> None:
    pdf.ln(1.2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 5.5, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.8)


def _bullets(pdf: ClinicalPDF, items: Sequence[str], size: int = 10) -> None:
    pdf.set_font("Helvetica", "", size)
    for it in items:
        line = f"- {it}"
        pdf.multi_cell(0, 4.8, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _title_page(pdf: ClinicalPDF, main: str, subtitle: str, lines: Sequence[str]) -> None:
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_x(15)
    pdf.ln(36)
    pdf.set_font("Times", "B", 22)
    pdf.multi_cell(0, 10, main, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 6, subtitle, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(18)
    pdf.set_font("Helvetica", "", 10)
    for ln in lines:
        pdf.multi_cell(0, 5.5, ln, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, f"Generated synthetic training document -- {date.today().isoformat()}", align="C", new_x="LMARGIN", new_y="NEXT")


def _toc(pdf: ClinicalPDF, entries: Sequence[str]) -> None:
    pdf.add_page()
    _h1(pdf, "Table of Contents")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0,
        5,
        "The following sections reflect the structure of this controlled document. "
        "Page numbers appear in the document footer for traceability.",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(3)
    for e in entries:
        pdf.multi_cell(0, 5.2, f"- {e}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _table(
    pdf: ClinicalPDF,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    col_widths: Sequence[float],
    fontsize: int = 8,
) -> None:
    """Simple bordered table using Courier; wraps cell text with uniform row height."""
    line_h = 4.8
    pdf.set_font("Courier", "B", fontsize)
    for i, htxt in enumerate(headers):
        pdf.multi_cell(
            col_widths[i],
            line_h,
            str(htxt),
            border=1,
            new_x="RIGHT",
            new_y="TOP",
            max_line_height=pdf.font_size + 1,
        )
    pdf.ln(line_h)
    pdf.set_font("Courier", "", fontsize)
    for row in rows:
        for i, cell in enumerate(row):
            pdf.multi_cell(
                col_widths[i],
                line_h,
                str(cell),
                border=1,
                new_x="RIGHT",
                new_y="TOP",
                max_line_height=pdf.font_size + 1,
            )
        pdf.ln(line_h)
    pdf.ln(2)


def _dense_block(
    pdf: ClinicalPDF,
    paragraphs: Sequence[str],
) -> None:
    for para in paragraphs:
        _p(pdf, para)


# ---------------------------------------------------------------------------
# Document 1 -- Phase III Protocol (~28 pages)
# ---------------------------------------------------------------------------


def build_protocol_zyn301() -> str:
    fn = "Phase_III_Clinical_Study_Protocol_ZYN_301.pdf"
    path = _out_pdf(fn)
    pdf = ClinicalPDF("ZYN-301 Protocol")

    _title_page(
        pdf,
        "Clinical Study Protocol",
        "A Phase III, Randomized, Double-Blind, Placebo-Controlled Study of Zynvara(TM) (ZYN-301) "
        "in Patients with Moderate-to-Severe Active Crohn's Disease",
        [
            "Protocol Number: ZYN-301-CD-301",
            "EudraCT: 2025-004321-12   |   IND: 135,792",
            "Sponsor: NovaThera Biosciences, Inc.",
            "Confidential -- For use by qualified investigators and regulators only.",
        ],
    )
    _toc(
        pdf,
        [
            "1. Protocol synopsis",
            "2. Introduction and scientific background",
            "3. Study objectives and endpoints",
            "4. Study design and investigational plan",
            "5. Study population: eligibility and discontinuation",
            "6. Study assessments and visit schedule",
            "7. Statistical considerations and interim analyses",
            "8. Safety monitoring, pharmacovigilance, and risk mitigation",
            "9. Data management, electronic systems, and traceability",
            "10. Ethics, privacy, regulatory compliance, and study oversight",
            "11. Document control, amendments, and publication policy",
        ],
    )

    _h1(pdf, "1. Protocol synopsis")
    _dense_block(
        pdf,
        [
            "This Phase III clinical study evaluates the efficacy, safety, tolerability, and "
            "patient-reported outcomes of Zynvara(TM) (ZYN-301), a selective oral integrin antagonist, in adults "
            "with moderate-to-severe Crohn's disease who have had inadequate response, loss of response, or "
            "intolerance to one or more conventional or biologic therapies. The study is conducted in "
            "accordance with the ethical principles of the Declaration of Helsinki, ICH E6(R2) GCP, and "
            "applicable regional regulatory requirements (21 CFR Parts 312 and 50 in the United States; EU "
            "Clinical Trials Regulation where applicable).",
            "Sponsor and accountable oversight are maintained through a central project team, qualified "
            "medical monitors, pharmacovigilance, and an independent Data Safety Monitoring Board (DSMB). "
            "Clinical activities are performed by qualified investigative sites under delegated responsibilities "
            "documented in study agreements and monitoring plans. Source data will be attributable, legible, "
            "contemporaneous, original, accurate, and complete (ALCOA+), with audit trails maintained in the "
            "electronic data capture (EDC) system.",
            "The synopsis below summarizes essential study attributes. Detailed procedures, assessments, "
            "definitions, and analytical specifications are provided in subsequent sections and in referenced "
            "manuals (e.g., laboratory manual, imaging charter, patient-reported outcome [PRO] manual, and "
            "investigational medicinal product [IMP] accountability manual).",
        ],
    )
    _h2(pdf, "Synopsis table -- administrative and scientific identifiers")
    _table(
        pdf,
        ["Field", "Details"],
        [
            ("Official title", "ZYN-301-CD-301: A Phase III trial in Crohn's disease (CD)."),
            ("Phase", "Phase III"),
            ("Indication", "Moderate-to-severe active CD with objective evidence of inflammation."),
            ("IMP", "Zynvara (ZYN-301) oral tablets: 45 mg and 90 mg strengths."),
            ("Comparator", "Matching placebo."),
            ("Population", "Adults 18-65 years; CDAI 220-450 at screening; SES-CD >=6."),
            ("Randomized N", "Approximately 900 participants (1:1:1 allocation)."),
            ("Primary endpoint", "Clinical remission at Week 52 (CDAI <150 and no corticosteroids)."),
            ("Key secondary endpoints", "Endoscopic response; corticosteroid-free remission; IBDQ change."),
            ("Study duration", "Up to 62 weeks (up to 2-week screening; 52-week treatment; 8-week follow-up)."),
        ],
        [55, 127],
    )

    _h1(pdf, "2. Introduction and scientific background")
    _dense_block(
        pdf,
        [
            "Crohn's disease is a chronic, immune-mediated inflammatory condition of the gastrointestinal tract "
            "characterized by transmural inflammation, relapsing-remitting course, and progressive bowel damage "
            "in a substantial subset of patients. Clinically, patients experience abdominal pain, diarrhea, "
            "fatigue, weight loss, and extraintestinal manifestations. Endoscopic and imaging evidence "
            "correlates with long-term outcomes, including hospitalization, surgery, and disability. Despite "
            "approved advanced therapies targeting tumor necrosis factor, interleukin-12/23, integrins, "
            "sphingosine-1-phosphate modulation, and Janus kinase inhibition, durable disease control remains "
            "elusive for many patients, and safety considerations (infection risk, cardiovascular events, "
            "malignancy signal evaluation) continue to shape benefit-risk decision-making.",
            "ZYN-301 is a novel small molecule designed to selectively inhibit lymphocyte trafficking mediated by "
            "integrin-ligand interactions involved in gut-homing pathways, with favorable preclinical "
            "differentiation from legacy agents based on in vitro potency, kinase selectivity panels, and "
            "nonclinical toxicology margins. Phase I single-ascending-dose and multiple-ascending-dose studies "
            "in healthy volunteers demonstrated dose-proportional exposure, acceptable tolerability, and "
            "pharmacodynamic changes consistent with target engagement. Phase IIb study ZYN-301-CD-202 "
            "(N=318) showed higher rates of endoscopic improvement versus placebo at Week 12 with doses "
            "45 mg and 90 mg once daily, with a safety profile typified by mild-to-moderate gastrointestinal "
            "symptoms, transient liver enzyme elevations generally <3x upper limit of normal (ULN), and "
            "no imbalance in serious infections versus placebo through Week 24.",
            "This Phase III program aims to confirm clinical benefit in a global population using rigorous "
            "efficacy endpoints aligned with regulatory guidance for inflammatory bowel disease trials, while "
            "maintaining comprehensive safety surveillance including hepatic monitoring, infection surveillance, "
            "and structured assessment of cardiovascular risk biomarkers. The study incorporates standardized "
            "central reading of endoscopy and MRI enterography substudies (where locally feasible), standardized "
            "laboratory definitions for potential Hy's law scenarios, and expedited reporting pathways for "
            "suspected unexpected serious adverse reactions (SUSARs).",
        ],
    )

    _h1(pdf, "3. Study objectives and endpoints")
    _h2(pdf, "3.1 Primary objective")
    _p(
        pdf,
        "To compare the efficacy of ZYN-301 45 mg QD, ZYN-301 90 mg QD, and placebo in establishing "
        "clinical remission at Week 52 in participants with moderate-to-severe Crohn's disease.",
    )
    _h2(pdf, "3.2 Secondary objectives")
    _bullets(
        pdf,
        [
            "Compare endoscopic response at Week 52 using centralized Simple Endoscopic Score for Crohn's Disease (SES-CD).",
            "Evaluate corticosteroid-free clinical remission among participants on baseline oral corticosteroids.",
            "Assess change from baseline in Inflammatory Bowel Disease Questionnaire (IBDQ) total score.",
            "Characterize pharmacokinetics in a sparse sampling subset and exposure-response relationships.",
            "Evaluate immunogenicity assessments not expected for a small molecule but included as a template clause for program consistency.",
        ],
    )
    _h2(pdf, "3.3 Endpoint definitions (operationalized)")
    _dense_block(
        pdf,
        [
            "Clinical remission (primary): Crohn's Disease Activity Index (CDAI) <150 at Week 52, without "
            "qualifying increases from the Week 48 visit, and without oral corticosteroids (prednisone "
            "equivalent >5 mg/day) for the final 12 weeks of maintenance. Oral budesonide used at stable "
            "doses for ileal-predominant disease per protocol allowance is handled via a sensitivity analysis.",
            "Endoscopic response: reduction in SES-CD from central read by >=50% from baseline (or SES-CD <=4 "
            "among participants with isolated ileal disease and baseline SES-CD 4-6 per imaging charter).",
            "Corticosteroid-free remission: participants receiving oral corticosteroids at baseline taper per "
            "schedule and achieve steroid-free remission while meeting CDAI remission criteria.",
        ],
    )

    _h1(pdf, "4. Study design and investigational plan")
    _dense_block(
        pdf,
        [
            "This is a multinational, multicenter, randomized, double-blind, placebo-controlled, parallel-group "
            "study with three arms. Randomization is stratified by baseline corticosteroid use (yes/no), prior "
            "biologic failure (yes/no), and geographic region. Interactive response technology assigns treatment "
            "kits with blinded labels; investigational site personnel, participants, sponsor study team with "
            "operational roles that could unblind, and outcome assessors for endoscopy remain blinded through "
            "database lock except during formal unblinded interim analyses performed by an independent "
            "statistical analysis center (ISR).",
            "The study includes an optional intensive pharmacokinetic substudy at selected sites with timed blood "
            "draws and standardized high-fat meal conditions for a food-effect supplement not detailed herein. "
            "Rescue therapy for disease worsening follows a prespecified algorithm requiring sponsor medical "
            "review and documentation of disease activity thresholds; rescue initiates study discontinuation "
            "from primary efficacy analyses per estimand definitions.",
            "Dose modification for potential hepatotoxicity follows Hy's law vigilance definitions: potential "
            "cases trigger IMP hold, enhanced monitoring, repeat tests within 48 hours, and adjudication by a "
            "hepatic expert panel. QT/QTc assessments include triplicate ECGs predose and multiple postdose "
            "timepoints in a dedicated cardiac safety subset (n~=120).",
        ],
    )

    _h1(pdf, "5. Study population: eligibility and discontinuation")
    _h2(pdf, "5.1 Inclusion criteria (selected operational list)")
    inc = [
        "Age 18-65 years inclusive at screening.",
        "Established Crohn's disease diagnosis >=6 months with objective evidence (endoscopy within 12 months or MRI within 6 months).",
        "Moderate-to-severe disease: CDAI 220-450 at screening; average CDAI computed from 7-day stool diary.",
        "SES-CD >=6 from central or qualified local read with photographic documentation for central confirmation.",
        "Inadequate response or intolerance to >=1 conventional therapies or biologic/small molecule advanced therapy.",
        "Agrees to use highly effective contraception if of childbearing potential; negative pregnancy test.",
        "Willingness to discontinue prohibited medications per protocol washout tables.",
        "Ability to comply with visit schedule, PRO completion, and fasting requirements for laboratory panels.",
        "Provision of written informed consent (ICF), including genetic sampling optional subsection where permitted.",
        "No planned elective intestinal surgery within the screening window.",
        "Tuberculosis screening per local guidelines with negative Quantiferon unless documented latent TB treated.",
        "Hepatitis B/C viral serologies negative or consistent with sponsor exclusion criteria if positive.",
        "Sufficient venous access for safety labs; hemoglobin >=10.0 g/dL (females) / >=10.5 g/dL (males) unless consistent with CD.",
        "Albumin >=3.0 g/dL unless acute inflammation-related and reviewed by sponsor physician.",
        "eGFR >=60 mL/min/1.73m^2 using CKD-EPI equation at screening.",
    ]
    _bullets(pdf, inc)
    _h2(pdf, "5.2 Exclusion criteria (selected operational list)")
    exc = [
        "Short bowel syndrome dependency on parenteral nutrition.",
        "Fulminant col toxic megacolon or bowel perforation within 12 weeks.",
        "Known stricturing phenotype requiring imminent dilation/surgery per investigator judgment.",
        "Active fistulae with abscess requiring drainage within 8 weeks (protocol-defined stability required).",
        "History of primary sclerosing cholangitis with complication considered high risk by hepatology consult.",
        "ALT or AST >3x ULN at screening; direct bilirubin >1.5x ULN (unless Gilbert's documented).",
        "History of drug-induced liver injury adjudicated as definite/likely related to investigational agents.",
        "QTcF >450 ms (males) or >460 ms (females) averaged from triplicate ECG (Fridericia).",
        "Recent myocardial infarction, unstable angina, Class III/IV heart failure, or uncontrolled arrhythmia.",
        "Malignancy within 5 years except adequately treated basal cell carcinoma or cervical carcinoma in situ.",
        "Live vaccine within 4 weeks of randomization.",
        "Chronic systemic infection (HIV with CD4 <350, active TB, untreated opportunistic infection).",
        "Receipt of any excluded biologic within washout period (e.g., anti-IL-12/23: 12 weeks; anti-TNF: 8 weeks).",
        "Use of prohibited concomitant therapies: JAK inhibitors, calcineurin inhibitors, investigational agents.",
        "Pregnancy, lactation, or planned pregnancy during study participation.",
        "Alcohol or drug use disorder interfering with protocol compliance per investigator discretion.",
        "Clinically significant lab abnormality not explained by CD and not corrected by baseline week delay.",
        "Prior exposure to ZYN-301 in a clinical trial (any dose).",
        "Employee of sponsor or site vendor with direct involvement in study management (site staff excluded).",
        "Any condition that, in investigator judgment, places participant at unacceptable risk or confounds interpretation.",
    ]
    _bullets(pdf, exc)
    _h2(pdf, "5.3 Withdrawal criteria")
    _bullets(
        pdf,
        [
            "Withdrawal of consent at any time without prejudice to standard medical care.",
            "Confirmed pregnancy during treatment; IMP discontinued immediately.",
            "Hy's law adjudication positive or hepatic injury meeting stopping criteria.",
            "Life-threatening allergic reaction or anaphylaxis attributed to IMP.",
            "Protocol-defined disease worsening requiring rescue biologic therapy initiation.",
            "Investigator determination of safety risk; sponsor concurrence documented.",
            "Lost to follow-up after structured site attempts per lost-to-follow-up SOP.",
        ],
    )

    _h1(pdf, "6. Study assessments and visit schedule")
    _h2(pdf, "6.1 Visit schedule (core table)")
    visits = [
        ("Screening", "Day -14 to -1", "ICF, CDAI diary training, labs, ECG (subset), SES-CD locally"),
        ("Baseline (Week 0)", "Day 1", "Randomization, IMP dispense, predose safety labs, PROs"),
        ("Week 2", "+/-3 days", "Safety labs, AE review, drug accountability"),
        ("Week 4", "+/-3", "Labs, CDAI, con meds, IP check"),
        ("Week 8", "+/-7", "Labs, SES-CD scheduling, endoscopy window opens"),
        ("Week 12", "+/-7", "Primary read for endoscopic endpoint in rolling cohort analyses (supportive)"),
        ("Week 24", "+/-7", "MRI substudy window (selected sites), IBDQ, labs"),
        ("Week 36", "+/-7", "Intensive monitoring visit in hepatic risk subset"),
        ("Week 52", ".14", "Primary endpoint assessments; EOT IMP return"),
        ("Follow-up", "+8 weeks", "Safety follow-up, SAE reconciliation, PRO closure"),
    ]
    _table(pdf, ["Visit", "Target window", "Core procedures"], visits, [42, 38, 102])

    _h2(pdf, "6.2 Safety and efficacy assessments")
    _dense_block(
        pdf,
        [
            "Safety laboratories include comprehensive metabolic panel, complete blood count with differential, "
            "coagulation studies where regionally required, lipase/amylase, and high-sensitivity C-reactive protein (hs-CRP). "
            "Stool calprotectin is collected at prespecified visits for biomarker analyses and supportive efficacy "
            "readouts. Hepatic events trigger enhanced hepatic panel, viral hepatitis serologies, autoimmune "
            "markers, and imaging per hepatology handbook.",
            "Central endoscopy reading uses standardized video acquisition; readers are blinded to treatment and "
            "visit label. Discrepancies above prespecified delta trigger tertiary adjudication. Patient-reported "
            "outcomes are collected on validated ePRO devices with training at screening; compliance thresholds "
            "define missing data rules for primary analyses and tipping-point sensitivity analyses.",
        ],
    )

    _h1(pdf, "7. Statistical considerations and interim analyses")
    _dense_block(
        pdf,
        [
            "Sample size is determined using simulations based on observed placebo and active-arm remission rates "
            "from Phase IIb (placebo ~15%, 45 mg ~29%, 90 mg ~34%) with conservative attenuation for Phase III "
            "heterogeneity. With approximately 300 participants per arm, a two-sided alpha=0.05 pairwise comparison "
            "of each active dose versus placebo achieves >90% power for a 12-15 percentage-point difference in "
            "Week 52 remission, depending on the simulated dropout and missingness model. Multiplicity across "
            "primary hypotheses is controlled using a fixed-sequence procedure testing 90 mg versus placebo "
            "first, then 45 mg versus placebo upon success, with graphical multiplicity extension for key "
            "secondary endpoints.",
            "The primary estimand is a hypothetical strategy addressing intercurrent events: rescue therapy and "
            "early discontinuation are treated as treatment failure for the primary endpoint; sensitivity "
            "estimands include treat-as-treated and composite definitions. Analysis populations include intent-to-treat (ITT), "
            "modified ITT (mITT; participants with baseline SES-CD confirmation), per-protocol (PP; no major "
            "protocol deviations impacting efficacy), and safety (all randomized participants as treated).",
            "One formal interim analysis for futility and potential sample size re-estimation is planned at ~60% "
            "information fraction using asymmetric boundaries; O'Brien-Fleming spending is approximated for "
            "safety signals reviewed by the DSMB, while efficacy stopping for success is discouraged to preserve "
            "long-term Week 52 evidence unless dramatic benefit emerges across endpoints with low probability of "
            "harm. Independent statistical reports are distributed under controlled access with locked randomization "
            "codes maintained in secure environments.",
        ],
    )

    _h1(pdf, "8. Safety monitoring, pharmacovigilance, and risk mitigation")
    _dense_block(
        pdf,
        [
            "Adverse events (AEs) are collected from first dose through follow-up and graded using CTCAE v5.0 where "
            "applicable. Relationship to IMP is assessed by investigators as reasonable possibility categories for "
            "regulatory reporting. Serious adverse events (SAEs) are reported to sponsor within 24 hours of "
            "investigator awareness; sponsor forwards SUSARs to regulators within 15 calendar days (fatal/life-"
            "threatening expedited timelines of 7 days for initial notification with updates).",
            "Dose-limiting toxicities (DLTs) follow oncology paradigms only where applicable; for this program, "
            "DLT analogs are hepatic enzyme thresholds, QTc increases >=30 ms from predose plus absolute >500 ms, "
            "or recurrent severe diarrhea with dehydration. DSMB reviews integrated safety summaries including "
            "infections, hepatic events, MACE surrogates, and malignancy reports quarterly or ad hoc after "
            "pre-specified triggers.",
        ],
    )

    _h1(pdf, "9. Data management, electronic systems, and traceability")
    _dense_block(
        pdf,
        [
            "Data are captured in a 21 CFR Part 11-compliant EDC platform with role-based access controls, "
            "deidentified participant codes, automated query triggers for range checks, and full audit trails. "
            "Electronic informed consent may be deployed where regulators permit, with eSignature workflows. "
            "Central imaging and laboratory vendors transfer results via validated integrations. Database soft-lock "
            "precedes blinded clinical review; hard lock occurs after query resolution and SDV milestones "
            "defined in the monitoring plan.",
        ],
    )

    _h1(pdf, "10. Ethics, privacy, regulatory compliance, and study oversight")
    _dense_block(
        pdf,
        [
            "Institutional review boards/independent ethics committees approve the protocol and ICF prior to "
            "enrollment. GDPR-aligned privacy measures include data minimization, data processing agreements, "
            "standard contractual clauses for cross-border transfers, and participant rights procedures (access, "
            "rectification, restriction). HIPAA protections apply for US sites with business associate agreements. "
            "Clinical trial insurance and indemnification provisions follow sponsor policy templates.",
        ],
    )

    _h1(pdf, "11. Document control, amendments, and publication policy")
    _dense_block(
        pdf,
        [
            "Protocol amendments are submitted to regulators and ethics committees as required prior to "
            "implementation except for urgent safety changes. Version-controlled documents reside in the trial "
            "master file (TMF). Publication committees govern external communications; investigators may publish "
            "site-level academic analyses consistent with sponsor publication policy and preserving confidentiality.",
            "Archiving follows ICH E6(R2) expectations: essential documents retained for at least 25 years unless "
            "local law dictates longer retention. Destruction of identifiable materials occurs under documented "
            "procedures after retention expiration and sponsor authorization.",
        ],
    )

    _h1(pdf, "12. Operational appendices and implementation reference material")
    _h2(pdf, "12.1 Central laboratories, assay validation, and sample management")
    _dense_block(
        pdf,
        [
            "All protocol-required laboratory assessments for hematology, clinical chemistry, coagulation, "
            "serum pregnancy, virology, and stool calprotectin are performed by a central laboratory vendor "
            "using validated methods traceable to international reference standards. Sample collection kits ship "
            "with chain-of-custody manifests; ambient versus cold-chain requirements are specified per analyte. "
            "Laboratories maintain CAP/CLIA accreditation (or regional equivalents) and provide instrument "
            "calibration records during qualification visits. Critical results are communicated to sites through "
            "graded alert pathways consistent with GCP obligations to protect participant welfare.",
            "Assay validation packages document accuracy, precision, linearity, and stability for each assay used "
            "to support primary and secondary endpoints. For calprotectin, fecal homogenization and extraction "
            "variability are monitored using embedded quality samples; longitudinal drift triggers retrospective "
            "review with statistical support. Pharmacokinetic substudy samples use distinct labels and shipping "
            "routes to prevent unblinding of treatment assignment at local sites.",
            "Data transfers use validated EDC integrations; reconciliation between local urgent values and "
            "centrally reported values follows defined medical review and query resolution timelines.",
        ],
    )
    _h2(pdf, "12.2 Imaging charter: endoscopy acquisition, transfer, and central reading")
    _dense_block(
        pdf,
        [
            "Video acquisition uses minimum resolution thresholds, mucosal exposure benchmarks, and segmental "
            "documentation standards to enable reproducible SES-CD scoring. Sites upload encrypted files through "
            "a regulated portal; checksum validation confirms integrity. Readers receive training on lesion "
            "recognition, artifact rejection, and documentation of postoperative anatomy. Inter-reader reliability "
            "kappa targets are monitored; poorly performing readers undergo remedial training or removal.",
            "MRI substudy sites adhere to harmonized pulse sequences and contrast administration rules where "
            "permitted locally. Central MRI reads evaluate inflammatory activity using quantitative MaRIA-like "
            "components adapted to Crohn's disease morphology. Imaging discordances with endoscopy are summarized "
            "for exploratory analyses and do not invalidate primary clinical endpoints without independent "
            "adjudication.",
            "Unscheduled imaging prompted by clinical deterioration is captured as safety data; efficacy analyses "
            "use only protocol-scheduled reads unless otherwise pre-specified in the statistical analysis plan.",
        ],
    )
    _h2(pdf, "12.3 Patient-reported outcomes, diary compliance, and missing data")
    _dense_block(
        pdf,
        [
            "The IBDQ and daily stool frequency diary are administered through validated handheld platforms with "
            "offline sync and timestamp auditing. Diary compliance below prespecified thresholds flags participants "
            "for investigator coaching without coercion; repeated non-compliance is documented as a protocol "
            "deviation. PRO training includes practice examples to reduce misunderstanding of symptom anchors.",
            "Missing item imputation for IBDQ follows the statistical analysis plan; tipping-point analyses "
            "evaluate robustness to alternate missing-not-at-random assumptions. Diary missingness patterns are "
            "summarized by arm in blinded interim safety reviews to exclude systematic device failures.",
            "Cultural adaptation and linguistic validation certificates are maintained in the TMF for each "
            "country-specific translation with reconciliation memos for minor wording updates.",
        ],
    )
    _h2(pdf, "12.4 Randomization integrity, unblinding, and pharmacy interface")
    _dense_block(
        pdf,
        [
            "Interactive response technology (IRT) maintains randomization lists under cryptographic controls; "
            "audit trails record each kit assignment. Emergency unblinding requires dual authorization and "
            "immediate notification to pharmacovigilance; participant welfare rationales are documented. Site "
            "pharmacy manuals define relabeling, temperature excursions, and destruction witnessed by qualified "
            "personnel using sponsor forms.",
            "Partial kit returns occur when dose modifications are not applicable; reconciliation ties tablets "
            "dispensed, consumed, returned, and destroyed across the supply chain using unique serial identifiers.",
            "Label text harmonizes across regions while respecting local language requirements and symbol usage "
            "per ISO standards where adopted.",
        ],
    )
    _h2(pdf, "12.5 Committee charters: ethics, steering, and endpoint adjudication")
    _dense_block(
        pdf,
        [
            "An independent ethics framework governs consent process audits, vulnerable population protections, "
            "and submission of serious breaches to regulators where law requires. A trial steering committee advises "
            "on scientific priorities without access to unblinded comparative efficacy until database lock except "
            "as mandated for participant safety. Hepatic event adjudication uses standardized case narratives, "
            "laboratory timelines, imaging, and medication histories with blinded assessments where feasible.",
            "Endpoint adjudication committees for cardiovascular events follow standardized definitions adapted "
            "from academic consortia; suspected events trigger dossier compilation within 30 days of site "
            "notification.",
            "Committee minutes are retained confidentially; recommendations impacting trial conduct are "
            "communicated through controlled sponsor pathways to avoid informal information leakage.",
        ],
    )
    _h2(pdf, "12.6 Supply forecasting, depot management, and accountable destruction")
    _dense_block(
        pdf,
        [
            "Clinical supply forecasting integrates enrollment curves, screen failure rates, visit windows, and "
            "country-specific import lead times. Temperature-monitored shipments use data loggers; excursions "
            "trigger quarantine until quality disposition. Returns from sites consolidate at regional depots with "
            "environmental monitoring and access control records suitable for regulatory inspection.",
            "Destruction certificates for scheduled destruction batches include witness signatures, batch numbers, "
            "quantities, and environmental compliance references. Reconciliation reports are generated monthly "
            "during active treatment and at study closure.",
            "Comparator matching placebo tablets are indistinguishable in appearance and organoleptic properties "
            "within validated specifications to maintain double-blind integrity.",
        ],
    )
    _h2(pdf, "12.7 Regulatory submissions package alignment and inspection readiness")
    _dense_block(
        pdf,
        [
            "The clinical study report integrates datasets, TLFs, listing conventions, and narrative safety "
            "summaries aligned with ICH E3 structure. Source document verification rates, query aging metrics, "
            "and protocol deviation taxonomies are summarized for agency questions. Mock inspections drill "
            "investigators and coordinators on tracing informed consent through eligibility to endpoint capture.",
            "Clinical trial disclosure obligations (ClinicalTrials.gov, EudraCT results posting) are tracked as "
            "milestones with accountable owners. Statistical programs undergo independent QC prior to database "
            "lock with version-controlled logs.",
            "Country-specific addenda capture local regulatory correspondence, translation certificates, and "
            "local medical monitor contact trees for urgent safety reviews.",
        ],
    )
    _h2(pdf, "12.8 Privacy engineering and cybersecurity controls for eClinical platforms")
    _dense_block(
        pdf,
        [
            "Role-based access implements least privilege with periodic recertification. Multi-factor authentication "
            "protects sponsor users; site users follow sponsor policy templates. Logging captures authentication "
            "events, data exports, and eSignature ceremonies with tamper-evident archival suitable for forensic "
            "review.",
            "Pseudonymization keys segregate from clinical databases; re-identification procedures exist for "
            "pharmacovigilance and regulatory audits under documented approval. GDPR data protection impact "
            "assessments are updated when new vendors or processing activities are introduced.",
            "Penetration testing on externally facing portals follows enterprise schedules; critical remediation "
            "occurs under severity-based SLAs with evidence retained in vendor qualification files.",
        ],
    )

    pdf.output(path)
    return fn


# ---------------------------------------------------------------------------
# Document 2 -- Investigator's Brochure (~25 pages)
# ---------------------------------------------------------------------------


def build_investigators_brochure() -> str:
    fn = "Investigators_Brochure_Zynvara_Edition_7.pdf"
    path = _out_pdf(fn)
    pdf = ClinicalPDF("IB Zynvara Ed.7")

    _title_page(
        pdf,
        "Investigator's Brochure",
        "Zynvara(TM) (ZYN-301) -- Edition 7, 10 May 2026",
        [
            "Sponsor: NovaThera Biosciences, Inc.",
            "Confidential -- Investigational; not approved for commercial use.",
            "This document summarizes nonclinical and clinical data available at time of compilation.",
        ],
    )
    _toc(
        pdf,
        [
            "Summary",
            "Pharmaceutical and physicochemical properties",
            "Nonclinical pharmacology",
            "Nonclinical pharmacokinetics and metabolism",
            "Nonclinical toxicology",
            "Clinical pharmacology",
            "Clinical efficacy",
            "Clinical safety",
            "Summary of benefits and risks",
            "Guidance for investigators",
        ],
    )

    _h1(pdf, "Summary")
    _dense_block(
        pdf,
        [
            "Zynvara (ZYN-301) is an investigational oral integrin pathway modulator intended for immune-mediated "
            "inflammatory diseases, with the most advanced clinical development in moderate-to-severe Crohn's disease. "
            "Nonclinical studies demonstrate selective functional effects on lymphocyte adhesion and gut-homing "
            "patterns at exposures achievable clinically, with margins to adverse findings in repeat-dose toxicology. "
            "Clinical Phase I studies characterized pharmacokinetics, food effect, and tolerability; Phase IIb "
            "provided initial efficacy signals on endoscopic and clinical outcomes.",
            "Common adverse events in clinical trials include nausea, headache, upper respiratory tract infection, "
            "and transient liver enzyme elevations generally <3x ULN without concurrent bilirubin rises meeting "
            "Hy's law criteria. Serious infections have occurred at rates comparable to placebo in controlled periods "
            "but require vigilance given mechanistic immunomodulation. This brochure must be read in conjunction "
            "with the approved protocol, pharmacy manuals, and local labeling/regulatory correspondence.",
        ],
    )

    _h1(pdf, "Pharmaceutical and physicochemical properties")
    _dense_block(
        pdf,
        [
            "ZYN-301 is presented as immediate-release film-coated tablets containing ZYN-301 hemifumarate salt "
            "equivalent to 45 mg or 90 mg free base. The drug substance is a white to off-white crystalline powder "
            "with aqueous solubility pH-dependent (higher at acidic pH), log D ~2.1 at pH 7.4, and molecular formula "
            "C27H31FN6O5S (free base). The coformer imparts improved stability against oxidative pathways observed "
            "in early salt screens.",
            "Tablets contain microcrystalline cellulose, mannitol, croscarmellose sodium, magnesium stearate, and "
            "Opadry II coating systems. Stability data under ICH conditions support retest intervals for drug "
            "substance and shelf life for drug product when stored at 20-25degC. IMP labels specify storage "
            "conditions and batch traceability requirements for site accountability logs.",
        ],
    )

    _h1(pdf, "Nonclinical pharmacology")
    _h2(pdf, "Mechanism of action")
    _dense_block(
        pdf,
        [
            "In vitro cellular adhesion assays show concentration-dependent inhibition of activated T-cell adhesion "
            "to fibronectin and mucosal addressin cell adhesion molecule-1 (MAdCAM-1) under flow conditions "
            "mimicking shear stress in post-capillary venules. ZYN-301 does not broadly inhibit rolling adhesion "
            "at clinically relevant exposures, supporting pathway selectivity relative to pan-integrin profiles. "
            "Ex vivo human lamina propria explants demonstrate reduced cytokine secretion in stimulated conditions "
            "when incubated with ZYN-301, with no effect in unstimulated explants.",
        ],
    )
    _h2(pdf, "In vivo efficacy models")
    _dense_block(
        pdf,
        [
            "Mouse adoptive T-cell transfer colitis models show dose-dependent reductions in colon weight:length "
            "ratio, histopathology scores, and fecal calprotectin-like surrogate proteins. Non-human primate (NHP) "
            "studies in mild immune activation models identified a no observed adverse effect level (NOAEL) for "
            "clinical projection based on exposure multiples. Translatability caveats include species differences "
            "in integrin expression and compensatory trafficking pathways; thus, human clinical outcomes remain "
            "authoritative for benefit-risk assessment.",
            "Secondary pharmacology screening across 168 targets (ion channels, GPCRs, kinases) at 10 muM identified "
            "minimal off-target hits requiring follow-up; hERG patch clamp IC50 margins exceed 30x unbound peak "
            "clinical Cmax in the therapeutic dose range under standard assumptions.",
        ],
    )

    _h1(pdf, "Nonclinical pharmacokinetics and metabolism")
    _dense_block(
        pdf,
        [
            "Absorption is rapid with median Tmax ~2 hours under fasted conditions in NHP; a high-fat meal increases "
            "AUC ~1.25-fold and delays Tmax without clinically required dosing restrictions in later-phase trials. "
            "Plasma protein binding in human plasma is ~88% (f_u ~0.12). Distribution into lymphoid tissues is "
            "observed in NHP mass balance studies with modest penetration across the blood-brain barrier consistent "
            "with P-gp substrate liability.",
            "Metabolism is primarily mediated by CYP3A4 with minor contributions from CYP2C9; primary metabolites "
            "M1 (hydroxyl) and M2 (N-dealkyl) circulate at lower exposures and are not considered pharmacodynamically "
            "active at clinical concentrations. Elimination is balanced renal/fecal with ~42% parent-related material "
            "recovered in feces and ~18% in urine within 168 hours in radiolabeled human ADME study (n=6).",
        ],
    )

    _h1(pdf, "Nonclinical toxicology")
    _h2(pdf, "General toxicity and safety pharmacology")
    _dense_block(
        pdf,
        [
            "In 4-week and 26-week repeat-dose rodent studies, the primary findings were mild liver enzyme elevations "
            "at high multiples, non-adverse thymic lymphoid depletion at mid/high doses, and reversible gastric "
            "epithelial hypertrophy correlating with local GI exposure. Dog studies identified emesis and diarrhea at "
            "escalated exposures; dose reductions mitigated findings. The NOAEL in the 26-week rat study corresponded "
            "to approximately 18x human AUC at the 90 mg clinical dose under worst-case bridging assumptions.",
            "Genotoxicity battery (Ames, in vitro micronucleus, in vivo rat micronucleus) was negative. "
            "Carcinogenicity studies are ongoing under regulatory agreements; interim pathology surveillance from "
            "26-week rodent studies identified no preneoplastic lesions attributable to IMP. Embryo-fetal development "
            "studies in rats and rabbits showed maternal toxicity at high doses with fetal skeletal variations within "
            "historical control ranges at non-maternally toxic doses.",
        ],
    )

    _h1(pdf, "Clinical pharmacology")
    _table(
        pdf,
        ["Parameter", "90 mg QD (fasted)", "Notes"],
        [
            ("Cmax (ng/mL)", "812 (30% CV)", "Phase I pooled"),
            ("AUC0-24 (ng.h/mL)", "6,420 (28% CV)", "Supports QD dosing"),
            ("t1/2 (h)", "9.4", "Exponential terminal phase"),
            ("CL/F (L/h)", "14.1", "Apparent oral clearance"),
            ("Vz/F (L)", "187", "Apparent volume"),
        ],
        [52, 52, 78],
        fontsize=8,
    )
    _dense_block(
        pdf,
        [
            "Drug-drug interaction potential: strong CYP3A4 inhibitors are predicted to increase ZYN-301 exposure "
            "~2-fold; inducers decrease exposure. Lipid-lowering statins sensitive to transporter interactions show "
            "minimal clinically relevant changes in Phase I cocktail studies except pravastatin (~22% AUC increase). "
            "Renal impairment: mild/moderate eGFR reduction does not require dose adjustment due to low renal clearance "
            "contribution; severe impairment studied in dedicated cohort (n=16) supports conservative dosing guidance. "
            "Hepatic impairment: moderate Child-Pugh B shows ~1.4-fold AUC increase; Child-Pugh C excluded from trials.",
        ],
    )

    _h1(pdf, "Clinical efficacy")
    _dense_block(
        pdf,
        [
            "Phase IIb ZYN-301-CD-202 enrolled 318 participants randomized 1:1:1:1 to placebo, 15 mg, 45 mg, and "
            "90 mg. At Week 12, SES-CD response rates were 28%, 35%, 42%, and 47% versus placebo with nominal "
            "p-values <0.05 for 45 mg and 90 mg in the primary endoscopic analysis. Clinical response and remission "
            "showed supportive trends; corticosteroid taper success was higher in active arms among steroid-using "
            "participants.",
            "Subgroup analyses by prior biologic failure status, baseline CRP, and ileal versus colonic involvement "
            "did not identify heterogeneity that definitively negates treatment benefit, though power was limited. "
            "Patient-reported outcome analyses demonstrated improvements in IBDQ bowel and social subscores at Week 12 "
            "that correlated modestly with objective inflammation changes (Spearman rho ~0.32).",
            "Exploratory analyses of stool metagenomics and circulating protein panels are ongoing under separate "
            "informatics governance; initial readouts suggest modulation of mucosal inflammatory pathways without "
            "broad immunosuppression signatures in blood transcriptional modules.",
        ],
    )

    _h1(pdf, "Clinical safety")
    _table(
        pdf,
        ["Adverse event (MedDRA PT)", "Placebo (n=84)", "ZYN pooled (n=234)", "Comment"],
        [
            ("Nausea", "6 (7.1%)", "38 (16.2%)", "Most mild; median duration 4 days"),
            ("Headache", "9 (10.7%)", "31 (13.2%)", "Clustered early dosing period"),
            ("ALT increased", "2 (2.4%)", "12 (5.1%)", "Most <2x ULN; reversible"),
            ("Upper respiratory infection", "11 (13.1%)", "24 (10.3%)", "No pattern of atypical infection"),
            ("Nasopharyngitis", "8 (9.5%)", "19 (8.1%)", "Seasonal clustering"),
        ],
        [58, 32, 32, 60],
        fontsize=7,
    )
    _dense_block(
        pdf,
        [
            "Serious adverse events occurred in 6.0% placebo versus 7.3% active across doses; no single cluster "
            "dominated. One adjudicated MACE occurred in active arm with contributing risk factors (diabetes, "
            "hypertension, smoking); causal relationship considered unlikely. Hepatic serious events: one "
            "cholestatic pattern deemed possibly related; resolved after IMP discontinuation. No Hy's law cases "
            "observed in clinical database through Edition 7 cut-off.",
            "Electrocardiographic pooled analysis shows mean QTcF change from baseline <5 ms at trough and +8 ms "
            "at 2 h postdose on Day 1 (90 mg), below thresholds of regulatory concern using ICH E14 definitions; "
            "categorical outliers >450 ms infrequent and balanced across arms.",
        ],
    )

    _h1(pdf, "Summary of benefits and risks")
    _dense_block(
        pdf,
        [
            "Potential benefits include improvement of endoscopic and clinical disease activity, corticosteroid "
            "reduction, and quality-of-life gains in a population with limited durable options. Risks include "
            "gastrointestinal intolerance, hepatic enzyme elevations, infection vigilance requirements, and unknown "
            "long-term safety pending Phase III and postmarketing experience. Benefit-risk remains favorable within "
            "protocol-defined monitoring for the intended study population; deviations require sponsor medical "
            "consultation.",
        ],
    )

    _h1(pdf, "Guidance for investigators")
    _bullets(
        pdf,
        [
            "Dispense IMP only to randomized participants; verify identity at each visit.",
            "Instruct participants to report infections promptly; hold dosing for febrile illness per algorithm.",
            "Perform hepatic monitoring at visits; if ALT/AST >3x ULN, repeat within 48-72 h and notify sponsor.",
            "ECG monitoring per schedule in cardiac subset; hold if QTcF thresholds exceeded.",
            "Contraception requirements apply for duration of therapy plus 90 days post last dose (semen donors: 90 days).",
            "Do not co-administer strong CYP3A4 inhibitors without sponsor approval; document concomitant meds.",
        ],
    )

    _h1(pdf, "Annexes to Edition 7 (clinical integration topics)")
    _h2(pdf, "Annex A -- Exposure-response and concentration-QT analyses")
    _dense_block(
        pdf,
        [
            "Population PK models integrate sparse Phase IIb samples with rich Phase I data using nonlinear mixed-"
            "effects estimation. Covariates screened include body weight, sex, age, albumin, and Crohn's disease "
            "severity markers; final covariate models retain only statistically supported and clinically plausible "
            "relationships. Simulated exposures at 45 mg and 90 mg bracket observed concentration quartiles for "
            "efficacy and safety dose-response visualizations.",
            "Concentration-QT analyses use baseline-adjusted DeltaDeltaQTcF modeling with time-matched placebo correction "
            "where possible. Slope estimates for unbound concentration remain below regulatory thresholds under "
            "worst-case adherence assumptions; categorical analyses confirm absence of clinically meaningful "
            "outlier clustering.",
        ],
    )
    _h2(pdf, "Annex B -- Immunogenicity considerations for combination development partners")
    _dense_block(
        pdf,
        [
            "Although ZYN-301 is a small molecule, combination studies with monoclonal antibodies require vigilance "
            "for overlapping infection risk and pharmacodynamic interactions. Washout windows and corticosteroid "
            "bridging strategies follow cross-program medical governance. Pregnancy prevention and documented "
            "counseling intensify when teratogenic partners or contraceptive interactions are contemplated.",
        ],
    )
    _h2(pdf, "Annex C -- Global safety surveillance and benefit-risk update cycle")
    _dense_block(
        pdf,
        [
            "Aggregate safety reviews occur quarterly during active trials: infections, hepatic laboratory shifts, "
            "MACE, malignancy, and pregnancy outcomes undergo structured narrative synthesis. Signal detection "
            "methods include disproportionality analyses within sponsor databases adjusted for confounders when "
            "feasible. Reference safety information updates trigger investigator notification letters when "
            "warranted across regions.",
            "Risk minimization measures include dosing holds for acute infections, vaccination guidance consistent "
            "with immunology expert statements, and site training refreshers after protocol amendments affecting "
            "safety labs or ECG monitoring.",
        ],
    )
    _h2(pdf, "Annex D -- Pediatric investigation plan cross-reference and deferral strategy")
    _dense_block(
        pdf,
        [
            "Pediatric development, if required by regulatory agreements, defers initiation until adequate adult "
            "exposure and growth plate biology assessments are complete in juvenile animal models where mandated. "
            "Age-appropriate formulations would undergo separate bioavailability bridging depending on regional "
            "scientific advice outcomes.",
        ],
    )
    _h2(pdf, "Annex E -- Analytical methods for drug substance and product quality control")
    _dense_block(
        pdf,
        [
            "Release specifications include identity, assay, impurities, dissolution, and water content within ICH "
            "Q3A/B-aligned acceptance criteria. Stability-indicating methods separate forced-degradation peaks; "
            "reference standards are qualified with documented traceability chains. Complaint investigations "
            "follow gated workflows with potential recall simulations for high-risk defects.",
        ],
    )
    _h2(pdf, "Annex F -- Environmental risk and manufacturing occupational health (development context)")
    _dense_block(
        pdf,
        [
            "During clinical supply manufacturing, occupational exposure limits and engineering controls align with "
            "ICH Q3C residual solvent guidance and facility EHS policies. Environmental fate modeling for API "
            "discharges supports future marketing authorization environmental risk assessment packages where "
            "legislatively required.",
        ],
    )
    _h2(pdf, "Annex G -- Third-party vendor qualification for bioanalytical support")
    _dense_block(
        pdf,
        [
            "Bioanalytical laboratories validating validated LC-MS/MS methods for ZYN-301 and metabolites adhere "
            "to CDER/CBER biomethod validation guidance with incurred sample reanalysis acceptance criteria. "
            "Incurred sample trends trigger root cause investigations; study reports include run summaries and "
            "ISR tables for regulatory filing integration.",
        ],
    )
    _h2(pdf, "Annex H -- Investigator communication and safety Dear Investigator letters")
    _dense_block(
        pdf,
        [
            "Important safety updates are distributed through tracked email and portal acknowledgments; IRB/IEC "
            "submissions follow local turnaround expectations. Training logs record team member review of each "
            "material revision before continued enrollment unless ethics bodies approve alternative timelines for "
            "minimal risk clarifications.",
        ],
    )

    pdf.output(path)
    return fn


# ---------------------------------------------------------------------------
# Document 3 -- DSMB Charter (~15 pages)
# ---------------------------------------------------------------------------


def build_dsmb_charter() -> str:
    fn = "DSMB_Charter_ZYN_301.pdf"
    path = _out_pdf(fn)
    pdf = ClinicalPDF("DSMB Charter ZYN-301")

    _title_page(
        pdf,
        "Data Safety Monitoring Board Charter",
        "Study ZYN-301-CD-301 (Zynvara Phase III Crohn's Disease Program)",
        [
            "Sponsor: NovaThera Biosciences, Inc.",
            "Document Version: 2.0   Effective Date: 10 May 2026",
        ],
    )
    _toc(
        pdf,
        [
            "Purpose and authority",
            "Membership, independence, conflicts of interest",
            "Responsibilities and scope of review",
            "Meeting schedule and ad hoc convening",
            "Operating procedures, quorum, voting",
            "Data review process: open and closed sessions",
            "Statistical monitoring and alpha-spending framework",
            "Stopping rules: efficacy, futility, safety",
            "Communications with sponsor, investigators, and regulators",
            "Confidentiality and document retention",
            "Appendices: recommendation templates and interim SAP outline",
        ],
    )

    _h1(pdf, "1. Purpose and authority")
    _dense_block(
        pdf,
        [
            "The Data Safety Monitoring Board (DSMB) is an independent expert panel established to protect "
            "participant safety and trial integrity while preserving scientific validity. The Board reviews "
            "unblinded safety summaries and, when formally triggered, limited efficacy summaries prepared by an "
            "independent statistical reporting center (ISRC) firewalled from sponsor operational staff with "
            "potential unblinding pathways. The DSMB may recommend continuation, modification, or termination "
            "of the study to the sponsor executive accountable for clinical development, whose role is to "
            "implement or formally document deferrals consistent with ethical obligations.",
            "Regulatory authorities may be informed of substantive DSMB recommendations and corresponding sponsor "
            "actions consistent with legal obligations, expedited safety reporting expectations, and clinical "
            "trial disclosure rules. The DSMB does not direct care of individual participants; treating "
            "physicians retain medical decision-making prerogatives consistent with local standard of care. "
            "This charter aligns with FDA guidance on Data Monitoring Committees and ICH E6(R2) expectations "
            "for independent review of accumulating safety data in trials presenting more than minimal risk.",
        ],
    )

    _h1(pdf, "2. Membership, independence, conflicts of interest")
    _dense_block(
        pdf,
        [
            "The voting membership includes three physician specialists: a gastroenterologist with inflammatory "
            "bowel disease expertise, an independent biostatistician member with randomized trial methodology "
            "experience, and a patient-safety oriented pharmacologist or epidemiologist (or equivalent training). "
            "An independent statistician performing analyses may attend closed sessions without voting "
            "privileges unless elevated as alternate member per succession rules. Sponsor representatives "
            "participate only in open sessions without access to treatment codes except when explicitly invited "
            "for logistical clarifications that do not reveal comparative results.",
            "Members complete confidentiality agreements and financial disclosure questionnaires annually. "
            "Material financial interests in sponsor equity, consulting arrangements exceeding de minimis "
            "thresholds, or scientific collaborations likely to impair objectivity disqualify participation. "
            "Management of conflicts follows a mitigation ladder: disclosure, recusal from deliberations touching "
            "conflicted domains, or member replacement if conflicts are pervasive.",
        ],
    )
    _h2(pdf, "2.1 Curriculum vitae maintenance and competency")
    _dense_block(
        pdf,
        [
            "Curricula vitae and Good Clinical Practice training certificates are collected at appointment and "
            "updated every two years or upon substantive change. Orientation includes protocol synopsis review, "
            "prior program safety narrative, and training on secure data room navigation with watermarking of "
            "downloadable files where permitted.",
        ],
    )

    _h1(pdf, "3. Responsibilities and scope of review")
    _bullets(
        pdf,
        [
            "Review unblinded safety tables: adverse events by preferred term, seriousness, severity, relationship, and exposure-adjusted incidence rates.",
            "Review deaths, serious infections, hepatic events meeting Hy's law vigilance rules, and adjudicated cardiovascular events.",
            "Monitor enrollment versus projected trajectory and major protocol deviations with safety implications.",
            "At triggered interim points, review conditional efficacy boundaries respecting alpha-spending rules.",
            "Evaluate external trial information or emerging epidemiology that alters context for observed signals.",
            "Approve meeting minutes and formal recommendations archived under access-controlled repositories.",
        ],
    )

    _h1(pdf, "4. Meeting schedule and ad hoc convening")
    _dense_block(
        pdf,
        [
            "Regular closed sessions occur approximately quarterly aligned with cumulative participant exposure "
            "milestones (e.g., every six months of study calendar contingent on accrual). Pre-planned interim "
            "analyses occur at approximately 50% and 75% information fractions for primary endpoint events "
            "under simulations updated as observed dropout deviates from planning assumptions.",
            "Ad hoc meetings convene within 72 hours for fatality clusters, unexpected serious infection "
            "patterns exceeding pre-specified thresholds, or regulatory agency requests. Meeting logistics use "
            "secure teleconferencing with dial-in controls; attendance logs record entry and exit times for "
            "non-public segments.",
        ],
    )

    _h1(pdf, "5. Operating procedures, quorum, and voting")
    _dense_block(
        pdf,
        [
            "Quorum requires at least two voting physician members and participation of the biostatistician "
            "member or documented designee with equivalent independence. Decisions default to consensus; if "
            "consensus cannot be reached after structured discussion, a formal vote is recorded with dissents "
            "documented as minority opinions without attribution in external communications.",
            "Minutes are drafted by independent support staff without reporting lines into clinical operations; "
            "minutes exclude participant identifiers and site-level attribution for rare events. Corrections "
            "follow controlled amendment with version history for audit inspection.",
        ],
    )

    _h1(pdf, "6. Data review process: open versus closed sessions")
    _dense_block(
        pdf,
        [
            "Open sessions may discuss high-level accrual, missing data summaries at arm-aggregated blinded "
            "levels, and logistical feasibility. Closed sessions receive ISRC-generated comparative displays "
            "with treatment labels accessible only to DSMB members and designated statisticians. Patient "
            "narratives for selected serious events may be pseudonymized; rare event denominators may be "
            "suppressed to reduce re-identification risk.",
            "Blinded sponsor medical monitors may propose medical queries or protocol clarifications in open "
            "session without learning comparative rates. Escalation pathways exist if DSMB requires sponsor "
            "confirmation of concomitant medication coding or endpoint ascertainment definitions.",
        ],
    )

    _h1(pdf, "7. Statistical monitoring plan: O'Brien-Fleming and Lan-DeMets spending")
    _dense_block(
        pdf,
        [
            "Efficacy futility and conditional power are assessed using information fraction based on the number "
            "of participants reaching primary endpoint evaluation milestones. Lan-DeMets alpha spending with "
            "O'Brien-Fleming analog boundaries preserves overall type I error for formal superiority testing; "
            "spending functions are implemented in validated statistical software with reproducible random seeds "
            "and tracked versions of simulation code.",
            "Safety monitoring uses repeated confidence sequence ideas only in exploratory capacity unless "
            "protocolized; primary regulatory conclusions rely on fixed protocols aligned with ICH E9(R1) "
            "estimand specifications. Crossing boundaries triggers DSMB recommendation categories: continue, "
            "continue with enhanced safety surveillance, pause enrollment pending investigation, or terminate "
            "randomization while allowing follow-up for ongoing participants under amended risk mitigation.",
        ],
    )

    _h1(pdf, "8. Stopping rules: efficacy, futility, and safety")
    _table(
        pdf,
        ["Category", "Illustrative trigger (protocol-defined)", "Typical DSMB action"],
        [
            (
                "Efficacy",
                "Conditional power >0.99 for primary endpoint with safety neutral",
                "Recommend sponsor consult regulators on early submission strategy; not an automatic stop.",
            ),
            (
                "Futility",
                "Conditional power <0.10 at interim with trend opposite hypothesized direction",
                "Consider enrollment pause or sample size revision if ethical to continue.",
            ),
            (
                "Safety",
                ">=3 adjudicated hepatic Hy's law cases related vs placebo",
                "Recommend termination or dose suspension pending external expert review.",
            ),
            (
                "Safety",
                "Serious infection rate excess with attributable mechanism plausibility",
                "Enhanced monitoring or risk mitigation amendment recommendations.",
            ),
        ],
        [32, 82, 68],
    )
    _dense_block(
        pdf,
        [
            "Exact numeric thresholds supersede illustrative examples if protocol amendments specify stricter "
            "values following emerging pharmacovigilance. DSMB may recommend unplanned pooled analyses across "
            "program studies when safety context requires larger denominators and human subject protections allow.",
        ],
    )

    _h1(pdf, "9. Communication procedures to sponsor, investigators, and regulators")
    _bullets(
        pdf,
        [
            "DSMB chair communicates recommendations via secure written transmittal to sponsor executive oversight within 24 hours of meeting conclusion.",
            "Sponsor distributes safety-critical DSMB communications to investigators as Dear Investigator letters after ethics review where required.",
            "Regulators receive expedited notifications per regional law when DSMB recommends substantive risk mitigation or study termination.",
            "Study participants are not directly informed of DSMB deliberations; general transparency occurs only through consent documents describing independent monitoring at a high level.",
        ],
    )

    _h1(pdf, "10. Confidentiality requirements and document retention")
    _dense_block(
        pdf,
        [
            "Members may not trade sponsor securities, publish interim results, or advise competitive programs on "
            "unblinded findings. Secure destruction or return of materials occurs at study conclusion except "
            "retained minutes and statistical exhibits archived for 25 years consistent with TMF expectations. "
            "Breaches confidentiality triggers contractual remedies and regulatory reporting if participant "
            "privacy is jeopardized.",
        ],
    )

    _h1(pdf, "11. Appendices")
    _h2(pdf, "Appendix A -- Recommendation letter templates")
    _dense_block(
        pdf,
        [
            "Templates include: (A) no action required beyond ongoing surveillance; (B) enhanced hepatic monitoring "
            "with protocol amendment suggestion; (C) enrollment pause pending data cleaning and cause "
            "ascertainment; (D) termination of one dose arm; (E) full study stop with follow-up continuation.",
            "Each template documents date, meeting identifier, attendance, datasets reviewed, statistical "
            "displays version, and explicit rationale referencing Charter sections.",
        ],
    )
    _h2(pdf, "Appendix B -- Interim statistical analysis plan outline")
    _dense_block(
        pdf,
        [
            "Interim SAP specifies datasets locked for interim read, estimand alignment for intercurrent events, "
            "multiple imputation sensitivity for missing PRO, adaptive decisions if enrollment paused, and "
            "simulation code repositories with QC validation memos signed by independent biostatistician.",
        ],
    )

    _h1(pdf, "12. Supplemental operational policies")
    _h2(pdf, "12.1 Emergency medical management and investigator autonomy")
    _dense_block(
        pdf,
        [
            "The DSMB charter does not preempt urgent medical management. Treating physicians may initiate rescue "
            "therapy, hospitalization, or procedures essential for participant welfare without awaiting DSMB "
            "deliberation. Subsequent unblinding for care may occur through emergency procedures consistent with "
            "protocol; data analyses treat such events per prespecified estimands. DSMB reviews aggregated impacts "
            "of emergency unblinding rates as integrity indicators.",
        ],
    )
    _h2(pdf, "12.2 COVID-19/public health disruption addendum hooks")
    _dense_block(
        pdf,
        [
            "Pandemic or regional public health emergencies may affect visit completion, endoscopy access, and "
            "central laboratory throughput. Contingency displays stratify safety events by disruption windows "
            "declared by sponsor governance. DSMB may recommend pragmatic protocol adaptations (telehealth, "
            "local labs with equivalency documentation) with ethics concurrence; statistical implications are "
            "simulated before implementation when time permits.",
        ],
    )
    _h2(pdf, "12.3 Diversity, equity, and inclusion monitoring")
    _dense_block(
        pdf,
        [
            "Recruitment dashboards summarize enrollment by sex, race, ethnicity, and age bands relative to "
            "epidemiology references for Crohn's disease. Underrepresentation triggers community engagement "
            "rescoping rather than coercion. DSMB reviews blinded disposition of discontinuations by demographic "
            "categories to detect differential loss patterns suggestive of access barriers.",
        ],
    )
    _h2(pdf, "12.4 Cybersecurity incident reporting into safety oversight")
    _dense_block(
        pdf,
        [
            "Serious data integrity incidents affecting safety ascertainment or randomization integrity escalate "
            "to sponsor quality and to DSMB if participant risk is plausible. Forensic conclusions accompany "
            "corrective action plans prior to restarting enrollment after pauses.",
        ],
    )

    pdf.output(path)
    return fn


# ---------------------------------------------------------------------------
# Document 4 -- Clinical Operations Manual (~20 pages)
# ---------------------------------------------------------------------------


def build_clinical_operations_manual() -> str:
    fn = "Clinical_Operations_Manual_v3.pdf"
    path = _out_pdf(fn)
    pdf = ClinicalPDF("ClinOps Manual v3")

    _title_page(
        pdf,
        "Clinical Operations Manual",
        "Study ZYN-301-CD-301 -- Version 3.0",
        [
            "Sponsor Operations: NovaThera Global Clinical Development",
            "Applies to investigative sites, monitors, and functional vendors supporting execution.",
        ],
    )
    _toc(
        pdf,
        [
            "Study overview and organization",
            "Site selection and qualification",
            "Site initiation and training",
            "Monitoring plan and risk-based oversight",
            "Data management, coding, and query SLAs",
            "Safety reporting workflows and timelines",
            "Investigational medicinal product supply chain",
            "Essential documents, ISF, and TMF governance",
            "Quality management: deviations, CAPA, and inspection readiness",
        ],
    )

    _h1(pdf, "1. Study overview and organization")
    _dense_block(
        pdf,
        [
            "ZYN-301-CD-301 is executed through sponsor clinical operations, a contracted CRO alliance, central "
            "vendors for laboratory, imaging, EDC/IRT, and specialized medical monitoring. Country lead "
            "managers oversee start-up regulatory packets; regional monitors manage day-to-day site execution. "
            "Governance forums include operational risk reviews, enrollment prediction workshops, and "
            "cross-functional safety triage incorporating pharmacovigilance.",
            "Roles and responsibilities matrices (RACI) clarify accountable owners for monitoring reports, "
            "protocol deviations, supply releases, and database updates. Study team communications use "
            "controlled distribution lists; substantive decisions are documented in study team meeting minutes "
            "stored in the TMF within SLA-defined timelines.",
        ],
    )

    _h1(pdf, "2. Site selection and qualification")
    _h2(pdf, "2.1 Feasibility and capacity assessment")
    _dense_block(
        pdf,
        [
            "Feasibility questionnaires quantify IBD patient volumes, prior trial experience, endoscopy access "
            "within visit windows, pharmacy capabilities for blinded IMP, and historical data quality metrics. "
            "Central feasibility analysts score responses using weighted criteria calibrated to protocol intensity.",
            "Competing trials, staffing turnover, and holiday blackout periods inform realistic enrollment curves. "
            "Geographic diversity targets balance regulatory representation without fragmenting supply logistics.",
        ],
    )
    _h2(pdf, "2.2 Qualification visits and essential document collection")
    _dense_block(
        pdf,
        [
            "Qualification visits verify GCP training records, delegation of authority logs templates, "
            "Archival procedures for source documents (paper versus electronic health record exports), and "
            "delegated ethics submissions. Pharmacy walkthroughs confirm temperature mapping, backup power, "
            "and IMP receipt workflows. Photos of storage areas may be retained with site permission for TMF.",
        ],
    )

    _h1(pdf, "3. Site initiation")
    _h2(pdf, "3.1 Site initiation visit (SIV) objectives and checklist")
    _bullets(
        pdf,
        [
            "Confirm regulatory approvals (IRB/IEC, MoH where applicable) and insurance certificates are current.",
            "Review protocol procedures, visit schedule, eligibility, prohibited medications, and safety reporting windows.",
            "Demonstrate EDC entry, query workflows, ePRO deployment, and IRT kit ordering simulations.",
            "Review IMP accountability logs, temperature logs, and shipment discrepancy handling.",
            "Establish monitoring visit communications, escalation trees, and confidentiality expectations.",
        ],
    )
    _h2(pdf, "3.2 Training and competency documentation")
    _dense_block(
        pdf,
        [
            "All site staff performing protocol procedures sign attendance logs and complete protocol-specific "
            "assessments. Re-training occurs within 30 days of protocol amendments impacting procedures they "
            "perform. Subinvestigator additions require updated FDA Form 1572 or regional equivalents before "
            "delegated tasks commence.",
        ],
    )

    _h1(pdf, "4. Monitoring plan: risk-based and centralized")
    _h2(pdf, "4.1 Risk-based monitoring strategy")
    _dense_block(
        pdf,
        [
            "Critical data and processes (CDP) include randomization, informed consent, eligibility, primary "
            "endpoint components, safety labs, SAE reporting, and IMP accountability. Risk scores combine "
            "intrinsic protocol factors (invasive procedures, immunomodulation) with site historic compliance "
            "signals. Targeted monitoring focuses SDV on CDPs while off-target workflows rely on statistical "
            "monitoring triggers.",
        ],
    )
    _h2(pdf, "4.2 Central monitoring metrics and KRIs")
    _table(
        pdf,
        ["Key risk indicator (KRI)", "Definition", "Trigger example", "Action"],
        [
            ("Enrollment velocity vs forecast", "Ratio of randomized to predicted", "<70% for 2 months", "Root cause workshop; resource reallocation"),
            ("Query aging", "Days open for critical variables", ">21 days median", "Escalate to country lead"),
            ("Protocol deviation rate", "Major deviations per randomized pt", ">0.25", "Focused on-site visit"),
            ("SAE timeliness", "% SAEs reported within 24 h", "<95%", "Training remediation"),
        ],
        [44, 38, 40, 60],
        fontsize=7,
    )
    _h2(pdf, "4.3 On-site monitoring cadence and remote visit hybrids")
    _dense_block(
        pdf,
        [
            "High-performing sites with clean central signals may transition to remote visits alternating with "
            "on-site visits every second cycle. Remote reviews use validated screen-share protocols with "
            "attestation signatures. On-site visits include traceability drills for primary endpoint source "
            "documents and temperature excursion investigations.",
        ],
    )

    _h1(pdf, "5. Data management plan highlights")
    _h2(pdf, "5.1 UAT, access control, and edit checks")
    _dense_block(
        pdf,
        [
            "EDC user acceptance testing validates edit checks, skip logic, linking of repeating instruments, and "
            "laboratory imports. Role permissions segregate site entry from medical monitoring queries and "
            "sponsor medical sign-offs. Audit trails capture old and new values, user, timestamp, and reason codes.",
        ],
    )
    _h2(pdf, "5.2 Coding with MedDRA and WHODrug")
    _dense_block(
        pdf,
        [
            "Adverse events are coded to MedDRA lowest level term with upward hierarchical mapping to PT and "
            "SOC; versioning is locked per reporting period with mid-study dictionary upgrades following "
            "controlled remapping procedures. Concomitant medications map to WHODrug Global B3 format where "
            "available; herbal coded using additional vendor standards with manual review flags.",
        ],
    )
    _h2(pdf, "5.3 Query SLAs and medical review")
    _table(
        pdf,
        ["Query priority", "Target site response", "Monitor escalation"],
        [
            ("Critical (safety/eligibility)", "48 hours", "Immediate phone escalation + medical monitor"),
            ("Primary endpoint linked", "7 calendar days", "Email + next visit focus"),
            ("Administrative", "14 calendar days", "Standard tracking dashboards"),
        ],
        [52, 58, 72],
    )

    _h1(pdf, "6. Safety reporting procedures")
    _dense_block(
        pdf,
        [
            "Investigators assess seriousness, causality, and expectedness against reference safety information. "
            "SAE workflows route through 24/7 pharmacovigilance intake with duplicate detection against sponsor "
            "global database. Line listings reconcile SAE narratives with hospital discharge summaries uploaded "
            "to safety portals when permitted by privacy law.",
            "Expedited reporting timelines: investigator-to-sponsor within 24 hours; sponsor regulatory "
            "expedited reports per regional calendars; follow-up reports consolidate new significant information. "
            "Aggregate safety reviews before DSMB meetings use standardized displays by SMQ and Standardized "
            "MedDRA Queries tuned for infection and hepatic disorders.",
        ],
    )

    _h1(pdf, "7. Investigational product management")
    _bullets(
        pdf,
        [
            "Receipt: verify shipment content versus packing list; log batch, expiry, quantity; quarantine until release.",
            "Storage: 15-25\u00bC unless label specifies alternate range; log daily min/max temperatures; alarm testing quarterly.",
            "Dispensing: blinded kit assignment via IRT; double-check by pharmacist per SOP.",
            "Accountability: tablet counts reconciled each visit; unexplained variance >2% triggers investigation.",
            "Returns/destruction: witnessed destruction logs; certificates filed in ISF and TMF pharmacy binder.",
        ],
    )

    _h1(pdf, "8. Essential document management")
    _dense_block(
        pdf,
        [
            "Investigator site files mirror TMF index structure with local substitutions for regulated forms. "
            "Certified copies of source documents accompany remote monitoring where originals cannot leave site; "
            "attestations reference imaging modalities and certification of equivalence. TMF completeness "
            "metrics track milestone achievements (first patient in, last patient out, database lock).",
        ],
    )

    _h1(pdf, "9. Quality management: CAPA, deviations, audits")
    _h2(pdf, "9.1 Protocol deviations and categorization")
    _dense_block(
        pdf,
        [
            "Major deviations include enrollment of ineligible patients, missed SAE reporting windows, IMP "
            "temperature excursions without assessment, and unblinding without documented emergency justification. "
            "CAPA plans document root cause, corrective actions, preventive actions, owners, and due dates; "
            "effectiveness checks occur within 90 days of closure.",
        ],
    )
    _h2(pdf, "9.2 Inspection readiness drills")
    _dense_block(
        pdf,
        [
            "Mock audits trace selected participants from consent to endpoint ascertainment; deficiencies map "
            "to remediation trackers. Subject matter experts rehearse responses regarding statistical analysis, "
            "data integrity, and pharmacovigilance governance using question banks updated after agency "
            "inspection observation publications.",
        ],
    )

    _h1(pdf, "10. Reference laboratory normal ranges (adult serum, exemplar)")
    _table(
        pdf,
        ["Analyte", "ULN example", "LLN example", "Note"],
        [
            ("ALT (U/L)", "41 (M), 33 (F)", "NA", "Site-specific: central lab SDS controls"),
            ("AST (U/L)", "40 (M), 32 (F)", "NA", ""),
            ("Total bilirubin (mg/dL)", "1.2", "0.2", "Gilbert's exclusion per protocol"),
            ("eGFR (mL/min/1.73m^2)", "NA", "60", "CKD-EPI screening threshold"),
            ("hs-CRP (mg/L)", "8.0 high", "<0.5", "Inflammation contextual interpretation"),
        ],
        [40, 38, 38, 66],
        fontsize=7,
    )

    _h1(pdf, "11. Extended references for cross-functional interfaces")
    _h2(pdf, "11.1 Medical monitoring and endpoint uncertainty adjudication")
    _dense_block(
        pdf,
        [
            "Medical monitors perform daily or triweekly review queues for eligibility uncertainties, dosing "
            "decisions near hold thresholds, and concomitant medication classification impacting exclusion criteria. "
            "Escalations route to therapeutic area physicians with documented decision rationales stored in the "
            "TMF. Endpoint adjudication queries integrate with imaging providers and local pathology for biopsy "
            "confirmation when granulomas or alternative diagnoses are suspected.",
        ],
    )
    _h2(pdf, "11.2 Translation, cultural adaptation, and local ethics variations")
    _dense_block(
        pdf,
        [
            "Translated informed consent documents undergo forward-backward translation with reconciliation memos. "
            "Sites in jurisdictions requiring witness signatures or physician disclosure of financial conflicts "
            "follow local templates appended to universal protocol synopses. Operational manuals document which "
            "procedures defer to local law versus central sponsor standardization.",
        ],
    )
    _h2(pdf, "11.3 Technology change control for EDC/IRT releases")
    _dense_block(
        pdf,
        [
            "Validated releases follow documented UAT sign-off, migration plans, regression testing scripts, and "
            "back-out strategies. Emergency fixes for critical safety capture defects undergo expedited risk "
            "assessment with notification to quality assurance and within one business day to impacted sites when "
            "data integrity is implicated.",
        ],
    )

    pdf.output(path)
    return fn


# ---------------------------------------------------------------------------
# Document 5 -- Regulatory Strategy (~18 pages)
# ---------------------------------------------------------------------------


def build_regulatory_strategy() -> str:
    fn = "Regulatory_Strategy_Document_Zynvara.pdf"
    path = _out_pdf(fn)
    pdf = ClinicalPDF("Reg Strategy Zynvara")

    _title_page(
        pdf,
        "Global Regulatory Strategy Document",
        "Zynvara(TM) (ZYN-301) -- Moderate-to-Severe Crohn's Disease",
        [
            "Program: ZYN-301-CD (Phases IIb-III and registration)",
            "Sponsor: NovaThera Biosciences, Inc.",
            "Classification: New molecular entity, oral small molecule.",
        ],
    )
    _toc(
        pdf,
        [
            "Product overview and development history",
            "Regulatory landscape assessment (FDA, EMA, PMDA)",
            "United States FDA strategy",
            "European Union centralized procedure strategy",
            "Japan PMDA strategy",
            "Labeling and risk communication strategy",
            "Post-marketing commitments and pharmacovigilance",
            "Timeline, milestones, and launch sequencing",
            "Regulatory risk assessment and mitigation",
        ],
    )

    _h1(pdf, "1. Product overview and development history")
    _dense_block(
        pdf,
        [
            "ZYN-301 is developed as an oral, gut-focused immunomodulator addressing residual unmet need among "
            "patients failing or intolerant to advanced therapies. Nonclinical packages, CMC scale-up, and "
            "clinical pharmacology bridging position the program for global filings contingent on confirmatory "
            "Phase III outcomes and acceptable long-term safety accumulation.",
            "Development milestones include IND clearance (US), ethics approvals across 24 countries, rolling "
            "end-of-Phase II meetings, alignment on primary estimands with FDA and EMA scientific advice, and "
            "pre-NDA/MAA readiness reviews integrating quality and safety surveillance datasets.",
        ],
    )

    _h1(pdf, "2. Regulatory landscape assessment")
    _h2(pdf, "2.1 FDA expectations for inflammatory bowel disease trials")
    _dense_block(
        pdf,
        [
            "FDA reviews in IBD emphasize objective inflammation change (endoscopy) paired with patient-centered "
            "clinical benefit, corticosteroid-sparing, and durable maintenance outcomes depending on claim "
            "strategy. Endpoints should align with published guidance and be supported by prespecified "
            "multiplicity control, sensitivity analyses, and missing data plans consistent with ICH E9(R1).",
        ],
    )
    _h2(pdf, "2.2 EMA and PRIME-like acceleration considerations")
    _dense_block(
        pdf,
        [
            "EMA scientific advice seeks confirmatory evidence on comparative benefit versus available therapies "
            "and on long-term immunosuppression safety. Pediatric investigation plans (PIP) waivers or deferrals "
            "may be sought based on adult- pediatric bridging rationale and juvenile toxicity packages.",
        ],
    )
    _h2(pdf, "2.3 PMDA consultation and Asian bridging")
    _dense_block(
        pdf,
        [
            "PMDA early dialogues clarify ethnic factor evaluations; bridging may leverage global pivotal data "
            "with augmented Japanese subgroup sizes if variability in metabolism or response is hypothesized. "
            "Translation of PRO instruments follows MHLW conventions; domestic clinical sites are pre-qualified.",
        ],
    )

    _h1(pdf, "3. United States FDA strategy")
    _dense_block(
        pdf,
        [
            "IND maintenance includes annual reports, protocol amendments, developmental safety update reports, "
            "and electronic submissions via gateway. Breakthrough Therapy Designation (BTD) eligibility review "
            "depends on preliminary clinical evidence indicating substantial improvement over available therapy on "
            "serious outcomes; sponsor milestones include compiling independent replication of endoscopic benefit "
            "and robust hepatic safety margins prior to requesting BTD.",
            "Pre-NDA meeting objectives seek alignment on filing modular structure, datasets (SDTM/ADaM), "
            "clinical pharmacology labeling expectations, and whether MRI substudy constitutes confirmatory "
            "evidence or supportive information. Priority Review eligibility may be pursued if the program "
            "addresses unmet need and files comprehensive outcomes; review clock assumptions integrate into "
            "commercial planning scenarios.",
            "NDA submission adopts eCTD M2-M5 organization with integrated summaries reflecting cross-discipline "
            "evaluation; proposed labeling negotiations anticipate boxed warnings only if reproducible serious "
            "risks emerge; Risk Evaluation and Mitigation Strategies are contingency-planned but not assumed.",
        ],
    )

    _h1(pdf, "4. European Union centralized procedure strategy")
    _dense_block(
        pdf,
        [
            "The centralized procedure targets a single CHMP opinion and Commission decision applicable across EU/ "
            "EEA states. Rapporteur/co-rapporteur assignment influences review focus; briefing packages highlight "
            "CMC consistency, environmental risk assessment, and pharmacovigilance system master file references.",
            "Accelerated assessment (150 days) may be requested if serious unmet need criteria are met; routine "
            "210-day reviews require clock-stop management for outstanding benefit-risk questions. Labeling "
            "negotiations include SmPC section 4.8 adverse reaction tables harmonized with MedDRA versions locked "
            "for periodic safety update reporting.",
            "REMS-like EU risk minimization measures employ additional monitoring or educational materials if "
            "Hepatic monitoring or infection risks warrant harmonized EU-wide communications rather than "
            "national variations.",
        ],
    )

    _h1(pdf, "5. Japan PMDA strategy")
    _dense_block(
        pdf,
        [
            "Consultation meetings define necessity of local bridging studies relative to ICH M5 acceptance of "
            "foreign data. If bridging proceeds, pharmacokinetic comparability in Japanese participants may "
            "suffice absent efficacy replication under precedent-dependent conditions; alternatively, a "
            "contribution analysis from prespecified subgroup within global trials may support filing.",
        ],
    )

    _h1(pdf, "6. Labeling strategy (initial draft positioning)")
    _h2(pdf, "6.1 Proposed indication and limitations")
    _bullets(
        pdf,
        [
            "Indication (working): treatment of adults with moderate-to-severe active Crohn's disease who have inadequate response, loss of response, or intolerance to conventional or biologic therapy.",
            "Limitations: not studied in fistulizing disease as sole phenotype; not established in pediatric patients.",
        ],
    )
    _h2(pdf, "6.2 Warnings and precautions (illustrative drafting notes)")
    _bullets(
        pdf,
        [
            "Hepatotoxicity: monitor ALT/AST per schedule; consider interruption for persistent elevations.",
            "Serious infections: consider tuberculosis screening; avoid live vaccines during therapy per guidance.",
            "Embryo-fetal toxicity: pregnancy testing and contraception requirements derived from nonclinical data.",
        ],
    )
    _h2(pdf, "6.3 Dosing and contraindications (illustrative)")
    _dense_block(
        pdf,
        [
            "Initial dosing anticipates 45 mg or 90 mg QD selection informed by benefit-risk and hepatic monitoring "
            "practicalities; final label reflects registrational trial arms. Contraindications may include "
            "concomitant strong CYP3A4 inhibitors if clinically substantial interactions are observed; draft "
            "language defers to DDI studies and post-hoc exposure-safety analyses.",
        ],
    )

    _h1(pdf, "7. Post-marketing commitments")
    _dense_block(
        pdf,
        [
            "Potential pharmacovigilance obligations include periodic safety update reports transitioning to "
            "periodic benefit-risk evaluation reports under EU regulation, US periodic FDA reporting, and "
            "Japanese PMDA routine safety updates. Post-marketing requirement (PMR) studies may include a "
            "pregnancy exposure registry, long-term malignancy observational study, or hepatic outcomes registry "
            "if numerical imbalances emerge in Phase III.",
            "REMS programs remain contingency-only; should REMS be required, elements would include prescriber "
            "education on hepatic monitoring and patient medication guides harmonized across modalities.",
        ],
    )

    _h1(pdf, "8. Timeline, milestones, and launch sequencing")
    _table(
        pdf,
        ["Milestone", "Target quarter", "Dependency"],
        [
            ("Phase III DBL / lock", "2027Q4", "Site data quality, imaging reads completion"),
            ("US NDA submission", "2028Q2", "CMC validation batches release"),
            ("EU MAA submission", "2028Q2", "RSI and environmental risk final"),
            ("Japan J-NDA filing", "2028Q4", "Bridging agreement"),
            ("First approval (US priority review scenario)", "2029Q1", "No major review issues"),
            ("EU Commission decision (+/-)", "2029Q3", "CHMP clock management"),
        ],
        [58, 38, 86],
    )

    _h1(pdf, "9. Regulatory risk assessment and mitigation")
    _table(
        pdf,
        ["Risk", "Impact", "Mitigation"],
        [
            ("Primary endpoint miss in one region", "Labeling restriction", "Pre-specified pooling and subgroup plans; independent imaging QC"),
            ("Hepatic signal expansion", "Labeling warnings; REMS risk", "Augmented monitoring; DSMB oversight; hepatology adjudication"),
            ("CMC inspection findings", "Approval delay", "Readiness audits; batch record excellence program"),
            ("Pediatric PIP timing", "EU approval gating", "Early EMA PIP strategy; deferral justification package"),
        ],
        [48, 45, 89],
        fontsize=8,
    )
    _dense_block(
        pdf,
        [
            "Risk reviews occur monthly during late-stage development with cross-functional signatories. Emerging "
            "post-marketing analog class concerns from competitors may trigger labeling precaution anticipations "
            "even before definitive ZYN-301-specific evidence; regulatory affairs maintains horizon scanning memos "
            "linked to benefit-risk update cycles.",
        ],
    )

    _h1(pdf, "10. Global labeling harmonization workshops and mock PMLR")
    _dense_block(
        pdf,
        [
            "Cross-functional labeling teams conduct iterative mock Prescribing Information/Mock SmPC workshops "
            "integrating safety narratives, clinical pharmacology, and CMC post-approval change management "
            "commitments. Patient education materials undergo health literacy testing in priority launch markets "
            "where required by authorities.",
        ],
    )

    _h1(pdf, "11. Health technology assessment readiness (ex-US access)")
    _dense_block(
        pdf,
        [
            "Beyond regulatory approval, evidence generation plans anticipate payer evidence needs: comparative "
            "claims may require network meta-analyses or matching-adjusted indirect comparisons versus SOC and "
            "advanced therapies. Budget impact models incorporate dosing, discontinuation patterns from trials, "
            "and safety-related resource use assumptions validated with health economist advisors.",
        ],
    )

    pdf.output(path)
    return fn


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    _ensure_volume()

    builders = [
        build_protocol_zyn301,
        build_investigators_brochure,
        build_dsmb_charter,
        build_clinical_operations_manual,
        build_regulatory_strategy,
    ]

    for builder in builders:
        builder()


main()