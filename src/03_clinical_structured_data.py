# Databricks notebook source
import subprocess

subprocess.check_call(["pip", "install", "faker", "holidays"])

import random
from datetime import date, timedelta

import holidays
import numpy as np
from faker import Faker
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

dbutils.widgets.text("catalog", "pharma_workshop", "Catalog Name")
CATALOG = dbutils.widgets.get("catalog").strip()
assert CATALOG, "ERROR: Please provide a catalog name in the widget above before running."
SCHEMA = "wsp_clinical"
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

SEED = 42
np.random.seed(SEED)
random.seed(SEED)
Faker.seed(SEED)

fake = Faker("en_US")
fake.seed_instance(SEED)

US_HOLIDAYS = holidays.US()

spark = SparkSession.builder.getOrCreate()
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {FULL_SCHEMA}")

PHASES = ["Phase 1", "Phase 1b", "Phase 2", "Phase 2b", "Phase 3", "Phase 4"]
THERAPEUTIC_AREAS = [
    "Oncology",
    "Immunology",
    "Cardiology",
    "Neurology",
    "Endocrinology",
    "Respiratory",
    "Rare Disease",
    "Hematology",
    "Infectious Disease",
    "Dermatology",
]
TRIAL_STATUSES = [
    "Recruiting",
    "Active, not recruiting",
    "Completed",
    "Terminated",
    "Suspended",
    "Withdrawn",
]
VISIT_TYPES = [
    "Screening",
    "Baseline",
    "Treatment",
    "Follow-up",
    "Unscheduled",
    "End of Study",
]
AE_TERMS = [
    "Nausea",
    "Headache",
    "Fatigue",
    "Hypertension",
    "Neutropenia",
    "ALT increased",
    "Rash",
    "Pyrexia",
    "Dizziness",
    "Abdominal pain",
    "Insomnia",
    "Anemia",
    "Hypokalemia",
    "Infusion reaction",
    "Vomiting",
    "Diarrhea",
]
AE_SEVERITY = ["Mild", "Moderate", "Severe", "Life-threatening"]
CAUSALITY = ["Unrelated", "Unlikely", "Possible", "Probable", "Definite"]
AE_OUTCOMES = ["Resolved", "Resolving", "Ongoing", "Fatal", "Unknown", "Sequelae"]
LAB_PANELS = ["Hematology", "Chemistry", "Coagulation", "Urinalysis", "Lipid panel"]
LAB_TESTS = {
    "Hematology": [
        ("WBC", "10^9/L", 4.0, 11.0),
        ("RBC", "10^12/L", 4.2, 5.8),
        ("Hemoglobin", "g/dL", 12.0, 17.5),
        ("Platelets", "10^9/L", 150.0, 450.0),
        ("ANC", "10^9/L", 1.8, 8.0),
    ],
    "Chemistry": [
        ("Glucose", "mg/dL", 70.0, 120.0),
        ("Creatinine", "mg/dL", 0.7, 1.3),
        ("eGFR", "mL/min/1.73m2", 60.0, 120.0),
        ("Sodium", "mmol/L", 135.0, 145.0),
        ("Potassium", "mmol/L", 3.5, 5.1),
        ("ALT", "U/L", 10.0, 55.0),
        ("AST", "U/L", 10.0, 50.0),
        ("Albumin", "g/dL", 3.5, 5.0),
    ],
    "Coagulation": [
        ("INR", "ratio", 0.9, 1.1),
        ("aPTT", "sec", 25.0, 35.0),
    ],
    "Urinalysis": [
        ("Urine protein/creatinine ratio", "mg/g", 10.0, 150.0),
        ("Urine glucose", "mg/dL", 0.0, 30.0),
    ],
    "Lipid panel": [
        ("Total cholesterol", "mg/dL", 120.0, 220.0),
        ("LDL-C", "mg/dL", 60.0, 160.0),
        ("HDL-C", "mg/dL", 35.0, 80.0),
        ("Triglycerides", "mg/dL", 50.0, 200.0),
    ],
}
DEV_TYPES = [
    "Inclusion criteria violation",
    "Exclusion criteria violation",
    "Out of window visit",
    "Informed consent deviation",
    "Dose administration error",
    "Prohibited concomitant medication",
    "LAB sample handling issue",
    "Randomization error",
]
DEV_SEVERITY = ["Minor", "Major", "Critical"]
CAPA_STATUS = ["Not required", "Open", "In progress", "Closed", "Overdue"]


