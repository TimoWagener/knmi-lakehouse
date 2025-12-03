# 🌩️ Master Design Doc: KNMI Modern Data Lakehouse

## 1. Project Mission & Status
We are building a **Vendor-Neutral, Single-Node Data Lakehouse** to analyze Dutch weather data (KNMI).
*   **Philosophy:** "Write Once, Run Anywhere." The code must run on a local Laptop (MinIO) and Google Cloud (Cloud Run + GCS) by changing *only* environment variables.
*   **Current State:**
    *   Repository initialized: `https://github.com/TimoWagener/knmi-lakehouse`
    *   Environment: `uv` initialized.
    *   Git: `main` branch active.
    *   Infrastructure: `docker-compose.yaml` ready with MinIO and Dagster (Pure SQLite mode).

## 2. The Full Tech Stack (Strict Requirements)

| Layer | Tool | Configuration/Notes |
| :--- | :--- | :--- |
| **Env Manager** | **`uv`** | Replaces pip/poetry. Used for all dependency management. |
| **Orchestrator** | **Dagster** | Asset-aware. Uses **Dynamic Partitions** for stations and **Monthly Partitions** for time. |
| **Compute** | **DuckDB** | In-process OLAP. Reads JSON/Parquet directly via `httpfs` (S3). |
| **Table Format**| **Apache Iceberg** | Open table format for ACID transactions and time travel. |
| **Transformation**| **dbt** | `dbt-duckdb` adapter. "Strict Medallion" architecture. |
| **Storage Protocol**| **S3** | **CRITICAL:** We use `fsspec` + `s3fs`. We **never** write to local disk paths. |
| **Storage Backend** | **MinIO** (Local) / **GCS** (Prod) | Swappable via `.env`. |
| **Visualization** | **Streamlit** | Uses **Polars** for zero-copy data transfer from DuckDB. |
| **Linting** | **`ruff`** | Enforced code quality. |

## 3. Directory Structure
The AI must adhere to this structure.

```text
knmi_lakehouse/
├── .env                     # Secrets (Excluded from Git)
├── pyproject.toml           # uv dependencies
├── uv.lock                  # Locked versions
├── docker-compose.yaml      # MinIO + Dagster Webserver + Daemon
├── dagster.yaml             # Configured for SQLite system storage
├── src/                     # DAGSTER CODEBASE
│   ├── __init__.py
│   ├── definitions.py       # Job/Schedule/Sensor wiring
│   ├── partitions.py        # Shared Partition Definitions
│   ├── assets/
│   │   ├── __init__.py
│   │   ├── metadata.py      # Station Discovery (The "Entry Point")
│   │   ├── ingestion.py     # LANDING: Main Data Pump (History & Live)
│   │   └── bronze.py        # BRONZE: Landing -> Iceberg
│   └── utils/
│       └── smart_client.py  # Shared API Logic & FileSystem abstraction
├── dbt_project/             # DBT CODEBASE (Coming Soon)
│   ├── dbt_project.yml
│   ├── profiles.yml         # Uses env_var() for portability
│   └── models/              # Bronze/Silver/Gold
└── dashboard/               # STREAMLIT APP
    └── app.py
```

## 4. Data Strategy (Medallion Architecture)

### A. Landing Zone (Raw Ingestion)
*   **Format:** Raw `CoverageJSON` (from KNMI API).
*   **Storage:** `s3://{BUCKET}/landing/source=knmi/type=hourly/station={id}/year={yyyy}/month={mm}/data.json`
*   **Logic:** Implemented in Dagster (`src/assets/ingestion.py`).
*   **Status:** ✅ COMPLETE.

