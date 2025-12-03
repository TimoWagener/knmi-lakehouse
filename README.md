# KNMI Lakehouse

A Vendor-Neutral, Single-Node Data Lakehouse for Dutch weather data analysis.

## Project Overview

This project ingests, transforms, and analyzes weather data from the KNMI (Royal Netherlands Meteorological Institute) API. It is designed to run locally using MinIO for storage and Dagster for orchestration, simulating a modern Data Lakehouse architecture (Medallion Architecture).

**Tech Stack:**
*   **Language:** Python 3.12+
*   **Dependency Manager:** `uv`
*   **Orchestrator:** Dagster
*   **Storage:** MinIO (S3 compatible)
*   **Compute:** DuckDB (planned)
*   **Table Format:** Apache Iceberg (planned)

## Getting Started

### Prerequisites

1.  **Docker Desktop**: Required for running MinIO (storage).
2.  **uv**: An extremely fast Python package installer and resolver.
    ```bash
    # Windows (PowerShell)
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

    # macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd knmi_lakehouse
    ```

2.  **Configure Environment:**
    Copy the template to a new `.env` file.
    ```bash
    cp .env.template .env
    ```
    Open `.env` and add your `KNMI_API_TOKEN`. You can obtain one from the [KNMI Developer Portal](https://developer.dataplatform.knmi.nl/).

3.  **Install Dependencies:**
    ```bash
    uv sync
    ```

## Running the Project

You can run the project in two modes: **Hybrid (Recommended for Dev)** or **Full Docker**.

### Mode A: Hybrid (Recommended for Development)
*MinIO runs in Docker, but Dagster runs natively on your machine for faster feedback.*

1.  **Start Infrastructure (MinIO Only):**
    ```bash
    docker-compose up -d minio
    ```

2.  **Run Dagster Locally:**
    ```bash
    # Starts the Dagster UI and Daemon
    uv run dagster dev
    ```

3.  **Access the UI:**
    Open [http://localhost:3000](http://localhost:3000) in your browser.

### Mode B: Full Docker
*Everything runs in containers.*

1.  **Start All Services:**
    ```bash
    docker-compose up -d
    ```
    *Note: This mounts your local `src/` directory, so code changes are reflected, but you may need to restart containers for dependency changes.*

2.  **Access the UI:**
    Open [http://localhost:3000](http://localhost:3000).

## Development & Verification

### Running Tests
Verify that your environment and code are working correctly:

```bash
# 1. Verify Dagster Definitions
uv run python tests/verify_dagster_defs.py

# 2. Test Data Ingestion (Fetches 10 years of data for one station)
uv run python tests/test_hourly_10yr.py

# 3. Run Unit/Integration Tests (if available)
uv run pytest
```

### Linting & Formatting
We use `ruff` for code quality.

```bash
uv run ruff check .
uv run ruff format .
```

## Directory Structure

*   `src/assets`: Dagster assets (Ingestion, Transformation).
*   `src/utils`: Shared utilities (S3 Client, API wrappers).
*   `tests/`: Verification scripts.
*   `minio_data/`: Local volume for MinIO storage (persists between restarts).
