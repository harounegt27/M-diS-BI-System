"""
predict.py — Phase 4: Inference Interface
==========================================
Clean prediction function called by Phase 5 (FastAPI).
Loads the trained model and returns a structured prediction
for a given product and future period.

Usage (standalone):
    python predict.py --ref PF013900028 --periode 2026-05

Usage (from FastAPI):
    from phase4_prediction.predict import predict_one, predict_all
"""

import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional
import logging

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATA_DIR      = BASE_DIR / "data"

MODEL_PATH    = ARTIFACTS_DIR / "model.joblib"
FEATURES_PATH = ARTIFACTS_DIR / "feature_cols.json"
DATA_PATH     = DATA_DIR / "features.csv"

TARGET = "Quantite_Totale"


# ── Load artifacts (cached at module level) ─────────────────────────────────
def _load_artifacts():
    model = joblib.load(MODEL_PATH)
    with open(FEATURES_PATH) as f:
        feature_cols = json.load(f)
    log.info("Artifacts loaded — model: %s | features: %d", type(model).__name__, len(feature_cols))
    return model, feature_cols


def _load_history() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["Date_Periode"])
    df = df.sort_values(["ReferenceProduit", "Date_Periode"]).reset_index(drop=True)
    log.info("History loaded: %d rows", len(df))
    return df


# ── Feature row builder ─────────────────────────────────────────────────────
def _build_feature_row(
    ref:         str,
    target_date: pd.Timestamp,
    history:     pd.DataFrame,
    feature_cols: list,
) -> Optional[pd.DataFrame]:
    """
    Given a product reference and a future period, build a single feature
    row using the product's historical data — exactly the same logic as
    engineer.py, applied at inference time for one future period.
    """
    prod_hist = (
        history[history["ReferenceProduit"] == ref]
        .sort_values("Date_Periode")
        .reset_index(drop=True)
    )

    if prod_hist.empty:
        log.warning("Product not found in history: %s", ref)
        return None

    qty = prod_hist["Quantite_Totale"].values

    def lag(n):
        """Quantity n months before target_date."""
        lag_date = target_date - pd.DateOffset(months=n)
        row = prod_hist[prod_hist["Date_Periode"] == lag_date]
        return float(row["Quantite_Totale"].values[0]) if not row.empty else 0.0

    def rolling_mean(n):
        vals = [lag(i) for i in range(1, n + 1)]
        return float(np.mean(vals))

    def rolling_std(n):
        vals = [lag(i) for i in range(1, n + 1)]
        return float(np.std(vals)) if len(vals) > 1 else 0.0

    def rolling_max(n):
        vals = [lag(i) for i in range(1, n + 1)]
        return float(np.max(vals))

    lag_1  = lag(1)
    lag_2  = lag(2)
    lag_3  = lag(3)
    lag_6  = lag(6)
    lag_12 = lag(12)

    rm3 = rolling_mean(3)
    rm6 = rolling_mean(6)

    # Check if lag_12 is from real data or imputed
    lag12_date = target_date - pd.DateOffset(months=12)
    lag12_disponible = int(not prod_hist[prod_hist["Date_Periode"] == lag12_date].empty)

    # Latest metadata row for static product features
    meta = prod_hist.iloc[-1]

    mois      = target_date.month
    trimestre = (mois - 1) // 3 + 1
    annee     = target_date.year

    row = {
        "Lag_1":               lag_1,
        "Lag_2":               lag_2,
        "Lag_3":               lag_3,
        "Lag_6":               lag_6,
        "Lag_12":              lag_12,
        "Rolling_Mean_3":      rm3,
        "Rolling_Mean_6":      rm6,
        "Rolling_Std_3":       rolling_std(3),
        "Rolling_Max_3":       rolling_max(3),
        "Trend_3M":            lag_1 - rm3,
        "Trend_6M":            lag_1 - rm6,
        "Mois_Sin":            float(np.sin(2 * np.pi * mois / 12)),
        "Mois_Cos":            float(np.cos(2 * np.pi * mois / 12)),
        "Est_Debut_Annee":     int(mois in [1, 2, 3]),
        "Est_Fin_Annee":       int(mois in [10, 11, 12]),
        "Famille_enc":         float(meta.get("Famille_enc", 0)),
        "FormeGalenique_enc":  float(meta.get("FormeGalenique_enc", 0)),
        "Activite_enc":        float(meta.get("Activite_enc", 0)),
        "Remise_Moy_Pct":      float(meta.get("Remise_Moy_Pct", 0)),
        "Nb_Clients_Distincts":float(meta.get("Nb_Clients_Distincts", 0)),
        "CV_Quantite":         float(meta.get("CV_Quantite", 0)),
        "Pct_Periodes_Zero":   float(meta.get("Pct_Periodes_Zero", 0)),
        "Lag12_Disponible":    lag12_disponible,
        "Mois":                mois,
        "Trimestre":           trimestre,
        "Annee":               annee,
    }

    return pd.DataFrame([row])[feature_cols]


