# Databricks notebook source

"""
Commercial Pharma Workshop -- Reproducible Synthetic Structured Data

This Databricks notebook generates realistic synthetic Delta tables for a
Commercial Pharma workshop track. Data is written to Unity Catalog for
downstream Genie Space SQL exploration. All stochastic processes use SEED=42
so results are reproducible across runs.

Tables produced in Unity Catalog (exactly five):
  ``product_portfolio``, ``sales_transactions``, ``hcp_engagements``,
  ``market_access``, ``sales_targets``.

Supporting dimensions (``sales_reps``, ``hcp_master``) are built in memory for
referential integrity but are not saved as tables unless you extend this script.

Run on a cluster with Spark and PySpark available. Requires network for ``pip install``.
"""

import subprocess

subprocess.check_call(["pip", "install", "faker", "holidays"])

import warnings
from datetime import date, datetime, timedelta

import holidays
import numpy as np
import pandas as pd
from faker import Faker
from pyspark.sql import SparkSession

warnings.filterwarnings("ignore", category=FutureWarning)

# --- Configuration ---
SEED = 42
dbutils.widgets.text("catalog", "pharma_workshop", "Catalog Name")
CATALOG = dbutils.widgets.get("catalog").strip()
assert CATALOG, "ERROR: Please provide a catalog name in the widget above before running."
SCHEMA = "wsp_commercial"

RNG = np.random.default_rng(SEED)
FAKE = Faker("en_US")
FAKE.seed_instance(SEED)

THERAPEUTIC_AREAS = [
    "Oncology",
    "Cardiology",
    "Neurology",
    "Immunology",
    "Respiratory",
    "Endocrinology",
]
THERAPEUTIC_AREA_WEIGHTS = np.array([0.30, 0.25, 0.12, 0.10, 0.12, 0.11])
THERAPEUTIC_AREA_WEIGHTS = THERAPEUTIC_AREA_WEIGHTS / THERAPEUTIC_AREA_WEIGHTS.sum()

# Baseline log-normal params for WAC (scaled & clipped per row)
WAC_MU_BASE = 6.2
WAC_SIGMA = 0.55
TA_WAC_MULTIPLIER = {
    "Oncology": 2.8,
    "Cardiology": 1.35,
    "Neurology": 1.15,
    "Immunology": 1.25,
    "Respiratory": 1.05,
    "Endocrinology": 1.1,
}

DOSAGE_FORMS = ["Tablet", "Injectable", "Capsule", "Infusion", "Inhaler"]
STATUS_CHOICES = ["Active", "Discontinued", "Pipeline"]
STATUS_WEIGHTS = np.array([0.85, 0.10, 0.05])

TERRITORIES = [
    "Northeast",
    "Southeast",
    "Midwest",
    "West",
    "Southwest",
    "Mid-Atlantic",
    "Pacific Northwest",
    "Great Lakes",
]
TERRITORY_TARGET_MULTIPLIER = {
    "Northeast": 1.28,
    "Southeast": 1.18,
    "Midwest": 1.0,
    "West": 1.22,
    "Southwest": 0.92,
    "Mid-Atlantic": 1.12,
    "Pacific Northwest": 0.88,
    "Great Lakes": 1.08,
}

CHANNELS = ["Retail Pharmacy", "Specialty Pharmacy", "Hospital", "Mail Order"]
CHANNEL_WEIGHTS = np.array([0.40, 0.30, 0.20, 0.10])
# Net / gross ratio ranges by channel (inclusive sampling)
CHANNEL_NET_RATIOS = {
    "Retail Pharmacy": (0.60, 0.74),
    "Specialty Pharmacy": (0.74, 0.86),
    "Hospital": (0.82, 0.92),
    "Mail Order": (0.87, 0.95),
}

ENGAGEMENT_TYPES = [
    "Detail Visit",
    "Speaker Program",
    "Conference",
    "Sample Drop",
    "Virtual Meeting",
]
ENGAGEMENT_TYPE_WEIGHTS = np.array([0.35, 0.15, 0.20, 0.20, 0.10])
ENGAGEMENT_DURATION_BOUNDS = {
    "Detail Visit": (15, 45),
    "Speaker Program": (90, 240),
    "Conference": (60, 480),
    "Sample Drop": (5, 30),
    "Virtual Meeting": (30, 90),
}