def shift_off_holiday_weekend(d: date) -> date:
    guard = 0
    while (d.weekday() >= 5 or d in US_HOLIDAYS) and guard < 14:
        d += timedelta(days=1)
        guard += 1
    return d


# --- clinical_trials (30) ---
n_trials = 30
trials_rows = []
for i in range(1, n_trials + 1):
    enroll_target = int(np.random.randint(80, 600))
    enroll_actual = int(np.random.randint(int(enroll_target * 0.85), enroll_target + 1))
    start = fake.date_between(date(2019, 1, 1), date(2024, 6, 1))
    phase = str(np.random.choice(PHASES, p=[0.12, 0.1, 0.22, 0.08, 0.35, 0.13]))
    status = str(
        np.random.choice(
            TRIAL_STATUSES,
            p=[0.15, 0.25, 0.35, 0.08, 0.07, 0.10],
        )
    )
    trials_rows.append(
        {
            "trial_id": i,
            "trial_code": f"NB-{np.random.randint(10000, 99999)}-{chr(65 + (i % 26))}",
            "trial_title": fake.sentence(nb_words=8).rstrip(".")[:200],
            "phase": phase,
            "therapeutic_area": str(np.random.choice(THERAPEUTIC_AREAS)),
            "status": status,
            "enrollment_target": enroll_target,
            "enrollment_actual": enroll_actual,
            "first_subject_first_visit_date": start,
            "data_cutoff_date": start + timedelta(days=int(np.random.randint(180, 900))),
            "sponsor": fake.company(),
            "indication": fake.catch_phrase()[:120],
        }
    )

trials_schema = StructType(
    [
        StructField("trial_id", IntegerType(), False),
        StructField("trial_code", StringType(), False),
        StructField("trial_title", StringType(), True),
        StructField("phase", StringType(), False),
        StructField("therapeutic_area", StringType(), False),
        StructField("status", StringType(), False),
        StructField("enrollment_target", IntegerType(), False),
        StructField("enrollment_actual", IntegerType(), False),
        StructField("first_subject_first_visit_date", DateType(), False),
        StructField("data_cutoff_date", DateType(), False),
        StructField("sponsor", StringType(), False),
        StructField("indication", StringType(), True),
    ]
)
clinical_trials_df = spark.createDataFrame(trials_rows, trials_schema)

trial_enrollment = {r["trial_id"]: r["enrollment_actual"] for r in trials_rows}

all_subject_pairs = []
for tid, cap in trial_enrollment.items():
    for pid in range(1, cap + 1):
        all_subject_pairs.append((tid, pid))
all_subject_pairs_arr = np.array(all_subject_pairs, dtype=np.int64)

# --- patient_visits (20000) ---
n_visits = 20000
idx = np.random.choice(len(all_subject_pairs_arr), size=n_visits, replace=True)
visit_pairs = all_subject_pairs_arr[idx]

