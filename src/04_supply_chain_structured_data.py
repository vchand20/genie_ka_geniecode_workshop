# Databricks notebook source
"""
Supply Chain (Pharma) Workshop -- Reproducible Synthetic Structured Data

Generates five Delta tables in Unity Catalog for Genie Space SQL exploration:
  ``inventory_levels``, ``manufacturing_batches``, ``supplier_performance``,
  ``distribution_shipments``, ``demand_forecast``.

A shared SKU dimension (200 pharmaceutical SKUs) ensures referential integrity
across inventory, batches, shipments, and forecasts. Cold-chain flags align with
each SKU's storage condition (refrigerated/frozen require cold chain).

Run on a cluster with Spark. ``pip install`` requires network access.
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
SCHEMA = "wsp_supply_chain"

RNG = np.random.default_rng(SEED)
FAKE = Faker("en_US")
FAKE.seed_instance(SEED)
US_HOLIDAYS = holidays.US()

# Anchors: user asked 6-12 months from today
TODAY = date.today()

# Warehouses (12 US DCs)
WAREHOUSES = [
    ("WH-01", "Memphis", "TN"),
    ("WH-02", "Indianapolis", "IN"),
    ("WH-03", "Louisville", "KY"),
    ("WH-04", "Dallas", "TX"),
    ("WH-05", "Columbus", "OH"),
    ("WH-06", "Reno", "NV"),
    ("WH-07", "Allentown", "PA"),
    ("WH-08", "Atlanta", "GA"),
    ("WH-09", "Phoenix", "AZ"),
    ("WH-10", "Seattle", "WA"),
    ("WH-11", "Kansas City", "MO"),
    ("WH-12", "Salt Lake City", "UT"),
]
WAREHOUSE_IDS = [w[0] for w in WAREHOUSES]
WAREHOUSE_BY_ID = {w[0]: f"{w[1]}, {w[2]}" for w in WAREHOUSES}
WH_STATE = {w[0]: w[2] for w in WAREHOUSES}

STORAGE_CONDITIONS = [
    "Ambient",
    "Refrigerated 2-8°C",
    "Frozen -20°C",
    "Controlled Room Temp",
]
STORAGE_WEIGHTS = np.array([0.50, 0.35, 0.10, 0.05])

# Product name fragments for realistic labels
BRANDISH = [
    "Cardiostat",
    "Neuroplex",
    "Oncotrust",
    "Dermaclear",
    "Immunexa",
    "Pulmovant",
    "Metabrix",
    "Hemostable",
    "Visioforte",
    "Rheumalign",
]
DOSAGE_FORMS_PHRASE = [
    "{b} {strength} mg tablets, film-coated",
    "{b} {strength} mg extended-release capsules",
    "{b} {strength} mg/ml concentrate for solution for infusion",
    "{b} {strength} mg powder for solution for injection",
    "{b} {strength} IU/ml solution for injection in vial",
    "{b} {strength} mg/ml solution for injection in prefilled syringe",
    "{b} lyophilized powder {strength} mg per vial (for reconstitution)",
    "{b} inhalation powder, {strength} mcg per dose",
]
STRENGTHS = [2, 5, 10, 20, 25, 40, 50, 75, 100, 150, 200, 400, 500]

MANUFACTURING_SITES = [
    "Site-A (Boston)",
    "Site-B (Research Triangle)",
    "Site-C (San Diego)",
    "Site-D (Basel)",
    "Site-E (Dublin)",
]

SUPPLIER_POOL = [
    "Lonza",
    "Catalent",
    "Thermo Fisher Scientific",
    "Merck KGaA",
    "BASF Pharma Solutions",
    "Evonik Health Care",
    "Colorcon",
    "DFE Pharma",
    "Ashland",
    "Gattefosse",
    "CordenPharma",
    "Albemarle",
    "Pfizer CentreOne",
    "Johnson Matthey",
    "Fujifilm Diosynth",
    "Pfizer Hospira",
    "Recipharm",
    "Siegfried",
    "Samsung Biologics",
    "BIOTEC",
    "Formosa Laboratories",
    "Ajinomoto BioPharma",
    "WuXi Biologics",
    "Novartis Technical Operations",
    "Dr. Reddy's Labs",
    "Lupin API",
    "Aurobindo Pharma",
    "Hetero Labs",
    "Neuland Laboratories",
    "ChemWerth",
    "Albemarle Fine Chemistry",
    "Carbogen Amcis",
    "Excella GmbH",
    "FARMABIOS",
    "Ipca Laboratories",
    "Ind-Swift",
    "Jubilant Generics",
    "Kores India",
    "Megafine Pharma",
    "Nectar Lifesciences",
    "Olon SpA",
    "Polaris Poland",
    "Seqens",
    "Servier Synthesis",
    "Teicke",
    "Unipex",
    "Valsynthe",
    "Wavelength Pharmaceuticals",
    "ZCL Chemicals",
]

MATERIAL_TYPES = [
    "Active Pharmaceutical Ingredient",
    "Excipient",
    "Packaging Primary",
    "Packaging Secondary",
    "Raw Material",
]
MATERIAL_TYPE_WEIGHTS = np.array([0.30, 0.25, 0.20, 0.15, 0.10])

API_NAMES = [
    "Atorvastatin Calcium USP",
    "Rosuvastatin Calcium EP",
    "Semaglutide API (recombinant)",
    "Pembrolizumab Drug Substance",
    "Adalimumab Bulk Drug",
    "Insulin Glargine Biosimilar API",
    "Omeprazole Sodium BP",
    "Metformin HCl Micronized",
    "Apixaban Crystalline Form-I",
    "Rivaroxaban Micronized",
]
EXCIPIENT_NAMES = [
    "Microcrystalline Cellulose PH-102",
    "Lactose Monohydrate Fast-Flo",
    "Croscarmellose Sodium NF",
    "Magnesium Stearate Vegetable",
    "Hypromellose 2910 (HPMC)",
    "Povidone K-30",
    "Sodium Starch Glycolate Type A",
    "Talc USP Purified",
    "Colloidal Silicon Dioxide",
    "Mannitol DC Grade",
]
PKG_PRIMARY = [
    "Amber Type-I Glass Vial 10ml",
    "Sterile Ready-to-Fill PFS 1ml",
    "HDPE Bottle 75cc CR Closure",
    "Aluminum Blister Foil 20um",
    "Child-Resistant PP Container 100cc",
    "Pre-sterilized Lyophilization Vial 30ml",
]
PKG_SECONDARY = [
    "Folding Carton 300g GC1",
    "Tamper-Evident Shrink Sleeve",
    "Patient Leaflet 8-page",
    "Shipper Box Insulated EPS",
    "Aggregate Label with Serialization",
    "Pallet Stretch Wrap Heavy Duty",
]
RAW_MATERIAL_NAMES = [
    "Purified Water USP (bulk)",
    "Ethanol 96% Pharmaceutical Grade",
    "Sodium Hydroxide Pellets EP",
    "Hydrochloric Acid Dilute",
    "WFI for Injection (bulk)",
    "Citric Acid Anhydrous USP",
]

REGIONS_FORECAST = ["Northeast", "Southeast", "Midwest", "West", "Southwest"]
MODEL_VERSIONS = ["v3.2", "v3.3", "v4.0"]

# Calendar month seasonality (bounded 0.8-1.3); applied in demand_forecast
SEASONALITY_BY_MONTH = {
    1: 0.88,
    2: 0.86,
    3: 0.92,
    4: 0.98,
    5: 1.05,
    6: 1.12,
    7: 1.18,
    8: 1.15,
    9: 1.08,
    10: 1.02,
    11: 0.95,
    12: 1.22,
}

US_STATES = [
    "AL",
    "AR",
    "AZ",
    "CA",
    "CO",
    "CT",
    "FL",
    "GA",
    "IL",
    "IN",
    "KS",
    "KY",
    "MA",
    "MD",
    "MI",
    "MN",
    "MO",
    "NC",
    "NJ",
    "NV",
    "NY",
    "OH",
    "OR",
    "PA",
    "SC",
    "TN",
    "TX",
    "UT",
    "VA",
    "WA",
    "WI",
]


def _to_business_day(d: date) -> date:
    """Roll calendar date to next weekday not in US federal holiday calendar."""
    cur = d
    step = 0
    while cur.weekday() >= 5 or cur in US_HOLIDAYS:
        cur += timedelta(days=1)
        step += 1
        if step > 14:
            break
    return cur


def _weighted_choice(items, weights, n):
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    idx = RNG.choice(len(items), size=n, p=w)
    return [items[i] for i in idx]


def cold_chain_required(storage_condition: str) -> bool:
    return storage_condition in ("Refrigerated 2-8°C", "Frozen -20°C")


def build_sku_master(n_skus: int = 200) -> pd.DataFrame:
    """Master SKUs: fixed demand, reorder policy, storage, and cost tier."""
    rows = []
    for i in range(1, n_skus + 1):
        sku = f"SKU-{i:03d}"
        storage = _weighted_choice(STORAGE_CONDITIONS, STORAGE_WEIGHTS, 1)[0]
        avg_daily = float(RNG.uniform(25, 800))
        reorder_point = int(RNG.integers(2000, 15_000))
        safety_stock = int(reorder_point * float(RNG.uniform(0.15, 0.35)))
        b = BRANDISH[(i - 1) % len(BRANDISH)]
        strength = STRENGTHS[(i * 7) % len(STRENGTHS)]
        tpl = DOSAGE_FORMS_PHRASE[(i * 3) % len(DOSAGE_FORMS_PHRASE)]
        product_name = tpl.format(b=b, strength=strength)

        if storage in ("Frozen -20°C", "Refrigerated 2-8°C"):
            cost_per_unit = float(RNG.uniform(12.0, 500.0))
        elif "prefilled" in product_name or "vial" in product_name or "infusion" in product_name:
            cost_per_unit = float(RNG.uniform(3.0, 180.0))
        else:
            cost_per_unit = float(RNG.uniform(0.50, 45.0))

        cycle_profile = int(RNG.choice([5, 7, 10, 14, 21, 28]))
        rows.append(
            {
                "sku": sku,
                "product_name": product_name,
                "storage_condition": storage,
                "avg_daily_demand": round(avg_daily, 2),
                "reorder_point": reorder_point,
                "safety_stock": safety_stock,
                "cost_per_unit": round(cost_per_unit, 4),
                "typical_cycle_days": cycle_profile,
            }
        )
    return pd.DataFrame(rows)


def build_inventory_levels(sku_master: pd.DataFrame, n_rows: int = 15_000) -> pd.DataFrame:
    snapshot_start = TODAY - timedelta(days=183)
    snapshot_end = TODAY
    skus = sku_master["sku"].tolist()
    sku_lookup = sku_master.set_index("sku")

    status_opts = ["Available", "Quarantine", "Reserved", "Expired"]
    status_w = np.array([0.80, 0.08, 0.07, 0.05])

    rows = []
    for k in range(1, n_rows + 1):
        sku = RNG.choice(skus)
        row_sku = sku_lookup.loc[sku]
        wh = RNG.choice(WAREHOUSE_IDS)
        snap = snapshot_start + timedelta(days=int(RNG.integers(0, (snapshot_end - snapshot_start).days + 1)))
        snap = _to_business_day(snap)

        mu = np.log(max(row_sku["avg_daily_demand"] * 30, 200))
        sigma = 0.55
        qty = int(np.clip(RNG.lognormal(mu, sigma), 100, 50_000))

        manu_offset = int(RNG.integers(30, 720))
        manufacture = snap - timedelta(days=manu_offset)
        expiry_months = int(RNG.integers(6, 37))
        expiry = manufacture + timedelta(days=int(expiry_months * 30.437))

        yrmo = manufacture.strftime("%Y%m")
        lot_seq = int(RNG.integers(1, 1000))
        lot_number = f"LOT-{yrmo}-{lot_seq:03d}"

        days_oh = float(qty / max(row_sku["avg_daily_demand"], 1e-6))

        st = _weighted_choice(status_opts, status_w, 1)[0]

        rows.append(
            {
                "inventory_id": f"INV-{k:06d}",
                "sku": sku,
                "product_name": row_sku["product_name"],
                "warehouse_id": wh,
                "warehouse_location": WAREHOUSE_BY_ID[wh],
                "snapshot_date": snap,
                "quantity_on_hand": qty,
                "reorder_point": int(row_sku["reorder_point"]),
                "safety_stock": int(row_sku["safety_stock"]),
                "days_on_hand": round(days_oh, 2),
                "lot_number": lot_number,
                "expiry_date": expiry,
                "storage_condition": row_sku["storage_condition"],
                "status": st,
            }
        )
    return pd.DataFrame(rows)


def build_manufacturing_batches(sku_master: pd.DataFrame, n_rows: int = 5_000) -> pd.DataFrame:
    sku_lookup = sku_master.set_index("sku")
    skus = sku_master["sku"].tolist()

    disposition_opts = ["Released", "Rejected", "Under Review", "Quarantine"]
    disp_w = np.array([0.82, 0.05, 0.08, 0.05])

    rows = []
    start_earliest = TODAY - timedelta(days=365)
    start_latest = TODAY - timedelta(days=7)

    for k in range(1, n_rows + 1):
        sku = RNG.choice(skus)
        meta = sku_lookup.loc[sku]
        site = RNG.choice(MANUFACTURING_SITES)

        batch_size = int(RNG.integers(1000, 100_001))
        yield_pct_raw = float(RNG.normal(0.95, 0.025))
        yield_pct = float(np.clip(yield_pct_raw, 0.85, 0.99))
        yield_quantity = int(batch_size * yield_pct)
        yield_pct_display = round(100.0 * yield_quantity / batch_size, 4)

        span = int(RNG.integers(3, 31))
        if "tablet" in meta["product_name"].lower() or "capsule" in meta["product_name"].lower():
            span = int(RNG.integers(3, 14))
        elif "prefilled" in meta["product_name"].lower() or "biologic" in meta["product_name"].lower():
            span = int(RNG.integers(14, 31))

        raw_start = start_earliest + timedelta(
            days=int(RNG.integers(0, max(1, (start_latest - start_earliest).days)))
        )
        start_date = _to_business_day(raw_start)
        end_date = start_date + timedelta(days=span)
        cycle_time = (end_date - start_date).days

        disp = _weighted_choice(disposition_opts, disp_w, 1)[0]
        deviation_count = int(RNG.poisson(0.8))
        deviation_count = min(deviation_count, 5)

        if disp == "Released":
            qa_status = _weighted_choice(["Approved", "Pending"], [0.94, 0.06], 1)[0]
        elif disp == "Rejected":
            qa_status = "Failed"
        else:
            qa_status = _weighted_choice(["Pending", "Approved", "Failed"], [0.70, 0.25, 0.05], 1)[0]

        cpu = float(meta["cost_per_unit"])
        total_cost = round(cpu * batch_size, 2)

        yrmo = start_date.strftime("%Y%m")
        bn_seq = int(RNG.integers(1, 10_000))
        batch_number = f"BN-{yrmo}-{bn_seq:04d}"

        rows.append(
            {
                "batch_id": f"BATCH-{k:06d}",
                "sku": sku,
                "product_name": meta["product_name"],
                "manufacturing_site": site,
                "batch_number": batch_number,
                "batch_size": batch_size,
                "yield_quantity": yield_quantity,
                "yield_pct": yield_pct_display,
                "start_date": start_date,
                "end_date": end_date,
                "cycle_time_days": cycle_time,
                "disposition": disp,
                "deviation_count": deviation_count,
                "qa_status": qa_status,
                "cost_per_unit": round(cpu, 4),
                "total_cost": total_cost,
            }
        )
    return pd.DataFrame(rows)


def _material_name_for_type(material_type: str) -> str:
    if material_type == "Active Pharmaceutical Ingredient":
        return RNG.choice(API_NAMES)
    if material_type == "Excipient":
        return RNG.choice(EXCIPIENT_NAMES)
    if material_type == "Packaging Primary":
        return RNG.choice(PKG_PRIMARY)
    if material_type == "Packaging Secondary":
        return RNG.choice(PKG_SECONDARY)
    return RNG.choice(RAW_MATERIAL_NAMES)


def _lead_time_range(material_type: str) -> tuple[int, int]:
    if material_type == "Active Pharmaceutical Ingredient":
        return 45, 120
    if material_type == "Excipient":
        return 14, 45
    if material_type == "Packaging Primary":
        return 21, 60
    if material_type == "Packaging Secondary":
        return 10, 45
    return 21, 90


def build_supplier_performance(n_rows: int = 3_000) -> pd.DataFrame:
    months_ts = pd.date_range(end=pd.Timestamp(TODAY).replace(day=1), periods=12, freq="MS")
    months = [pd.Timestamp(m).date().replace(day=1) for m in months_ts]

    audit_opts = ["Approved", "Conditional", "Under Review"]
    audit_w = np.array([0.70, 0.20, 0.10])
    risk_opts = ["Low", "Medium", "High"]
    risk_w = np.array([0.50, 0.35, 0.15])

    supplier_names = {f"SUP-{j:03d}": SUPPLIER_POOL[(j - 1) % len(SUPPLIER_POOL)] for j in range(1, 51)}

    rows = []
    for rec_id in range(1, n_rows + 1):
        sup_id = f"SUP-{int(RNG.integers(1, 51)):03d}"
        month = RNG.choice(months)

        mat_type = _weighted_choice(MATERIAL_TYPES, MATERIAL_TYPE_WEIGHTS, 1)[0]
        mat_name = _material_name_for_type(mat_type)

        orders_placed = int(RNG.integers(1, 21))
        ot_frac = float(RNG.uniform(0.70, 1.0))
        orders_on_time = int(round(orders_placed * ot_frac))
        orders_on_time = min(orders_on_time, orders_placed)
        on_time_pct = round(100.0 * orders_on_time / orders_placed, 2) if orders_placed else 0.0

        q_raw = float(RNG.beta(8.0, 2.0))
        quality_score = round(70.0 + q_raw * 30.0, 2)

        lo, hi = _lead_time_range(mat_type)
        lead_time_days = int(RNG.integers(lo, hi + 1))
        lead_time_variance_days = int(RNG.integers(0, 31))

        defect_raw = float(RNG.exponential(0.8))
        defect_rate_pct = round(float(np.clip(defect_raw, 0.0, 5.0)), 3)

        rows.append(
            {
                "record_id": f"SPR-{rec_id:06d}",
                "supplier_id": sup_id,
                "supplier_name": supplier_names[sup_id],
                "material_type": mat_type,
                "material_name": mat_name,
                "month": month,
                "orders_placed": orders_placed,
                "orders_on_time": orders_on_time,
                "on_time_delivery_pct": on_time_pct,
                "quality_score": quality_score,
                "lead_time_days": lead_time_days,
                "lead_time_variance_days": lead_time_variance_days,
                "defect_rate_pct": defect_rate_pct,
                "audit_status": _weighted_choice(audit_opts, audit_w, 1)[0],
                "risk_rating": _weighted_choice(risk_opts, risk_w, 1)[0],
            }
        )

    return pd.DataFrame(rows)


def _destination_name(dest_type: str) -> str:
    if dest_type == "Hospital":
        return f"{FAKE.last_name()} {RNG.choice(['Medical Center', 'Community Hospital', 'Regional Health', 'University Hospital'])}"
    if dest_type == "Retail Pharmacy":
        return f"{FAKE.company()} Pharmacy"
    if dest_type == "Specialty Pharmacy":
        return f"{FAKE.company()} Specialty"
    return f"{FAKE.company()} Wholesale"


def _delivery_lag_days(origin_wh: str, dest_state: str) -> int:
    """Rough zones: farther from hub -> more transit days (1-7). Deterministic w.r.t. states."""
    o_state = WH_STATE[origin_wh]
    same = 1 if o_state == dest_state else 0
    zone = (ord(o_state[0]) + 3 * ord(dest_state[0])) % 7
    base = 2 + zone // 2 + (0 if same else 2)
    return int(np.clip(base + int(RNG.integers(0, 3)), 1, 7))


def build_distribution_shipments(sku_master: pd.DataFrame, n_rows: int = 20_000) -> pd.DataFrame:
    sku_lookup = sku_master.set_index("sku")
    skus = sku_master["sku"].tolist()

    dest_types = ["Hospital", "Retail Pharmacy", "Specialty Pharmacy", "Wholesaler"]
    dest_w = np.array([0.30, 0.35, 0.20, 0.15])

    carriers = ["FedEx", "UPS", "McKesson Logistics", "AmerisourceBergen"]
    car_w = np.array([0.35, 0.30, 0.20, 0.15])

    stat_opts = ["Delivered", "In Transit", "Delayed", "Returned", "Lost"]
    stat_w = np.array([0.85, 0.08, 0.04, 0.02, 0.01])

    ship_start = TODAY - timedelta(days=183)

    rows = []
    for k in range(1, n_rows + 1):
        sku = RNG.choice(skus)
        meta = sku_lookup.loc[sku]
        origin = RNG.choice(WAREHOUSE_IDS)
        dest_type = _weighted_choice(dest_types, dest_w, 1)[0]
        dest_state = RNG.choice(US_STATES)
        dest_name = _destination_name(dest_type)

        qty = int(RNG.integers(10, 5001))
        ship_raw = ship_start + timedelta(days=int(RNG.integers(0, (TODAY - ship_start).days + 1)))
        ship_date = _to_business_day(ship_raw)

        lag = _delivery_lag_days(origin, dest_state)
        expected = ship_date + timedelta(days=lag)

        delivery_status = _weighted_choice(stat_opts, stat_w, 1)[0]
        if delivery_status == "In Transit":
            actual = pd.NaT
        elif delivery_status == "Delayed":
            actual = expected + timedelta(days=int(RNG.integers(2, 5)))
        elif delivery_status == "Returned":
            actual = expected + timedelta(days=int(RNG.integers(0, 3)))
        elif delivery_status == "Lost":
            actual = pd.NaT
        else:
            delta = int(RNG.integers(-1, 4))
            actual = expected + timedelta(days=delta)

        cc = cold_chain_required(meta["storage_condition"])
        temp_exc = False
        if cc:
            temp_exc = bool(RNG.random() < 0.03)

        dist_score = _delivery_lag_days(origin, dest_state)
        shipping_cost = round(float(RNG.uniform(15, 150)) + qty * float(RNG.uniform(0.02, 0.12)) + dist_score * float(RNG.uniform(5, 40)), 2)
        shipping_cost = float(np.clip(shipping_cost, 15.0, 500.0))

        rows.append(
            {
                "shipment_id": f"SHP-{k:06d}",
                "order_id": f"ORD-{k:06d}",
                "sku": sku,
                "origin_warehouse_id": origin,
                "destination_type": dest_type,
                "destination_name": dest_name,
                "destination_state": dest_state,
                "quantity_shipped": qty,
                "ship_date": ship_date,
                "expected_delivery_date": expected,
                "actual_delivery_date": actual,
                "delivery_status": delivery_status,
                "carrier": _weighted_choice(carriers, car_w, 1)[0],
                "cold_chain_required": cc,
                "temperature_excursion": temp_exc,
                "shipping_cost": shipping_cost,
            }
        )
    return pd.DataFrame(rows)


def build_demand_forecast(sku_master: pd.DataFrame, n_rows: int = 6_000) -> pd.DataFrame:
    """Monthly forecasts for top 100 SKUs only: SKU-001 .. SKU-100."""
    top_skus = [f"SKU-{i:03d}" for i in range(1, 101)]
    top = sku_master[sku_master["sku"].isin(top_skus)].sort_values("sku").reset_index(drop=True)
    assert len(top) == 100
    sku_lookup = top.set_index("sku")

    months = pd.date_range(end=TODAY.replace(day=1), periods=12, freq="MS")

    rows = []
    for i in range(1, n_rows + 1):
        sku = top.iloc[int(RNG.integers(0, len(top)))]["sku"]
        meta = sku_lookup.loc[sku]
        month = pd.Timestamp(RNG.choice(months)).date().replace(day=1)
        region = RNG.choice(REGIONS_FORECAST)

        base_hist = meta["avg_daily_demand"] * 30.0
        mnum = month.month
        season = float(np.clip(SEASONALITY_BY_MONTH.get(mnum, 1.0), 0.8, 1.3))
        trend = float(RNG.uniform(0.95, 1.15))
        forecast_quantity = int(max(50, round(base_hist * season * trend)))

        var_pct = float(RNG.uniform(0.05, 0.25))
        sign = RNG.choice([-1.0, 1.0])
        actual_quantity = int(max(0, round(forecast_quantity * (1.0 + sign * var_pct))))

        mape = abs(actual_quantity - forecast_quantity) / max(forecast_quantity, 1) * 100.0
        forecast_accuracy_pct = round(float(np.clip(100.0 - mape, 0.0, 100.0)), 2)
        bias = round((actual_quantity - forecast_quantity) / max(forecast_quantity, 1) * 100.0, 2)

        model_version = RNG.choice(MODEL_VERSIONS)

        rows.append(
            {
                "forecast_id": f"FCT-{i:06d}",
                "sku": sku,
                "product_name": meta["product_name"],
                "month": month,
                "region": region,
                "forecast_quantity": forecast_quantity,
                "actual_quantity": actual_quantity,
                "forecast_accuracy_pct": forecast_accuracy_pct,
                "bias": bias,
                "model_version": model_version,
                "seasonality_factor": round(season, 4),
                "trend_factor": round(trend, 4),
            }
        )
    return pd.DataFrame(rows)


def write_delta_table(spark: SparkSession, pdf: pd.DataFrame, table_short_name: str) -> None:
    fq = f"{CATALOG}.{SCHEMA}.{table_short_name}"
    print(f"Writing {len(pdf):,} rows -> {fq} ...")
    spark.createDataFrame(pdf).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(fq)
    print(f"  [OK] Saved {fq}")


def validate_tables(spark: SparkSession) -> None:
    print("\n--- Validation: row counts (read-back) ---")
    tables = [
        "inventory_levels",
        "manufacturing_batches",
        "supplier_performance",
        "distribution_shipments",
        "demand_forecast",
    ]
    expected = {
        "inventory_levels": 15_000,
        "manufacturing_batches": 5_000,
        "supplier_performance": 3_000,
        "distribution_shipments": 20_000,
        "demand_forecast": 6_000,
    }
    for t in tables:
        fq = f"{CATALOG}.{SCHEMA}.{t}"
        cnt = spark.table(fq).count()
        exp = expected[t]
        ok = "OK" if cnt == exp else "CHECK"
        print(f"  {t}: {cnt:,} rows (expected {exp:,}) [{ok}]")


def run_integrity_checks(spark: SparkSession) -> None:
    print("\n--- Referential integrity & business-rule checks ---")
    wh_list_sql = ", ".join(repr(w) for w in WAREHOUSE_IDS)
    checks = [
        (
            "Child tables: every sku exists in _supply_sku_master",
            f"""
            SELECT 'inventory_levels' AS tbl, COUNT(*) AS orphan_skus FROM {CATALOG}.{SCHEMA}.inventory_levels i
            LEFT ANTI JOIN _supply_sku_master m ON i.sku = m.sku
            UNION ALL
            SELECT 'manufacturing_batches', COUNT(*) FROM {CATALOG}.{SCHEMA}.manufacturing_batches b
            LEFT ANTI JOIN _supply_sku_master m ON b.sku = m.sku
            UNION ALL
            SELECT 'distribution_shipments', COUNT(*) FROM {CATALOG}.{SCHEMA}.distribution_shipments d
            LEFT ANTI JOIN _supply_sku_master m ON d.sku = m.sku
            UNION ALL
            SELECT 'demand_forecast', COUNT(*) FROM {CATALOG}.{SCHEMA}.demand_forecast f
            LEFT ANTI JOIN _supply_sku_master m ON f.sku = m.sku
            """,
        ),
        (
            "distribution_shipments.origin_warehouse_id in known warehouses",
            f"""
            SELECT COUNT(*) AS bad_origin
            FROM {CATALOG}.{SCHEMA}.distribution_shipments
            WHERE origin_warehouse_id NOT IN ({wh_list_sql})
            """,
        ),
        (
            "cold_chain_required matches SKU storage (master)",
            f"""
            SELECT COUNT(*) AS violations
            FROM {CATALOG}.{SCHEMA}.distribution_shipments d
            INNER JOIN _supply_sku_master m ON d.sku = m.sku
            WHERE d.cold_chain_required <>
              (m.storage_condition IN ('Refrigerated 2-8°C', 'Frozen -20°C'))
            """,
        ),
        (
            "temperature_excursion only when cold_chain_required",
            f"""
            SELECT COUNT(*) AS violations
            FROM {CATALOG}.{SCHEMA}.distribution_shipments
            WHERE temperature_excursion AND NOT cold_chain_required
            """,
        ),
        (
            "demand_forecast uses only SKU-001..SKU-100",
            f"""
            SELECT COUNT(*) AS out_of_scope
            FROM {CATALOG}.{SCHEMA}.demand_forecast
            WHERE sku NOT RLIKE '^SKU-(00[1-9]|0[1-9][0-9]|100)$'
            """,
        ),
    ]
    for label, q in checks:
        print(f"\n  > {label}")
        spark.sql(q).show(truncate=False)

    print("\n  (Expect 0 in orphan/violation/out_of_scope counts.)")


def main() -> None:
    print("=" * 72)
    print("Supply Chain (Pharma) Workshop -- synthetic structured data")
    print(f"SEED={SEED} | {CATALOG}.{SCHEMA}")
    print(f"As-of (anchor date): {TODAY}")
    print("=" * 72)

    spark = SparkSession.builder.getOrCreate()
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

    print("\n[0/6] Building SKU master (200 SKUs, shared dimension) ...")
    sku_master = build_sku_master(200)
    print(f"  [OK] SKU master ready: {len(sku_master)} SKUs")
    print(f"  [OK] Cold-chain SKUs: {sku_master['storage_condition'].apply(cold_chain_required).sum()} / {len(sku_master)}")
    spark.createDataFrame(sku_master).createOrReplaceTempView("_supply_sku_master")

    print("\n[1/6] inventory_levels (15,000 rows) ...")
    inv_pdf = build_inventory_levels(sku_master, 15_000)
    write_delta_table(spark, inv_pdf, "inventory_levels")

    print("\n[2/6] manufacturing_batches (5,000 rows) ...")
    batch_pdf = build_manufacturing_batches(sku_master, 5_000)
    write_delta_table(spark, batch_pdf, "manufacturing_batches")

    print("\n[3/6] supplier_performance (3,000 rows) ...")
    sup_pdf = build_supplier_performance(3_000)
    write_delta_table(spark, sup_pdf, "supplier_performance")

    print("\n[4/6] distribution_shipments (20,000 rows) ...")
    ship_pdf = build_distribution_shipments(sku_master, 20_000)
    write_delta_table(spark, ship_pdf, "distribution_shipments")

    print("\n[5/6] demand_forecast (6,000 rows, top 100 SKUs) ...")
    fc_pdf = build_demand_forecast(sku_master, 6_000)
    write_delta_table(spark, fc_pdf, "demand_forecast")

    validate_tables(spark)
    run_integrity_checks(spark)

    print("\nDone. Point your Genie Space at:")
    print(f"  {CATALOG}.{SCHEMA}.*")


if __name__ == "__main__":
    main()
