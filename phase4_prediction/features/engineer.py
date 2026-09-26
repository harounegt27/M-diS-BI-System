"""
engineer.py — Phase 4: Feature Engineering
===========================================
Reads monthly_sales.csv produced by extract.py and builds the full
feature matrix ready for XGBoost training.

Input:  data/monthly_sales.csv
Output: data/features.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
DATA_DIR    = Path(__file__).resolve().parent.parent / "data"
INPUT_FILE  = DATA_DIR / "monthly_sales.csv"
OUTPUT_FILE = DATA_DIR / "features.csv"


# ── Load ────────────────────────────────────────────────────────────────────
def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date_Periode"])
    df = df.sort_values(["ReferenceProduit", "Date_Periode"]).reset_index(drop=True)
    log.info("Loaded: %d rows, %d columns", len(df), len(df.columns))
    return df


# ── 1. Lag features ─────────────────────────────────────────────────────────
def add_lags(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Computing lag features ...")
    for lag in [1, 2, 3, 6, 12]:
        df[f"Lag_{lag}"] = (
            df.groupby("ReferenceProduit")["Quantite_Totale"]
            .shift(lag)
        )
    return df


# ── 2. Rolling statistics ───────────────────────────────────────────────────
def add_rolling(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Computing rolling statistics ...")
    grp = df.groupby("ReferenceProduit")["Quantite_Totale"]

    # shift(1) so we never include the current period in the window
    df["Rolling_Mean_3"] = grp.shift(1).rolling(3).mean().reset_index(level=0, drop=True)
    df["Rolling_Mean_6"] = grp.shift(1).rolling(6).mean().reset_index(level=0, drop=True)
    df["Rolling_Std_3"]  = grp.shift(1).rolling(3).std().reset_index(level=0, drop=True)
    df["Rolling_Max_3"]  = grp.shift(1).rolling(3).max().reset_index(level=0, drop=True)

    return df


# ── 3. Trend & momentum ─────────────────────────────────────────────────────
def add_trend(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Computing trend features ...")
    df["Trend_3M"] = df["Lag_1"] - df["Rolling_Mean_3"]
    df["Trend_6M"] = df["Lag_1"] - df["Rolling_Mean_6"]
    return df


# ── 4. Time features ────────────────────────────────────────────────────────
def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Computing time features ...")

    # Cyclical encoding — tells the model Dec and Jan are adjacent
    df["Mois_Sin"] = np.sin(2 * np.pi * df["Mois"] / 12)
    df["Mois_Cos"] = np.cos(2 * np.pi * df["Mois"] / 12)

    df["Est_Debut_Annee"] = df["Mois"].isin([1, 2, 3]).astype(int)
    df["Est_Fin_Annee"]   = df["Mois"].isin([10, 11, 12]).astype(int)

    return df


# ── 5. Target encoding for categorical columns ──────────────────────────────
def add_target_encodings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Target encoding: replace each category with the mean Quantite_Totale
    for that category, computed on the FULL dataset.

    In a production setting this should be computed on the training set only
    to avoid leakage — here we compute globally since this is a batch offline
    pipeline. The train.py script will recompute on the training fold.
    """
    log.info("Computing target encodings ...")

    global_mean = df["Quantite_Totale"].mean()

    for col, out_col in [
        ("Famille",        "Famille_enc"),
        ("FormeGalenique", "FormeGalenique_enc"),
        ("Activite",       "Activite_enc"),
    ]:
        mapping = (
            df.groupby(col)["Quantite_Totale"]
            .mean()
            .fillna(global_mean)
        )
        df[out_col] = df[col].map(mapping).fillna(global_mean)

    return df


# ── 6. Lag availability flag ─────────────────────────────────────────────────
def add_lag_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag whether the 12-month lag is real or imputed.
    Allows the model to down-weight predictions based on imputed history.
    """
    df["Lag12_Disponible"] = df["Lag_12"].notna().astype(int)
    return df


# ── 7. Fill NaNs from lags/rolling ──────────────────────────────────────────
def fill_nans(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill NaN lag/rolling values with 0.
    Products with short history will have NaNs in early periods —
    treating them as 0 is consistent with fill_missing_periods() in extract.py.
    """
    lag_rolling_cols = [c for c in df.columns if c.startswith(("Lag_", "Rolling_", "Trend_"))]
    df[lag_rolling_cols] = df[lag_rolling_cols].fillna(0)
    log.info("NaNs filled with 0 for %d lag/rolling columns", len(lag_rolling_cols))
    return df


# ── 8. Final column selection ───────────────────────────────────────────────
FEATURE_COLS = [
    # Target
    "Quantite_Totale",

    # Identifiers (not used as model features, kept for traceability)
    "ReferenceProduit",
    "DesignationProduit",
    "Date_Periode",
    "Annee",
    "Mois",
    "Trimestre",

    # Lag features
    "Lag_1", "Lag_2", "Lag_3", "Lag_6", "Lag_12",

    # Rolling stats
    "Rolling_Mean_3", "Rolling_Mean_6", "Rolling_Std_3", "Rolling_Max_3",

    # Trend
    "Trend_3M", "Trend_6M",

    # Time features
    "Mois_Sin", "Mois_Cos", "Est_Debut_Annee", "Est_Fin_Annee",

    # Product encodings
    "Famille_enc", "FormeGalenique_enc", "Activite_enc",

    # Carry-forward from extract
    "Remise_Moy_Pct",
    "Nb_Clients_Distincts",
    "CV_Quantite",
    "Pct_Periodes_Zero",
    "Lag12_Disponible",

    # Metadata (kept for confidence output, not used as training features)
    "Confiance_Donnees",
    "Nb_Periodes_Historique",
]


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    available = [c for c in FEATURE_COLS if c in df.columns]
    missing   = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        log.warning("Columns not found, skipped: %s", missing)
    return df[available]


# ── Save ────────────────────────────────────────────────────────────────────
def save(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    log.info("Saved → %s  (%d rows, %d columns)", path, len(df), len(df.columns))


# ── Main ────────────────────────────────────────────────────────────────────
def run() -> pd.DataFrame:
    df = load(INPUT_FILE)
    df = add_lags(df)
    df = add_rolling(df)
    df = add_trend(df)
    df = add_time_features(df)
    df = add_target_encodings(df)
    df = add_lag_flags(df)
    df = fill_nans(df)
    df = select_columns(df)

    save(df, OUTPUT_FILE)
    return df


if __name__ == "__main__":
    df = run()
    print("\nSample output:")
    print(df.head(5).to_string(index=False))
    print(f"\nShape: {df.shape}")
    print(f"\nFeature columns ({len(df.columns)}):")
    print(df.columns.tolist())
    print(f"\nNaN count per column:")
    print(df.isnull().sum()[df.isnull().sum() > 0].to_string())