visits_rows = []
for v in range(n_visits):
    tid, pid = int(visit_pairs[v, 0]), int(visit_pairs[v, 1])
    trial_start = trials_rows[tid - 1]["first_subject_first_visit_date"]
    visit_day = shift_off_holiday_weekend(
        trial_start + timedelta(days=int(np.random.randint(0, 540)))
    )
    sbp = float(np.random.normal(122, 14))
    dbp = float(np.random.normal(78, 10))
    sbp = max(85.0, min(190.0, sbp))
    dbp = max(50.0, min(115.0, dbp))
    if dbp >= sbp:
        dbp = sbp - float(np.random.uniform(15, 35))
    hr = float(np.clip(np.random.normal(72, 12), 45.0, 140.0))
    wt = float(np.clip(np.random.normal(78.0, 18.0), 40.0, 160.0))
    temp_c = float(np.clip(np.random.normal(36.6, 0.35), 35.0, 39.5))
    visits_rows.append(
        {
            "visit_id": 100000 + v,
            "trial_id": tid,
            "patient_id": pid,
            "site_id": f"SITE-{np.random.randint(101, 199)}",
            "visit_number": int(np.random.randint(1, 15)),
            "visit_type": str(
                np.random.choice(
                    VISIT_TYPES,
                    p=[0.12, 0.15, 0.35, 0.22, 0.08, 0.08],
                )
            ),
            "visit_date": visit_day,
            "systolic_bp_mmhg": round(sbp, 1),
            "diastolic_bp_mmhg": round(dbp, 1),
            "heart_rate_bpm": round(hr, 1),
            "weight_kg": round(wt, 2),
            "temperature_c": round(temp_c, 2),
        }
    )

visits_schema = StructType(
    [
        StructField("visit_id", LongType(), False),
        StructField("trial_id", IntegerType(), False),
        StructField("patient_id", IntegerType(), False),
        StructField("site_id", StringType(), False),
        StructField("visit_number", IntegerType(), False),
        StructField("visit_type", StringType(), False),
        StructField("visit_date", DateType(), False),
        StructField("systolic_bp_mmhg", DoubleType(), False),
        StructField("diastolic_bp_mmhg", DoubleType(), False),
        StructField("heart_rate_bpm", DoubleType(), False),
        StructField("weight_kg", DoubleType(), False),
        StructField("temperature_c", DoubleType(), False),
    ]
)
patient_visits_df = spark.createDataFrame(visits_rows, visits_schema)

visit_lookup = {}
for r in visits_rows:
    k = (r["trial_id"], r["patient_id"])
    visit_lookup.setdefault(k, []).append(r["visit_id"])
visit_date_by_id = {r["visit_id"]: r["visit_date"] for r in visits_rows}
visit_key_by_index = [
    (visits_rows[i]["trial_id"], visits_rows[i]["patient_id"], visits_rows[i]["visit_id"])
    for i in range(n_visits)
]

visits_pdf = patient_visits_df.select("trial_id", "patient_id").distinct().toPandas()
subject_keys = list(zip(visits_pdf["trial_id"].tolist(), visits_pdf["patient_id"].tolist()))

# --- adverse_events (8000) ---
n_ae = 8000
ae_rows = []
for a in range(n_ae):
    tid, pid = subject_keys[np.random.randint(0, len(subject_keys))]
    onset = trials_rows[tid - 1]["first_subject_first_visit_date"] + timedelta(
        days=int(np.random.randint(0, 500))
    )
    candidates = visit_lookup.get((tid, pid), [])
    chosen_visit = int(np.random.choice(candidates)) if candidates else None
    resolved = None
    if np.random.random() >= 0.25:
        resolved = onset + timedelta(days=int(np.random.randint(3, 120)))
    ae_rows.append(
        {
            "adverse_event_id": 500000 + a,
            "trial_id": tid,
            "patient_id": pid,
            "visit_id": chosen_visit,
            "ae_term": str(np.random.choice(AE_TERMS)),
            "meddra_pt_code": f"PT{np.random.randint(100000, 999999)}",
            "severity": str(np.random.choice(AE_SEVERITY, p=[0.45, 0.30, 0.18, 0.07])),
            "causality_assessment": str(
                np.random.choice(CAUSALITY, p=[0.18, 0.22, 0.25, 0.20, 0.15])
            ),
            "outcome": str(
                np.random.choice(AE_OUTCOMES, p=[0.42, 0.18, 0.28, 0.01, 0.08, 0.03])
            ),
            "serious_flag": bool(np.random.random() < 0.12),
            "onset_date": onset,
            "resolved_date": resolved,
        }
    )

