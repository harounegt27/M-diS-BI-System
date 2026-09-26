# MédiS BI System

An end-to-end Business Intelligence system built during a 4th-year engineering internship. The project covers the full data pipeline — from raw Excel sources through a SQL Server data warehouse, Power BI dashboards, an XGBoost sales prediction model, a FastAPI + React web portal, and automated ETL execution via SQL Server Agent.

---

## Architecture

```
Excel Sources (Client, Produit, Vente)
        │
        ▼
  ETL Pipeline (SSIS / SSDT)
        │
        ▼
  SQL Server Data Warehouse (Star Schema)
        │
        ├──────────────────────┐
        ▼                      ▼
  Power BI Dashboards    XGBoost Prediction Model
  (Microsoft Fabric)           │
                               ▼
                        FastAPI Backend
                               │
                               ▼
                        React Frontend Portal
        │
        ▼
  SQL Server Agent (ETL Automation)
```

---

## Project Phases

### Phase 1 — Data Comprehension & Profiling
Explored and profiled three Excel source files (Client, Produit, Vente) using Python/pandas. Documented data quality issues, field semantics, and business logic ambiguities before any transformation was applied.

### Phase 2 — ETL Pipeline & Data Warehouse
Designed and implemented a star-schema data warehouse on SQL Server using SSIS/SSDT (Visual Studio, 32-bit mode). The schema includes `Dim_Produit`, `Dim_Client`, `Dim_Date`, and `Fait_Ventes` (~292,600 rows, 633 products). ETL packages handle type casting, deduplication, surrogate key assignment, and incremental loading.

### Phase 3 — Power BI Dashboards
Built interactive dashboards covering sales KPIs, client segmentation, and product performance. Published via Microsoft Fabric "Publish to Web" and connected through an on-premises data gateway for live data refresh.

### Phase 4 — Sales Prediction Model (`PHASE4_PREDICTION/`)
Trained an XGBoost regression model to forecast monthly sales per product. Pipeline includes:
- **`data/extract.py`** — pulls and aggregates data from the data warehouse into a clean monthly time series
- **`features/engineer.py`** — builds lag features, rolling statistics, and confidence tiers per product
- **`model/train.py`** — trains and tunes the XGBoost model with MLflow tracking
- **`model/evaluate.py`** — evaluates performance and generates metrics artifacts
- **`predict.py`** — runs inference for on-demand or batch predictions

Model artifacts (metrics, feature columns, serialized model) are stored under `artifacts/`.

### Phase 5 — BI Web Portal (`PHASE5_PORTAIL/`)
A full-stack web portal providing a unified interface for all BI outputs.

**Backend (FastAPI):**
- Live KPI endpoints (revenue, volume, top products, client counts)
- Paginated product and client tables with detail drawers
- On-demand XGBoost predictions — per product and global across all products
- Power BI report embedding via Microsoft Fabric iframe
- SQLAlchemy + pyodbc connection to the SQL Server data warehouse

**Frontend (React 18 + Vite + TailwindCSS):**
- Live KPI cards and CA evolution chart (Recharts)
- Embedded Power BI dashboards
- Paginated product/client tables with drawer panels
- On-demand prediction UI with per-product and global modes

### Phase 6 — ETL Automation
Automated the full ETL pipeline execution using SQL Server Agent. Scheduled jobs run the SSIS packages on a recurring basis, replacing manual execution and ensuring the data warehouse stays up to date without intervention.

### Phase 7 — Report
A full technical report written in LaTeX documenting all seven phases, including the architecture, design decisions, problems encountered, and their resolutions.

---

## Stack

| Layer | Technology |
|---|---|
| Data Sources | Excel (Client, Produit, Vente) |
| ETL | SSIS / SSDT (Visual Studio) |
| Data Warehouse | SQL Server, SSMS |
| Dashboards | Power BI Desktop, Microsoft Fabric |
| Prediction | Python, XGBoost, scikit-learn, MLflow |
| Backend | FastAPI, SQLAlchemy, pyodbc |
| Frontend | React 18, Vite, TailwindCSS, Recharts |
| Automation | SQL Server Agent |
| Report | LaTeX |

---

## Repository Structure

```
├── PHASE4_PREDICTION/
│   ├── artifacts/          # Model metrics, feature columns, serialized model, plots
│   ├── data/               # extract.py (data/monthly_sales.csv excluded — real data)
│   ├── features/           # engineer.py — feature engineering pipeline
│   ├── model/              # train.py, evaluate.py
│   └── predict.py          # Inference entry point
│
└── PHASE5_PORTAIL/
    ├── backend/
    │   ├── app/
    │   │   ├── core/       # config.py — settings via environment variables
    │   │   ├── db/         # database.py — SQLAlchemy engine and session
    │   │   ├── ml/         # model loading and inference
    │   │   ├── routers/    # FastAPI route handlers
    │   │   ├── schemas/    # Pydantic request/response models
    │   │   └── services/   # Business logic (clients, produits, ventes, prediction)
    │   ├── Dockerfile
    │   └── requirements.txt
    ├── frontend/
    │   ├── src/            # React components, pages, hooks
    │   ├── Dockerfile
    │   └── nginx.conf
    └── docker-compose.yml
```

---

## Setup

### Phase 4 — Prediction Model

```bash
cd PHASE4_PREDICTION
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file at the root (see `.env.example`):
```
DW_SQL_SERVER=your_server_name
DW_DATABASE=your_database_name
DW_ODBC_DRIVER=ODBC Driver 17 for SQL Server
```

Run the pipeline:
```bash
python data/extract.py          # Extract from data warehouse
python features/engineer.py     # Feature engineering
python model/train.py           # Train the model
python model/evaluate.py        # Evaluate performance
python predict.py               # Run predictions
```

### Phase 5 — Web Portal

```bash
cd PHASE5_PORTAIL
```

Create a `.env` file inside `backend/` (see `.env.example`):
```
DB_SERVER=your_server_name
DB_DATABASE=your_database_name
DB_DRIVER=ODBC Driver 17 for SQL Server
MODEL_PATH=app/ml/model_xgboost.json
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Or run both with Docker Compose:
```bash
docker-compose up --build
```

> **Note:** The portal connects to a local SQL Server instance via Windows Authentication (trusted connection). Docker deployment requires the host SQL Server to be reachable from the container network.

---

## Data Privacy

Raw source data (Excel files, extracted CSVs, evaluation reports) are excluded from this repository via `.gitignore`. The code is published for portfolio and academic purposes only.
