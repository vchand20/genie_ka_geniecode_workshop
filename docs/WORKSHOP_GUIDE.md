# Workshop Facilitator Guide

## Pre-workshop setup

1. Deploy the bundle to the target workspace:

   ```bash
   databricks bundle deploy --var catalog=<your_catalog>
   databricks bundle run pharma_workshop_pipeline
   ```

2. Verify all 15 tables and 15 PDFs were created:

   ```sql
   -- Check tables
   SHOW TABLES IN <catalog>.wsp_commercial;
   SHOW TABLES IN <catalog>.wsp_clinical;
   SHOW TABLES IN <catalog>.wsp_supply_chain;

   -- Check volumes
   LIST '/Volumes/<catalog>/wsp_commercial/documents/';
   LIST '/Volumes/<catalog>/wsp_clinical/documents/';
   LIST '/Volumes/<catalog>/wsp_supply_chain/documents/';
   ```

3. Ensure participants have `USE CATALOG`, `USE SCHEMA`, and `SELECT` on the catalog.

---

## Group assignments

| Group | Schema | Focus |
|---|---|---|
| **1 - Commercial** | `wsp_commercial` | Sales analytics, HCP engagement, market access |
| **2 - Clinical** | `wsp_clinical` | Trial management, patient safety, lab analytics |
| **3 - Supply Chain** | `wsp_supply_chain` | Inventory optimization, manufacturing quality, logistics |

---

## Exercise 1: Build a Genie Space

Each group creates a Genie Space from their schema's tables:

1. Navigate to **Genie** in the workspace sidebar
2. Click **New** and select your group's 5 tables
3. Add 3–5 sample questions relevant to the domain
4. Test natural-language queries against the data

**Example questions by group:**

- **Commercial:** "What are the top 5 products by revenue this quarter?", "Show HCP engagement trends by specialty"
- **Clinical:** "How many adverse events were reported per trial?", "Which sites have the most protocol deviations?"
- **Supply Chain:** "Which warehouses have inventory below safety stock?", "Show batch yield by manufacturing site"

---

## Exercise 2: Build a Knowledge Assistant

Each group creates a KA from their schema's PDF documents:

1. Navigate to **AI Playground** → **Knowledge Assistant**
2. Create a new KA pointed at `/Volumes/<catalog>/<schema>/documents`
3. Ask questions that require synthesizing information across documents
4. Evaluate answer quality and source citations

---

## Exercise 3: Build a Genie Code Space

Each group creates a Genie Code space for advanced analytics:

1. Navigate to **Genie** → create a new space with code capabilities enabled
2. Select tables from their group's schema
3. Ask analytical questions that require computed metrics, joins, or visualizations
4. Review the generated code and iterate on results

---

## Timing guide

| Activity | Duration |
|---|---|
| Introduction & setup | 15 min |
| Exercise 1: Genie Space | 30 min |
| Exercise 2: Knowledge Assistant | 30 min |
| Exercise 3: Genie Code | 30 min |
| Wrap-up & discussion | 15 min |
| **Total** | **~2 hours** |