ae_schema = StructType(
    [
        StructField("adverse_event_id", LongType(), False),
        StructField("trial_id", IntegerType(), False),
        StructField("patient_id", IntegerType(), False),
        StructField("visit_id", LongType(), True),
        StructField("ae_term", StringType(), False),
        StructField("meddra_pt_code", StringType(), False),
        StructField("severity", StringType(), False),
        StructField("causality_assessment", StringType(), False),
        StructField("outcome", StringType(), False),
        StructField("serious_flag", BooleanType(), False),
        StructField("onset_date", DateType(), False),
        StructField("resolved_date", DateType(), True),
    ]
)
adverse_events_df = spark.createDataFrame(ae_rows, ae_schema)

# --- lab_results (30000) ---
n_lab = 30000
lab_rows = []
for l in range(n_lab):
    tid, pid, vid = visit_key_by_index[np.random.randint(0, n_visits)]
    panel = str(np.random.choice(LAB_PANELS, p=[0.28, 0.35, 0.12, 0.12, 0.13]))
    test_name, unit, lo, hi = LAB_TESTS[panel][np.random.randint(0, len(LAB_TESTS[panel]))]
    raw = float(np.random.normal((lo + hi) / 2.0, (hi - lo) * 0.12))
    if np.random.random() < 0.08:
        raw = float(lo - np.random.uniform(0.05, 0.25) * (hi - lo))
    elif np.random.random() < 0.08:
        raw = float(hi + np.random.uniform(0.05, 0.35) * (hi - lo))
    raw = max(raw, lo * 0.5)
    flag = "N"
    if raw < lo * 0.98:
        flag = "L"
    elif raw > hi * 1.02:
        flag = "H"
    lab_rows.append(
        {
            "lab_result_id": 900000 + l,
            "visit_id": vid,
            "trial_id": tid,
            "patient_id": pid,
            "lab_panel": panel,
            "analyte_name": test_name,
            "result_value": round(raw, 3 if raw < 20 else 2),
            "unit": unit,
            "reference_low": lo,
            "reference_high": hi,
            "abnormal_flag": flag,
            "collection_date": visit_date_by_id[vid],
        }
    )

lab_schema = StructType(
    [
        StructField("lab_result_id", LongType(), False),
        StructField("visit_id", LongType(), False),
        StructField("trial_id", IntegerType(), False),
        StructField("patient_id", IntegerType(), False),
        StructField("lab_panel", StringType(), False),
        StructField("analyte_name", StringType(), False),
        StructField("result_value", DoubleType(), False),
        StructField("unit", StringType(), False),
        StructField("reference_low", DoubleType(), False),
        StructField("reference_high", DoubleType(), False),
        StructField("abnormal_flag", StringType(), False),
        StructField("collection_date", DateType(), False),
    ]
)
lab_results_df = spark.createDataFrame(lab_rows, lab_schema)

# --- protocol_deviations (3000) ---
n_pd = 3000
pd_rows = []
for p in range(n_pd):
    tid, pid = subject_keys[np.random.randint(0, len(subject_keys))]
    disc = shift_off_holiday_weekend(
        trials_rows[tid - 1]["first_subject_first_visit_date"]
        + timedelta(days=int(np.random.randint(0, 520)))
    )
    pd_rows.append(
        {
            "protocol_deviation_id": 700000 + p,
            "trial_id": tid,
            "patient_id": pid,
            "site_id": f"SITE-{np.random.randint(101, 199)}",
            "deviation_category": str(np.random.choice(DEV_TYPES)),
            "deviation_severity": str(
                np.random.choice(DEV_SEVERITY, p=[0.55, 0.35, 0.10])
            ),
            "discovery_date": disc,
            "capa_status": str(
                np.random.choice(CAPA_STATUS, p=[0.25, 0.18, 0.22, 0.30, 0.05])
            ),
            "description": fake.text(max_nb_chars=240),
        }
    )

pd_schema = StructType(
    [
        StructField("protocol_deviation_id", LongType(), False),
        StructField("trial_id", IntegerType(), False),
        StructField("patient_id", IntegerType(), False),
        StructField("site_id", StringType(), False),
        StructField("deviation_category", StringType(), False),
        StructField("deviation_severity", StringType(), False),
        StructField("discovery_date", DateType(), False),
        StructField("capa_status", StringType(), False),
        StructField("description", StringType(), True),
    ]
)
protocol_deviations_df = spark.createDataFrame(pd_rows, pd_schema)

