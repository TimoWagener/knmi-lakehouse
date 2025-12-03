# KNMI Lakehouse Project

## Project Overview
This project is a **Vendor-Neutral, Single-Node Data Lakehouse** designed to analyze Dutch weather data (KNMI). It adheres to a "Write Once, Run Anywhere" philosophy, capable of running locally (MinIO) or on Google Cloud (GCS) by changing only environment variables.

**Core Technologies:**
*   **Environment:** `uv` (Dependency Management)
*   **Orchestrator:** Dagster (Asset-aware, Dynamic Partitions)
*   **Compute:** DuckDB (In-process OLAP)
*   **Table Format:** Apache Iceberg
*   **Storage:** MinIO (Local S3) / GCS
*   **Transformation:** dbt
*   **Visualization:** Streamlit

## Architecture
The project follows a "Strict Medallion" architecture:
1.  **Landing Zone:** Raw `CoverageJSON` from KNMI API stored in S3.
2.  **Bronze Layer:** Raw data converted to Apache Iceberg tables.
3.  **Silver Layer:** Cleaned, deduped, and typed data (Iceberg).
4.  **Gold Layer:** Aggregated marts for BI (Iceberg).

## Directory Structure
```text
knmi_lakehouse/
├── .env                     # Secrets (Excluded from Git)
├── pyproject.toml           # uv dependencies
├── docker-compose.yaml      # MinIO + Dagster Webserver + Daemon
├── dagster.yaml             # Configured for SQLite system storage
├── src/                     # DAGSTER CODEBASE
│   ├── definitions.py       # Job/Schedule/Sensor wiring
│   ├── partitions.py        # Shared Partition Definitions
│   ├── assets/
│   │   ├── metadata.py      # Station Discovery
│   │   ├── ingestion.py     # Landing Zone Data Pump
│   │   └── bronze.py        # Bronze Layer (Next Implementation)
│   └── utils/
│       └── smart_client.py  # Shared API & S3 Logic
└── tests/                   # Verification scripts
```

## Building and Running

### Prerequisites
*   **uv:** `pip install uv`
*   **Docker:** Ensure Docker Desktop is running.

### Key Commands

**1. Start Infrastructure (MinIO + Dagster UI)**
```bash
docker-compose up -d
```

**2. Run Dagster Locally (Development)**
This starts the Dagster UI and Daemon for development, allowing hot-reloading of code in `src/`.
```bash
dagster dev
```

**3. Run Tests/Verification**
```bash
# Verify Dagster definitions are valid
uv run python tests/verify_dagster_defs.py

# Verify Data Ingestion (10-year fetch)
uv run python tests/test_hourly_10yr.py
```

**4. Linting**
```bash
uv run ruff check .
```

## Development Conventions
*   **Dependency Management:** Always use `uv add <package>` or `uv run <script>`. Do not use `pip` or `poetry` directly.
*   **Storage:** **NEVER** write data to the local filesystem. All data persistence must go through `src/utils/smart_client.py` (or compatible libraries) to S3/MinIO.
*   **Configuration:** Use `pydantic-settings` to load configuration from `.env`.
*   **Code Quality:** Adhere to `ruff` linting standards.
*   **Dagster:** Use Software-Defined Assets (SDAs) and Dynamic Partitions for scalability.

## Current Status (as of Dec 3, 2025)
*   **Completed:** Project init, `uv` setup, MinIO/Dagster infra, Station Discovery (`metadata.py`), Landing Zone Ingestion (`ingestion.py`).
*   **Verified:** 
    *   Dagster Daemon & Sensors operational.
    *   Dynamic Partitions population.
    *   Partial backfill (Landing Zone) successfully tested.
*   **Next Steps:** Implement Bronze Layer (`src/assets/bronze.py`) to convert JSON to Iceberg.
