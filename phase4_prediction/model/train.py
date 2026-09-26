"""
train.py — Phase 4: Model Training
====================================
Reads features.csv and trains an XGBoost model using TimeSeriesSplit CV.
Saves the trained model and encoders to artifacts/.

Input:  data/features.csv
Output: artifacts/model.joblib
        artifacts/feature_cols.json
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import logging

from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
DATA_DIR      = Path(__file__).resolve().parent.parent / "data"
ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
INPUT_FILE    = DATA_DIR / "features.csv"

ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Columns used as model input features (excludes target, identifiers, metadata)
MODEL_FEATURES = [
    "Lag_1", "Lag_2", "Lag_3", "Lag_6", "Lag_12",
    "Rolling_Mean_3", "Rolling_Mean_6", "Rolling_Std_3", "Rolling_Max_3",
    "Trend_3M", "Trend_6M",
    "Mois_Sin", "Mois_Cos", "Est_Debut_Annee", "Est_Fin_Annee",
    "Famille_enc", "FormeGalenique_enc", "Activite_enc",
    "Remise_Moy_Pct", "Nb_Clients_Distincts",
    "CV_Quantite", "Pct_Periodes_Zero", "Lag12_Disponible",
    "Mois", "Trimestre", "Annee",
]

TARGET = "Quantite_Totale"


# ── Load ────────────────────────────────────────────────────────────────────
def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date_Periode"])
    df = df.sort_values(["ReferenceProduit", "Date_Periode"]).reset_index(drop=True)
    log.info("Loaded: %d rows, %d columns", len(df), len(df.columns))
    return df


# ── Train / test split ──────────────────────────────────────────────────────
def split(df: pd.DataFrame, test_months: int = 3):
    """
    Time-based split: last N months → test, everything before → train.
    Never use random split for time series — it leaks future data into training.
    """
    cutoff = df["Date_Periode"].max() - pd.DateOffset(months=test_months - 1)
    train  = df[df["Date_Periode"] < cutoff].copy()
    test   = df[df["Date_Periode"] >= cutoff].copy()
    log.info(
        "Train: %d rows (up to %s) | Test: %d rows (%s → %s)",
        len(train), cutoff.strftime("%Y-%m"),
        len(test),
        test["Date_Periode"].min().strftime("%Y-%m"),
        test["Date_Periode"].max().strftime("%Y-%m"),
    )
    return train, test


# ── Baseline model ──────────────────────────────────────────────────────────
def evaluate_baseline(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    """
    Naive baseline: predict last known value (Lag_1).
    XGBoost must beat this to justify using ML.
    """
    y_true = test[TARGET]
    y_pred = test["Lag_1"]

    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    # MAPE — skip rows where actual = 0 to avoid division by zero
    mask = y_true > 0
    mape = (((y_true[mask] - y_pred[mask]).abs() / y_true[mask]) * 100).mean()

    log.info("Baseline (Lag_1) — MAE: %.2f | RMSE: %.2f | MAPE: %.2f%%", mae, rmse, mape)
    return {"mae": mae, "rmse": rmse, "mape": mape}


# ── XGBoost training ────────────────────────────────────────────────────────
def train_xgboost(train: pd.DataFrame) -> Pipeline:
    """
    Train XGBoost with TimeSeriesSplit cross-validation and
    RandomizedSearchCV for hyperparameter tuning.
    """
    X_train = train[MODEL_FEATURES]
    y_train = train[TARGET]

    # TimeSeriesSplit — respects temporal order within training set
    tscv = TimeSeriesSplit(n_splits=5)

    xgb_model = xgb.XGBRegressor(
        objective    = "reg:squarederror",
        random_state = 42,
        n_jobs       = -1,
        verbosity    = 0,
    )

    param_dist = {
        "xgb__n_estimators":      [100, 200, 300, 500],
        "xgb__max_depth":         [3, 4, 5, 6],
        "xgb__learning_rate":     [0.01, 0.05, 0.1, 0.2],
        "xgb__subsample":         [0.7, 0.8, 0.9, 1.0],
        "xgb__colsample_bytree":  [0.7, 0.8, 0.9, 1.0],
        "xgb__min_child_weight":  [1, 3, 5, 7],
        "xgb__gamma":             [0, 0.1, 0.2, 0.5],
    }

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("xgb",    xgb_model),
    ])

    search = RandomizedSearchCV(
        estimator          = pipeline,
        param_distributions= param_dist,
        n_iter             = 30,         # 30 random combinations
        scoring            = "neg_mean_absolute_error",
        cv                 = tscv,
        random_state       = 42,
        n_jobs             = -1,
        verbose            = 1,
    )

    log.info("Starting RandomizedSearchCV (30 iterations × 5 folds) ...")
    search.fit(X_train, y_train)

    log.info("Best params: %s", search.best_params_)
    log.info("Best CV MAE: %.2f", -search.best_score_)

    return search.best_estimator_


# ── Evaluate on test set ────────────────────────────────────────────────────
def evaluate(model: Pipeline, test: pd.DataFrame, baseline: dict) -> dict:
    X_test = test[MODEL_FEATURES]
    y_true = test[TARGET]
    y_pred = model.predict(X_test)
    y_pred = np.maximum(y_pred, 0)   # predictions can't be negative

    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    mask = y_true > 0
    mape = (((y_true[mask] - y_pred[mask]) / y_true[mask]).abs() * 100).mean()

    log.info("XGBoost        — MAE: %.2f | RMSE: %.2f | MAPE: %.2f%%", mae, rmse, mape)
    log.info(
        "Improvement vs baseline — MAE: %.2f%% | RMSE: %.2f%%",
        (1 - mae  / baseline["mae"])  * 100,
        (1 - rmse / baseline["rmse"]) * 100,
    )

    # Per-confidence-tier breakdown
    test = test.copy()
    test["y_pred"] = y_pred
    test["abs_error"] = (test[TARGET] - test["y_pred"]).abs()

    log.info("MAE by confidence tier:")
    tier_mae = test.groupby("Confiance_Donnees")["abs_error"].mean()
    log.info("\n%s", tier_mae.to_string())

    return {
        "mae": mae, "rmse": rmse, "mape": mape,
        "baseline_mae": baseline["mae"],
        "improvement_pct": (1 - mae / baseline["mae"]) * 100,
    }


# ── Save artifacts ──────────────────────────────────────────────────────────
def save_artifacts(model: Pipeline, metrics: dict) -> None:
    # Model
    model_path = ARTIFACTS_DIR / "model.joblib"
    joblib.dump(model, model_path)
    log.info("Model saved → %s", model_path)

    # Feature column list — needed at inference time to guarantee column order
    features_path = ARTIFACTS_DIR / "feature_cols.json"
    with open(features_path, "w") as f:
        json.dump(MODEL_FEATURES, f, indent=2)
    log.info("Feature columns saved → %s", features_path)

    # Metrics
    metrics_path = ARTIFACTS_DIR / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({k: round(float(v), 4) for k, v in metrics.items()}, f, indent=2)
    log.info("Metrics saved → %s", metrics_path)


# ── Main ────────────────────────────────────────────────────────────────────
def run() -> Pipeline:
    df             = load(INPUT_FILE)
    train, test    = split(df, test_months=3)
    baseline       = evaluate_baseline(train, test)
    model          = train_xgboost(train)
    metrics        = evaluate(model, test, baseline)
    save_artifacts(model, metrics)
    return model


if __name__ == "__main__":
    model = run()
    log.info("Training complete.")