### B. Bronze Layer (Structuring)
*   **Format:** **Apache Iceberg**.
*   **Library:** `dagster-iceberg` (using `PyArrowIcebergIOManager`) or `duckdb` with iceberg extension.
*   **Goal:** Flatten the nested JSON into a raw, structured table.
*   **Logic:**
    *   Asset `bronze_observations` depends on `knmi_hourly_observations`.
    *   Reads JSON from Landing Zone.
    *   Converts to `pyarrow.Table` (via DuckDB for speed).
    *   Writes to Iceberg Table `bronze_observations` via IO Manager.

### C. Silver Layer (Transformation)
*   **Format:** **Apache Iceberg**.
*   **Goal:** Cleaned, deduped, type-casted (Metadata driven).
*   **Logic:**
    1.  Fetch KNMI Metadata (Units, Parameters) to drive the schema.
    2.  Pivot parameters (`DD`, `FF`, `T`) into columns.
    3.  Enforce types (e.g., `wind_speed` -> `FLOAT`).

### D. Gold Layer (Marts)
*   **Format:** **Apache Iceberg**.
*   **Goal:** Aggregated Tables (Daily Averages, Storm Events) ready for BI.

---

## 5. Configuration & Environment
The AI must use `pydantic-settings` to load these.

**`.env` content:**
```bash
DATA_ROOT="s3://weather-lake"        # Swaps to gs:// in prod
KNMI_API_TOKEN="<YOUR_TOKEN>"
# MinIO Specifics (Optional in Prod)
ENDPOINT_URL="http://127.0.0.1:9000"
AWS_ACCESS_KEY_ID="admin" # Updated to ADM_TimoWag in local
AWS_SECRET_ACCESS_KEY="password" # Updated to ... in local
```

---

## 6. Implementation Plan (Execute in Order)

### **Step 1: The Smart Utility (`src/utils/smart_client.py`)** [COMPLETED]
*Goal: Abstract the complexity of S3 connections and API Retries.*

### **Step 2: Station Metadata Asset (`src/assets/metadata.py`)** [COMPLETED]
*Goal: The "Big Bang" that discovers stations.*

### **Step 3: Definitions & Dynamic Sensor (`src/definitions.py`)** [COMPLETED]
*Goal: Teach Dagster about the stations.*

### **Step 4: Landing Zone Asset (`src/assets/ingestion.py`)** [COMPLETED]
*Goal: The Data Pump (JSON).*

### **Step 5: Verify Dagster Architecture (`tests/verify_dagster_defs.py`)** [READY]
*Goal: Ensure the Graph is valid before building complex Iceberg logic.*
*   Run: `uv run python tests/verify_dagster_defs.py`
*   Checks: Asset loading, Partitions, Sensor registration.

### **Step 6: Bronze Layer (Iceberg Conversion) (`src/assets/bronze.py`)** [NEXT]
*Goal: Convert Landing JSONs to Bronze Iceberg Table.*
*   Install `dagster-iceberg` (and `pyiceberg`, `pyarrow`).
*   Configure `PyArrowIcebergIOManager` pointing to MinIO (S3) + Catalog (Sqlite or REST).
*   Create Asset that reads JSON -> Returns PyArrow Table -> Writes to Iceberg.

### **Step 7: The dbt Transformation (Silver/Gold)**
*   Use `dbt-duckdb` to query Bronze Iceberg tables and create Silver/Gold Iceberg tables.

---

## 7. Progress & Verification Log

### Phase 1: API & Ingestion (Verified 2025-11-24)
*   **API:** Verified `hourly-in-situ` collection and Long WIGOS IDs (`tests/manual_verification.py`).
*   **Ingestion:** Verified 10-year hourly fetch for De Bilt (`tests/test_hourly_10yr.py`).

### Phase 2: Dagster Architecture (Verified 2025-12-03)
*   **Docker:** Setup pure SQLite architecture (No Postgres).
*   **Definitions:** `src/definitions.py` implemented.
*   **Verification:** 
    *   Created and verified `tests/verify_dagster_defs.py`.
    *   Verified Dynamic Partitions population mechanism.
    *   Successfully ran partial backfill for 3 stations (Nov 2025).
