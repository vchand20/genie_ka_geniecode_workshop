# Pharma Workshop — Genie, Knowledge Assistant & Genie Code

A complete, deployable Databricks Asset Bundle (DAB) that generates all synthetic data for a hands-on pharma workshop covering:

- **Genie Spaces** — structured Delta tables for natural-language SQL exploration
- **Knowledge Assistants (KA)** — PDF document corpora for RAG-based Q&A
- **Genie Code** — advanced analytics with code generation on structured data

Three parallel workshop groups (Commercial, Clinical, Supply Chain) each get their own schema, tables, and documents — ready for participants to build Genie Spaces, KAs, and Genie Code spaces from scratch.

Everything is parameterized — drop the bundle into any workspace, set a target catalog, and deploy.

---

## What gets created

| Schema | Structured Tables (for Genie) | PDF Documents (for KA) |
|---|---|---|
| **wsp_commercial** | `product_portfolio`, `sales_transactions`, `hcp_engagements`, `market_access`, `sales_targets` (~41K rows) | Product Launch Playbook, Competitive Intelligence Report, Field Force Training Guide, Market Research Insights, Incentive Compensation Plan (~85 pages) |
| **wsp_clinical** | `clinical_trials`, `patient_visits`, `adverse_events`, `lab_results`, `protocol_deviations` (~61K rows) | Phase III Protocol, Investigator's Brochure, DSMB Charter, Clinical Operations Manual, Regulatory Strategy (~106 pages) |
| **wsp_supply_chain** | `inventory_levels`, `manufacturing_batches`, `supplier_performance`, `distribution_shipments`, `demand_forecast` (~49K rows) | GMP Manufacturing SOPs, Cold Chain Guidelines, Supplier Audit Report, Risk Management Plan, Serialization Guide (~93 pages) |

Each schema also gets a `documents` volume where PDFs are stored.

---

## Prerequisites

1. **Databricks CLI v0.218+** (DAB support): `databricks --version`
2. **Unity Catalog** enabled on the workspace
3. A catalog you have `CREATE` privileges on (default: `pharma_workshop` — change via `--var catalog=...`)
4. **Serverless notebook compute** enabled

---

## Deploy & run

The bundle does **not** pin a workspace host. DAB picks it up from your environment / `~/.databrickscfg` so the same bundle deploys to any workspace.

```bash
# 1. Authenticate to your workspace (one of the following):
#    a) Use a profile from ~/.databrickscfg
#       databricks bundle deploy -p my-workspace
#    b) Use the DEFAULT profile (no flag)
#    c) Use env vars
#       export DATABRICKS_HOST=https://my-workspace.cloud.databricks.com
#       export DATABRICKS_TOKEN=dapi...

# 2. Validate the bundle
databricks bundle validate

# 3. Deploy notebooks + job
databricks bundle deploy --var catalog=my_catalog

# 4. Run the job (synchronous, follows logs)
databricks bundle run pharma_workshop_pipeline

# Or trigger via UI: Workflows -> "Pharma Workshop — Data Generation Pipeline (DAB)"
```

### Variables (override with `--var name=value`)

| Variable | Default | Notes |
|---|---|---|
| `catalog` | `pharma_workshop` | Target catalog — must exist with CREATE privileges |

---

## Job DAG (7 tasks)

```
setup
  ↓
  ├── commercial_structured_data
  ├── clinical_structured_data
  ├── supply_chain_structured_data
  ├── commercial_pdfs
  ├── clinical_pdfs
  └── supply_chain_pdfs
```

All six data-generation tasks run in parallel after setup completes.
Typical end-to-end run on serverless: ~15 minutes.

---

## Repo layout

```
genie_ka_geniecode_workshop/
├── databricks.yml                          # bundle metadata, variables, targets
├── README.md                              # this file
├── resources/
│   └── pharma_workshop_pipeline.yml       # 7-task job DAG
├── src/                                   # all notebooks (.py source format)
│   ├── 01_setup.py                        # creates schemas and volumes
│   ├── 02_commercial_structured_data.py   # 5 tables → wsp_commercial
│   ├── 03_clinical_structured_data.py     # 5 tables → wsp_clinical
│   ├── 04_supply_chain_structured_data.py # 5 tables → wsp_supply_chain
│   ├── 05_commercial_pdfs.py             # 5 PDFs → wsp_commercial.documents
│   ├── 06_clinical_pdfs.py               # 5 PDFs → wsp_clinical.documents
│   └── 07_supply_chain_pdfs.py           # 5 PDFs → wsp_supply_chain.documents
└── docs/
    └── WORKSHOP_GUIDE.md                  # facilitator guide and group assignments
```

---

## Workshop groups

### Group 1: Commercial Pharma
- **Genie Space tables:** `product_portfolio`, `sales_transactions`, `hcp_engagements`, `market_access`, `sales_targets`
- **KA documents:** Product Launch Playbook, Competitive Intelligence Report, Field Force Training Guide, Market Research Insights, Incentive Compensation Plan

### Group 2: Clinical Pharma
- **Genie Space tables:** `clinical_trials`, `patient_visits`, `adverse_events`, `lab_results`, `protocol_deviations`
- **KA documents:** Phase III Protocol, Investigator's Brochure, DSMB Charter, Clinical Operations Manual, Regulatory Strategy

### Group 3: Supply Chain
- **Genie Space tables:** `inventory_levels`, `manufacturing_batches`, `supplier_performance`, `distribution_shipments`, `demand_forecast`
- **KA documents:** GMP Manufacturing SOPs, Cold Chain Guidelines, Supplier Audit Report, Risk Management Plan, Serialization Guide

---

## Workshop flow

After data generation is complete, participants follow these steps:

1. **Build a Genie Space** — select tables from their group's schema, add sample questions, and explore data with natural language
2. **Build a Knowledge Assistant** — point a KA at their group's `documents` volume, then ask questions against the PDF corpus
3. **Build a Genie Code space** — create an advanced analytics space with code generation capabilities on the structured data

---

## Reproducing without DAB

If you prefer to run notebooks manually (without the bundle):

1. Upload the `src/` folder to your Databricks workspace
2. Open each notebook and set the `catalog` widget to your target catalog
3. Run `01_setup.py` first, then run `02`–`07` in any order

---

## Dependencies

Installed automatically by each notebook at runtime (no pre-install needed):

- `faker` — realistic synthetic data generation
- `holidays` — US holiday calendar for date patterns
- `fpdf2` — PDF document generation