OUTCOMES = ["Positive", "Neutral", "Follow-up Required", "No Interest"]
OUTCOME_WEIGHTS = np.array([0.48, 0.26, 0.16, 0.10])

PAYERS = [
    "Aetna",
    "UnitedHealthcare",
    "Cigna",
    "Blue Cross Blue Shield",
    "Humana",
    "Kaiser Permanente",
    "Anthem",
    "Centene",
    "Molina",
    "CVS Caremark",
    "Independence Blue Cross",
    "Health Care Service Corporation",
    "Oscar Health",
    "Medicaid (State Plan)",
    "Tricare",
    "CareFirst",
    "EmblemHealth",
    "Highmark",
    "Elevance Health",
    "Regence",
]

FORMULARY_STATUSES = [
    "Preferred",
    "Non-Preferred",
    "Specialty Tier",
    "Not Listed",
    "Prior Auth Required",
]
FORMULARY_STATUS_WEIGHTS = np.array([0.30, 0.25, 0.20, 0.15, 0.10])

HCP_SPECIALTIES = [
    "Oncologist",
    "Cardiologist",
    "Neurologist",
    "Pulmonologist",
    "Endocrinologist",
    "Rheumatologist",
    "Dermatologist",
    "Primary Care Physician",
    "Gastroenterologist",
    "Nephrologist",
    "Infectious Disease Specialist",
]


def _clip_wac(raw: np.ndarray) -> np.ndarray:
    return np.clip(np.round(raw, 2), 50.0, 15000.0)


