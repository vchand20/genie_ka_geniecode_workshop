# Databricks notebook source
"""
Pharma Workshop - Setup & Infrastructure
=========================================
Run this notebook FIRST to create all Unity Catalog schemas and volumes.
Then run notebooks 02-07 in any order (structured data and PDFs are independent).

Schemas: wsp_commercial, wsp_clinical, wsp_supply_chain
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
dbutils.widgets.text("catalog", "pharma_workshop", "Catalog Name")
CATALOG = dbutils.widgets.get("catalog").strip()
assert CATALOG, "ERROR: Please provide a catalog name in the widget above before running."
SCHEMAS = {
    "wsp_commercial": "Commercial Pharma: Sales, HCP engagement, market access",
    "wsp_clinical": "Clinical Pharma: Trials, patients, adverse events, lab results",
    "wsp_supply_chain": "Supply Chain: Inventory, manufacturing, distribution",
}

print("=" * 70)
print("PHARMA WORKSHOP - INFRASTRUCTURE SETUP")
print("=" * 70)

spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
print(f"\n✓ Catalog: {CATALOG}")

for schema, description in SCHEMAS.items():
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{schema} COMMENT '{description}'")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{schema}.documents COMMENT 'PDF documents for Knowledge Assistant'")
    print(f"✓ Schema: {CATALOG}.{schema}")
    print(f"  └─ Volume: {CATALOG}.{schema}.documents")

print("\n" + "=" * 70)
print("SETUP COMPLETE")
print("=" * 70)
print("""
Next steps - run these notebooks (in any order):

STRUCTURED DATA (for Genie Spaces):
  02_commercial_structured_data.py  → 5 tables in wsp_commercial
  03_clinical_structured_data.py    → 5 tables in wsp_clinical
  04_supply_chain_structured_data.py → 5 tables in wsp_supply_chain

PDF DOCUMENTS (for Knowledge Assistants):
  05_commercial_pdfs.py  → 5 PDFs in wsp_commercial.documents
  06_clinical_pdfs.py    → 5 PDFs in wsp_clinical.documents
  07_supply_chain_pdfs.py → 5 PDFs in wsp_supply_chain.documents
""")

print("\nValidating schemas...")
schemas_df = spark.sql(f"SHOW SCHEMAS IN {CATALOG}").filter("databaseName LIKE 'wsp_%'")
schemas_df.show(truncate=False)

print("Validating volumes...")
for schema in SCHEMAS:
    vols = spark.sql(f"SHOW VOLUMES IN {CATALOG}.{schema}")
    vols.show(truncate=False)

print("All infrastructure ready!")