# ── Confidence label ────────────────────────────────────────────────────────
def _get_confidence(ref: str, history: pd.DataFrame) -> str:
    row = history[history["ReferenceProduit"] == ref]
    if row.empty:
        return "Inconnue"
    return row["Confiance_Donnees"].iloc[0]


# ── Public API ──────────────────────────────────────────────────────────────
def predict_one(
    ref:      str,
    periode:  str,
    model=None,
    feature_cols=None,
    history: pd.DataFrame = None,
) -> dict:
    """
    Predict demand for a single (product, period) pair.

    Args:
        ref      : ReferenceProduit  e.g. "PF006100005"
        periode  : Target month      e.g. "2026-05"
        model, feature_cols, history: pass pre-loaded objects to avoid
                                      reloading on every call (FastAPI use)

    Returns:
        {
            "ReferenceProduit":   "PF006100005",
            "Periode":            "2026-05",
            "Quantite_Predite":   1240,
            "Confiance_Donnees":  "Haute",
            "Lag_1":              1180.0,
            "Rolling_Mean_6":     1205.0,
        }
    """
    if model is None or feature_cols is None:
        model, feature_cols = _load_artifacts()
    if history is None:
        history = _load_history()

    target_date = pd.Timestamp(periode + "-01")
    feature_row = _build_feature_row(ref, target_date, history, feature_cols)

    if feature_row is None:
        return {
            "ReferenceProduit":  ref,
            "Periode":           periode,
            "Quantite_Predite":  None,
            "Confiance_Donnees": "Inconnue",
            "Erreur":            f"Produit {ref} non trouvé dans l'historique.",
        }

    raw_pred = float(model.predict(feature_row)[0])
    pred     = max(round(raw_pred), 0)      # no negative, round to nearest unit
    confiance = _get_confidence(ref, history)

    result = {
        "ReferenceProduit":    ref,
        "Periode":             periode,
        "Quantite_Predite":    pred,
        "Confiance_Donnees":   confiance,
        "Lag_1":               float(feature_row["Lag_1"].values[0]),
        "Rolling_Mean_6":      float(feature_row["Rolling_Mean_6"].values[0]),
    }

    log.info(
        "[%s] %s → %d unités | Confiance: %s",
        periode, ref, pred, confiance,
    )
    return result


def predict_all(
    periode:  str,
    model=None,
    feature_cols=None,
    history: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Predict demand for ALL products for a given future period.
    Returns a DataFrame sorted by predicted quantity descending.

    This is the main output used by the Phase 5 dashboard.
    """
    if model is None or feature_cols is None:
        model, feature_cols = _load_artifacts()
    if history is None:
        history = _load_history()

    all_products = history["ReferenceProduit"].unique()
    log.info("Predicting %d products for period %s ...", len(all_products), periode)

    results = []
    for ref in all_products:
        r = predict_one(ref, periode, model, feature_cols, history)
        # Attach designation for readability
        meta = history[history["ReferenceProduit"] == ref]
        if not meta.empty:
            r["DesignationProduit"] = meta["DesignationProduit"].iloc[0] if "DesignationProduit" in meta.columns else ""
            r["Famille"] = meta["Famille_enc"].iloc[0] if "Famille_enc" in meta.columns else ""
        results.append(r)

    df = (
        pd.DataFrame(results)
        .sort_values("Quantite_Predite", ascending=False)
        .reset_index(drop=True)
    )

    log.info("predict_all complete — %d products predicted", len(df))
    return df


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse, json as _json

    parser = argparse.ArgumentParser(description="Phase 4 — Inference")
    parser.add_argument("--ref",     type=str, help="ReferenceProduit (single product)")
    parser.add_argument("--periode", type=str, required=True, help="Target period e.g. 2026-05")
    parser.add_argument("--all",     action="store_true", help="Predict all products")
    args = parser.parse_args()

    model, feature_cols = _load_artifacts()
    history             = _load_history()

    if args.all:
        df = predict_all(args.periode, model, feature_cols, history)
        print(df[["ReferenceProduit", "DesignationProduit", "Quantite_Predite",
                   "Confiance_Donnees", "Famille"]].to_string(index=False))
        df.to_csv(BASE_DIR / "data" / f"predictions_{args.periode}.csv",
                  index=False, encoding="utf-8-sig")
        log.info("Saved → data/predictions_%s.csv", args.periode)

    elif args.ref:
        result = predict_one(args.ref, args.periode, model, feature_cols, history)
        print(_json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()