def build_product_portfolio(n: int = 50) -> pd.DataFrame:
    """Synthetic pharma product master (50 rows)."""
    brand_names = [
        "Zynvara",
        "Liprenol",
        "Cardivex",
        "Oncolyze",
        "Neurexin",
        "Respilux",
        "Immunex",
        "Diatrol",
        "Hemofix",
        "Arthreze",
        "Pravacoril",
        "Metformex",
        "Glucostra",
        "Insultra",
        "Venouset",
        "Pulmodyn",
        "Asbestinib",
        "Keratora",
        "Nucelyx",
        "Renodyl",
        "Thyrovex",
        "Ceftranex",
        "Ostevance",
        "Levotrel",
        "Fibroneo",
        "Amlocrest",
        "Solvestat",
        "Lunarexa",
        "Epirexa",
        "Ventristat",
        "Myelivax",
        "Prostagen",
        "Dexilantrix",
        "Vasorexin",
        "Bradyvate",
        "Adrenolex",
        "Cortivast",
        "Neuropaxil",
        "Fibrolec",
        "Coagulix",
        "Angiotrel",
        "Broncholex",
        "Immunostat",
        "Dermalexin",
        "Pancrolin",
        "Hepatrex",
        "Nephrovil",
        "Somatrel",
        "Erythrexin",
        "Lymphostat",
    ]
    generic_names = [
        "atorvastatin",
        "lisinopril",
        "metformin",
        "trastuzumab",
        "osimertinib",
        "etanercept",
        "adalimumab",
        "sitagliptin",
        "apixaban",
        "rivaroxaban",
        "empagliflozin",
        "semaglutide",
        "dupilumab",
        "pembrolizumab",
        "nivolumab",
        "ustekinumab",
        "levothyroxine",
        "amlodipine",
        "omeprazole",
        "gabapentin",
        "sertraline",
        "pantoprazole",
        "meloxicam",
        "prednisone",
        "clopidogrel",
        "carvedilol",
        "losartan",
        "hydrochlorothiazide",
        "spironolactone",
        "insulin glargine",
        "tirzepatide",
        "filgrastim",
        "trastuzumab deruxtecan",
        "bevacizumab",
        "trastuzumab emtansine",
        "rituximab",
        "infliximab",
        "vedolizumab",
        "secukinumab",
        "ixekizumab",
        "guselkumab",
        "risankizumab",
        "upadacitinib",
        "tofacitinib",
        "baricitinib",
        "acalabrutinib",
        "zanubrutinib",
        "ibrutinib",
        "venetoclax",
        "ruxolitinib",
    ]
    assert len(brand_names) == n and len(generic_names) == n

    tas = RNG.choice(THERAPEUTIC_AREAS, size=n, p=THERAPEUTIC_AREA_WEIGHTS)
    base = RNG.lognormal(WAC_MU_BASE, WAC_SIGMA, size=n)
    mult = np.array([TA_WAC_MULTIPLIER[t] for t in tas])
    wac = _clip_wac(base * mult)

    rows = []
    for i in range(n):
        pid = f"PRD-{i + 1:03d}"
        lanch = date(2015, 1, 1) + timedelta(days=int(RNG.integers(0, (date(2025, 12, 31) - date(2015, 1, 1)).days)))
        ndc_a = int(RNG.integers(10000, 99999))
        ndc_b = int(RNG.integers(1000, 9999))
        ndc_c = int(RNG.integers(10, 99))
        ndc = f"{ndc_a:05d}-{ndc_b:04d}-{ndc_c:02d}"
        dosage = str(RNG.choice(DOSAGE_FORMS))
        status = str(RNG.choice(STATUS_CHOICES, p=STATUS_WEIGHTS))
        rows.append(
            {
                "product_id": pid,
                "brand_name": brand_names[i],
                "generic_name": generic_names[i],
                "therapeutic_area": tas[i],
                "ndc_code": ndc,
                "launch_date": lanch,
                "wac_price": float(wac[i]),
                "dosage_form": dosage,
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def build_sales_reps(n: int = 150) -> pd.DataFrame:
    """Assign each rep a home territory (balances coverage across regions)."""
    rep_ids = [f"REP-{i:03d}" for i in range(1, n + 1)]
    terr_idx = np.arange(n) % len(TERRITORIES)
    territories = [TERRITORIES[i] for i in terr_idx]
    # Small shuffle per territory block for realism while keeping even spread
    order = RNG.permutation(n)
    return pd.DataFrame(
        {"sales_rep_id": [rep_ids[i] for i in order], "territory": [territories[i] for i in order]}
    )


def build_hcp_master(n: int = 2000) -> pd.DataFrame:
    """Synthetic HCP dimension (implied FK for engagements & sales)."""
    rows = []
    for i in range(1, n + 1):
        spec = str(RNG.choice(HCP_SPECIALTIES))
        rows.append(
            {
                "hcp_id": f"HCP-{i:04d}",
                "hcp_name": f"Dr. {FAKE.name()}",
                "hcp_specialty": spec,
                "primary_territory": str(RNG.choice(TERRITORIES)),
            }
        )
    return pd.DataFrame(rows)


def sample_transaction_dates(n: int, start: date, end: date) -> np.ndarray:
    """Last-6-months calendar with weekday/weekend and US holiday weighting."""
    us_holidays = holidays.US(years=range(start.year, end.year + 1))
    days = []
    weights = []
    d = start
    while d <= end:
        days.append(d)
        if d in us_holidays:
            w = 0.12
        elif d.weekday() >= 5:
            w = 0.38
        else:
            w = 1.0
        weights.append(w)
        d += timedelta(days=1)
    w = np.array(weights, dtype=float)
    w /= w.sum()
    idx = RNG.choice(len(days), size=n, p=w)
    return np.array([days[i] for i in idx], dtype="object")


def date_to_quarter_str(d: date) -> str:
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"


def build_sales_transactions(
    portfolio: pd.DataFrame,
    reps: pd.DataFrame,
    n: int = 25_000,
) -> pd.DataFrame:
    """Territory-level sales with referential integrity to products and reps."""
    wac_by_pid = portfolio.set_index("product_id")["wac_price"].to_dict()
    pids = portfolio["product_id"].tolist()
    ranks = np.arange(1, len(pids) + 1, dtype=float)
    product_weights = 1.0 / np.power(ranks, 0.85)
    product_weights /= product_weights.sum()

    end_dt = datetime.now().date()
    start_dt = end_dt - timedelta(days=183)

    txn_dates = sample_transaction_dates(n, start_dt, end_dt)

    rows = []
    for i in range(n):
        pid = str(RNG.choice(pids, p=product_weights))
        rep_row = reps.iloc[int(RNG.integers(0, len(reps)))]
        sales_rep_id = rep_row["sales_rep_id"]
        territory = rep_row["territory"]
        hcp_num = int(RNG.integers(1, 2001))
        hcp_id = f"HCP-{hcp_num:04d}"

        units = int(np.clip(round(RNG.lognormal(3.1, 1.25)), 1, 500))
        wac = float(wac_by_pid[pid])
        discount_factor = float(RNG.uniform(0.88, 1.03))
        gross = round(units * wac * discount_factor, 2)

        channel = str(RNG.choice(CHANNELS, p=CHANNEL_WEIGHTS))
        lo, hi = CHANNEL_NET_RATIOS[channel]
        net_ratio = float(RNG.uniform(lo, hi))
        net = round(gross * net_ratio, 2)

        d = txn_dates[i]
        rows.append(
            {
                "transaction_id": f"TXN-{i + 1:06d}",
                "product_id": pid,
                "sales_rep_id": sales_rep_id,
                "territory": territory,
                "hcp_id": hcp_id,
                "units_sold": units,
                "gross_sales": gross,
                "net_sales": net,
                "channel": channel,
                "transaction_date": d,
                "quarter": date_to_quarter_str(d),
            }
        )
    return pd.DataFrame(rows)


def reps_for_territory(reps: pd.DataFrame, territory: str) -> list:
    return reps.loc[reps["territory"] == territory, "sales_rep_id"].tolist()


def build_hcp_engagements(
    portfolio: pd.DataFrame,
    reps: pd.DataFrame,
    hcp_master: pd.DataFrame,
    n: int = 15_000,
) -> pd.DataFrame:
    """HCP interactions aligned to product, rep, and territory conventions."""
    pids = portfolio["product_id"].tolist()
    ranks = np.arange(1, len(pids) + 1, dtype=float)
    product_weights = 1.0 / np.power(ranks, 0.75)
    product_weights /= product_weights.sum()

    end_dt = datetime.now().date()
    start_dt = end_dt - timedelta(days=183)

    eng_dates = sample_transaction_dates(n, start_dt, end_dt)
    rows = []
    for i in range(n):
        territory = str(RNG.choice(TERRITORIES))
        rep_candidates = reps_for_territory(reps, territory)
        if not rep_candidates:
            territory = TERRITORIES[0]
            rep_candidates = reps_for_territory(reps, territory)
        sales_rep_id = str(RNG.choice(rep_candidates))

        hcp_row = hcp_master.iloc[int(RNG.integers(0, len(hcp_master)))]
        hcp_id = hcp_row["hcp_id"]
        hcp_name = hcp_row["hcp_name"]
        hcp_specialty = hcp_row["hcp_specialty"]

        eng_type = str(RNG.choice(ENGAGEMENT_TYPES, p=ENGAGEMENT_TYPE_WEIGHTS))
        lo, hi = ENGAGEMENT_DURATION_BOUNDS[eng_type]
        duration = int(RNG.integers(lo, hi + 1))

        pid = str(RNG.choice(pids, p=product_weights))
        outcome = str(RNG.choice(OUTCOMES, p=OUTCOME_WEIGHTS))

        rows.append(
            {
                "engagement_id": f"ENG-{i + 1:06d}",
                "hcp_id": hcp_id,
                "hcp_name": hcp_name,
                "hcp_specialty": hcp_specialty,
                "engagement_type": eng_type,
                "product_id": pid,
                "sales_rep_id": sales_rep_id,
                "engagement_date": eng_dates[i],
                "duration_minutes": duration,
                "outcome": outcome,
                "notes": FAKE.sentence(nb_words=12)[:-1],
            }
        )
    return pd.DataFrame(rows)


def build_market_access(portfolio: pd.DataFrame, n: int = 200) -> pd.DataFrame:
    """Payer / formulary coverage rows."""
    pids = portfolio["product_id"].tolist()
    rows = []
    for i in range(n):
        pid = str(RNG.choice(pids))
        status = str(RNG.choice(FORMULARY_STATUSES, p=FORMULARY_STATUS_WEIGHTS))
        tier = int(RNG.choice([1, 2, 3, 4], p=[0.35, 0.35, 0.22, 0.08]))

        if tier == 1:
            copay_lo, copay_hi = 10, 45
        elif tier == 2:
            copay_lo, copay_hi = 35, 120
        elif tier == 3:
            copay_lo, copay_hi = 90, 260
        else:
            copay_lo, copay_hi = 200, 500

        prior_auth = status == "Prior Auth Required" or bool(RNG.random() < 0.18)
        step_therapy = bool(RNG.random() < (0.12 + 0.08 * tier))

        eff_start = datetime.now().date() - timedelta(days=int(RNG.integers(30, 730)))
        lives = int(np.clip(RNG.lognormal(14.5, 1.1), 100_000, 50_000_000))

        rows.append(
            {
                "access_id": f"MA-{i + 1:03d}",
                "product_id": pid,
                "payer_name": str(RNG.choice(PAYERS)),
                "formulary_status": status,
                "tier": tier,
                "copay_amount": float(round(RNG.uniform(copay_lo, copay_hi), 2)),
                "prior_auth_required": prior_auth,
                "step_therapy_required": step_therapy,
                "effective_date": eff_start,
                "lives_covered": lives,
            }
        )
    return pd.DataFrame(rows)


def build_sales_targets(portfolio: pd.DataFrame, reps: pd.DataFrame, n_rows: int = 600) -> pd.DataFrame:
    """Quarterly quotas -- four (product, quarter) targets per rep from top programs."""
    assert n_rows == 600 and len(reps) == 150
    top_products = [f"PRD-{i:03d}" for i in range(1, 21)]
    quarters = ["2025-Q4", "2026-Q1", "2026-Q2"]
    pairs = [(p, q) for p in top_products for q in quarters]
    assert len(pairs) == 60

    wac_by_pid = portfolio.set_index("product_id")["wac_price"].to_dict()
    rows = []
    tgt_num = 1
    for _, rep in reps.iterrows():
        rep_id = rep["sales_rep_id"]
        terr = rep["territory"]
        pick_idx = RNG.choice(60, size=4, replace=False)
        for pi in pick_idx:
            pid, quarter = pairs[int(pi)]
            base = int(RNG.integers(700, 6200))
            target_units = int(np.clip(base * TERRITORY_TARGET_MULTIPLIER[terr], 300, 25_000))
            wac = float(wac_by_pid[pid])
            target_revenue = round(target_units * wac, 2)

            pct = float(RNG.normal(1.0, 0.11))
            pct = float(np.clip(pct, 0.70, 1.30))
            actual_units = int(max(0, round(target_units * pct)))
            actual_revenue = round(actual_units * wac, 2)
            attainment = round(100.0 * actual_units / target_units, 2) if target_units else 0.0

            rows.append(
                {
                    "target_id": f"TGT-{tgt_num:03d}",
                    "sales_rep_id": rep_id,
                    "product_id": pid,
                    "territory": terr,
                    "quarter": quarter,
                    "target_units": target_units,
                    "target_revenue": target_revenue,
                    "actual_units": actual_units,
                    "actual_revenue": actual_revenue,
                    "attainment_pct": attainment,
                }
            )
            tgt_num += 1
    return pd.DataFrame(rows)


def write_delta_table(spark: SparkSession, pdf: pd.DataFrame, table_short_name: str) -> None:
    fq = f"{CATALOG}.{SCHEMA}.{table_short_name}"
    print(f"Writing {len(pdf):,} rows -> {fq} ...")
    spark.createDataFrame(pdf).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(fq)
    print(f"  [OK] Saved {fq}")


def validate_tables(spark: SparkSession) -> None:
    print("\n--- Validation: row counts (read-back) ---")
    tables = [
        "product_portfolio",
        "sales_transactions",
        "hcp_engagements",
        "market_access",
        "sales_targets",
    ]
    expected = {
        "product_portfolio": 50,
        "sales_transactions": 25_000,
        "hcp_engagements": 15_000,
        "market_access": 200,
        "sales_targets": 600,
    }
    for t in tables:
        fq = f"{CATALOG}.{SCHEMA}.{t}"
        cnt = spark.table(fq).count()
        exp = expected[t]
        ok = "OK" if cnt == exp else "CHECK"
        print(f"  {t}: {cnt:,} rows (expected {exp:,}) [{ok}]")


def run_integrity_checks(spark: SparkSession) -> None:
    """Lightweight FK-style checks in Spark SQL (uses temp view ``_workshop_sales_reps``)."""
    print("\n--- Referential integrity spot checks ---")
    q1 = f"""
    SELECT COUNT(*) AS orphans
    FROM {CATALOG}.{SCHEMA}.sales_transactions s
    LEFT ANTI JOIN {CATALOG}.{SCHEMA}.product_portfolio p ON s.product_id = p.product_id
    """
    q2 = f"""
    SELECT COUNT(*) AS orphans
    FROM {CATALOG}.{SCHEMA}.hcp_engagements e
    LEFT ANTI JOIN {CATALOG}.{SCHEMA}.product_portfolio p ON e.product_id = p.product_id
    """
    q3 = f"""
    SELECT COUNT(*) AS mismatches
    FROM {CATALOG}.{SCHEMA}.sales_transactions s
    INNER JOIN _workshop_sales_reps r ON s.sales_rep_id = r.sales_rep_id
    WHERE s.territory <> r.territory
    """
    q4 = f"""
    SELECT COUNT(*) AS orphans
    FROM {CATALOG}.{SCHEMA}.hcp_engagements e
    LEFT ANTI JOIN _workshop_sales_reps r ON e.sales_rep_id = r.sales_rep_id
    """
    checks = [
        ("sales_transactions -> product_portfolio", q1),
        ("hcp_engagements -> product_portfolio", q2),
        ("sales_transactions rep/territory alignment", q3),
        ("hcp_engagements -> sales_reps (session view)", q4),
    ]
    for label, q in checks:
        spark.sql(q).show(truncate=False)
        print(f"  ({label}: expect 0 orphan/mismatch rows)")


def main() -> None:
    print("=" * 72)
    print("Commercial Pharma Workshop -- synthetic structured data")
    print(f"SEED={SEED} | {CATALOG}.{SCHEMA}")
    print(f"As-of (local date anchor): {datetime.now().date()}")
    print("=" * 72)

    spark = SparkSession.builder.getOrCreate()
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

    print("\n[1/5] Building product_portfolio ...")
    portfolio_pdf = build_product_portfolio(50)
    write_delta_table(spark, portfolio_pdf, "product_portfolio")

    print("\n[2/5] Building sales_reps (in-memory) + sales_transactions ...")
    reps_pdf = build_sales_reps(150)
    spark.createDataFrame(reps_pdf).createOrReplaceTempView("_workshop_sales_reps")

    txn_pdf = build_sales_transactions(portfolio_pdf, reps_pdf, 25_000)
    write_delta_table(spark, txn_pdf, "sales_transactions")

    print("\n[3/5] Building HCP master (in-memory) + hcp_engagements ...")
    hcp_pdf = build_hcp_master(2000)

    eng_pdf = build_hcp_engagements(portfolio_pdf, reps_pdf, hcp_pdf, 15_000)
    write_delta_table(spark, eng_pdf, "hcp_engagements")

    print("\n[4/5] Building market_access ...")
    ma_pdf = build_market_access(portfolio_pdf, 200)
    write_delta_table(spark, ma_pdf, "market_access")

    print("\n[5/5] Building sales_targets ...")
    tgt_pdf = build_sales_targets(portfolio_pdf, reps_pdf, 600)
    write_delta_table(spark, tgt_pdf, "sales_targets")

    validate_tables(spark)
    run_integrity_checks(spark)

    print("\nDone. Genie Space can now point at these tables for SQL exploration.")
    print("Core facts: 50 products | 150 reps | 2,000 HCPs | 25k txns | 15k engagements")


if __name__ == "__main__":
    main()