# --- Write Delta tables ---
clinical_trials_df.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{FULL_SCHEMA}.clinical_trials")
patient_visits_df.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{FULL_SCHEMA}.patient_visits")
adverse_events_df.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{FULL_SCHEMA}.adverse_events")
lab_results_df.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{FULL_SCHEMA}.lab_results")
protocol_deviations_df.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{FULL_SCHEMA}.protocol_deviations")

# --- Validation ---
print("=== Row counts ===")
for t in [
    "clinical_trials",
    "patient_visits",
    "adverse_events",
    "lab_results",
    "protocol_deviations",
]:
    c = spark.table(f"{FULL_SCHEMA}.{t}").count()
    print(f"{t}: {c}")

assert spark.table(f"{FULL_SCHEMA}.clinical_trials").count() == 30
assert spark.table(f"{FULL_SCHEMA}.patient_visits").count() == 20000
assert spark.table(f"{FULL_SCHEMA}.adverse_events").count() == 8000
assert spark.table(f"{FULL_SCHEMA}.lab_results").count() == 30000
assert spark.table(f"{FULL_SCHEMA}.protocol_deviations").count() == 3000

orphan_visits = spark.sql(
    f"""
    SELECT COUNT(*) AS c
    FROM {FULL_SCHEMA}.patient_visits v
    LEFT ANTI JOIN {FULL_SCHEMA}.clinical_trials t ON v.trial_id = t.trial_id
    """
).collect()[0]["c"]
assert orphan_visits == 0, f"patient_visits with missing trial: {orphan_visits}"

ae_bad = spark.sql(
    f"""
    SELECT COUNT(*) AS c
    FROM {FULL_SCHEMA}.adverse_events a
    LEFT ANTI JOIN {FULL_SCHEMA}.clinical_trials t ON a.trial_id = t.trial_id
    """
).collect()[0]["c"]
assert ae_bad == 0

ae_subject = spark.sql(
    f"""
    SELECT COUNT(*) AS c
    FROM {FULL_SCHEMA}.adverse_events a
    WHERE NOT EXISTS (
      SELECT 1 FROM {FULL_SCHEMA}.patient_visits v
      WHERE v.trial_id = a.trial_id AND v.patient_id = a.patient_id
    )
    """
).collect()[0]["c"]
assert ae_subject == 0, f"AE subject not in visits: {ae_subject}"

ae_visit_mismatch = spark.sql(
    f"""
    SELECT COUNT(*) AS c
    FROM {FULL_SCHEMA}.adverse_events a
    WHERE a.visit_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM {FULL_SCHEMA}.patient_visits v
        WHERE v.visit_id = a.visit_id
          AND v.trial_id = a.trial_id
          AND v.patient_id = a.patient_id
      )
    """
).collect()[0]["c"]
assert ae_visit_mismatch == 0, f"AE visit mismatch: {ae_visit_mismatch}"

lab_bad = spark.sql(
    f"""
    SELECT COUNT(*) AS c
    FROM {FULL_SCHEMA}.lab_results l
    WHERE NOT EXISTS (
      SELECT 1 FROM {FULL_SCHEMA}.patient_visits v
      WHERE v.visit_id = l.visit_id
        AND v.trial_id = l.trial_id
        AND v.patient_id = l.patient_id
    )
    """
).collect()[0]["c"]
assert lab_bad == 0, f"lab_results not aligned to visits: {lab_bad}"

pd_bad = spark.sql(
    f"""
    SELECT COUNT(*) AS c
    FROM {FULL_SCHEMA}.protocol_deviations d
    WHERE NOT EXISTS (
      SELECT 1 FROM {FULL_SCHEMA}.patient_visits v
      WHERE v.trial_id = d.trial_id AND v.patient_id = d.patient_id
    )
    """
).collect()[0]["c"]
assert pd_bad == 0, f"protocol_deviations without visit subject: {pd_bad}"

print("=== Referential integrity checks passed ===")
