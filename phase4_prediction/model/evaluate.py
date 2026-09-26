"""
evaluate.py — Phase 4: Model Evaluation
=========================================
Loads the trained model and features.csv, runs predictions on the test set,
and produces a detailed evaluation report with per-product and per-tier metrics.

Input:  data/features.csv
        artifacts/model.joblib
        artifacts/feature_cols.json
        artifacts/metrics.json

Output: artifacts/evaluation_report.csv   ← per-product metrics
        artifacts/evaluation_summary.json ← aggregate metrics
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

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
PLOTS_DIR     = ARTIFACTS_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET        = "Quantite_Totale"
TEST_MONTHS   = 3


# ── Load ────────────────────────────────────────────────────────────────────
def load_all():
    df = pd.read_csv(DATA_DIR / "features.csv", parse_dates=["Date_Periode"])
    df = df.sort_values(["ReferenceProduit", "Date_Periode"]).reset_index(drop=True)

    model = joblib.load(ARTIFACTS_DIR / "model.joblib")

    with open(ARTIFACTS_DIR / "feature_cols.json") as f:
        feature_cols = json.load(f)

    log.info("Loaded: %d rows | model: %s", len(df), type(model).__name__)
    return df, model, feature_cols


# ── Split (same logic as train.py) ─────────────────────────────────────────
def split(df: pd.DataFrame):
    cutoff = df["Date_Periode"].max() - pd.DateOffset(months=TEST_MONTHS - 1)
    train  = df[df["Date_Periode"] < cutoff].copy()
    test   = df[df["Date_Periode"] >= cutoff].copy()
    log.info(
        "Test set: %d rows | %s → %s",
        len(test),
        test["Date_Periode"].min().strftime("%Y-%m"),
        test["Date_Periode"].max().strftime("%Y-%m"),
    )
    return train, test


# ── Predict ─────────────────────────────────────────────────────────────────
def predict(model, test: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    X       = test[feature_cols]
    y_pred  = np.maximum(model.predict(X), 0)   # no negative predictions
    test    = test.copy()
    test["Quantite_Predite"] = y_pred
    test["Erreur_Absolue"]   = (test[TARGET] - test["Quantite_Predite"]).abs()
    test["Erreur_Relative"]  = np.where(
        test[TARGET] > 0,
        test["Erreur_Absolue"] / test[TARGET] * 100,
        np.nan,    # undefined when actual = 0
    )
    return test


# ── Aggregate metrics ───────────────────────────────────────────────────────
def aggregate_metrics(test: pd.DataFrame) -> dict:
    y_true = test[TARGET]
    y_pred = test["Quantite_Predite"]

    mae  = (test["Erreur_Absolue"]).mean()
    rmse = np.sqrt(((y_true - y_pred) ** 2).mean())

    # MAPE only on non-zero actuals
    mask = y_true > 0
    mape = test.loc[mask, "Erreur_Relative"].mean()

    # Median absolute error — more robust than MAE on skewed data
    medae = test["Erreur_Absolue"].median()

    log.info("── Aggregate metrics (test set) ──────────────────")
    log.info("MAE        : %.2f units", mae)
    log.info("Median AE  : %.2f units", medae)
    log.info("RMSE       : %.2f units", rmse)
    log.info("MAPE       : %.2f%% (non-zero actuals only)", mape)

    return {
        "mae": round(mae, 2),
        "median_ae": round(medae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
    }


# ── Per-confidence-tier metrics ─────────────────────────────────────────────
def tier_metrics(test: pd.DataFrame) -> pd.DataFrame:
    """
    Per tier: MAE, MedianAE, MAPE (non-zero only), nb products.
    MAPE per tier is more honest than MAE per tier for comparing tiers
    with very different sales volumes.
    """
    rows = []
    for tier, grp in test.groupby("Confiance_Donnees"):
        y_true = grp[TARGET]
        y_pred = grp["Quantite_Predite"]
        mask   = y_true > 0

        rows.append({
            "Tier":        tier,
            "Nb_Produits": grp["ReferenceProduit"].nunique(),
            "MAE":         round((grp["Erreur_Absolue"]).mean(), 2),
            "Median_AE":   round(grp["Erreur_Absolue"].median(), 2),
            "RMSE":        round(np.sqrt(((y_true - y_pred) ** 2).mean()), 2),
            "MAPE":        round(grp.loc[mask, "Erreur_Relative"].mean(), 2),
        })

    tiers_df = pd.DataFrame(rows).set_index("Tier")
    log.info("── Metrics by confidence tier ────────────────────")
    log.info("\n%s", tiers_df.to_string())
    return tiers_df


# ── Per-product metrics ──────────────────────────────────────────────────────
def per_product_metrics(test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ref, grp in test.groupby("ReferenceProduit"):
        y_true = grp[TARGET]
        y_pred = grp["Quantite_Predite"]
        mask   = y_true > 0

        rows.append({
            "ReferenceProduit":  ref,
            "DesignationProduit":grp["DesignationProduit"].iloc[0],
            "Confiance_Donnees": grp["Confiance_Donnees"].iloc[0],
            "Nb_Periodes_Test":  len(grp),
            "MAE":               round(grp["Erreur_Absolue"].mean(), 2),
            "Median_AE":         round(grp["Erreur_Absolue"].median(), 2),
            "MAPE":              round(grp.loc[mask, "Erreur_Relative"].mean(), 2) if mask.any() else None,
            "Quantite_Moy_Reelle":   round(y_true.mean(), 2),
            "Quantite_Moy_Predite":  round(y_pred.mean(), 2),
        })

    prod_df = (
        pd.DataFrame(rows)
        .sort_values("MAE", ascending=False)
        .reset_index(drop=True)
    )

    log.info("── Top 10 worst predicted products (by MAE) ──────")
    log.info("\n%s", prod_df.head(10)[
        ["ReferenceProduit", "DesignationProduit", "Confiance_Donnees", "MAE", "MAPE"]
    ].to_string(index=False))

    return prod_df


# ── Plots ────────────────────────────────────────────────────────────────────
def plot_actual_vs_predicted(test: pd.DataFrame) -> None:
    """Scatter plot: actual vs predicted quantity (test set)."""
    fig, ax = plt.subplots(figsize=(8, 6))

    colors = {"Haute": "#2ecc71", "Moyenne": "#f39c12", "Faible": "#e74c3c"}
    for tier, grp in test.groupby("Confiance_Donnees"):
        ax.scatter(
            grp[TARGET], grp["Quantite_Predite"],
            alpha=0.4, s=15,
            color=colors.get(tier, "grey"),
            label=tier,
        )

    lim = max(test[TARGET].max(), test["Quantite_Predite"].max()) * 1.05
    ax.plot([0, lim], [0, lim], "k--", linewidth=1, label="Parfait")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Quantité Réelle")
    ax.set_ylabel("Quantité Prédite")
    ax.set_title("Réel vs Prédit — Ensemble de test")
    ax.legend(title="Confiance")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    plt.tight_layout()
    path = PLOTS_DIR / "actual_vs_predicted.png"
    plt.savefig(path, dpi=150)
    plt.close()
    log.info("Plot saved → %s", path)


def plot_error_distribution(test: pd.DataFrame) -> None:
    """Histogram of absolute errors."""
    fig, ax = plt.subplots(figsize=(8, 5))
    errors = test["Erreur_Absolue"]
    p95    = errors.quantile(0.95)
    ax.hist(errors[errors <= p95], bins=50, color="#3498db", edgecolor="white", alpha=0.85)
    ax.set_xlabel("Erreur Absolue (unités)")
    ax.set_ylabel("Fréquence")
    ax.set_title("Distribution des erreurs absolues (95e percentile)")
    ax.axvline(errors.mean(),   color="red",    linestyle="--", label=f"MAE = {errors.mean():.0f}")
    ax.axvline(errors.median(), color="orange", linestyle="--", label=f"Médiane = {errors.median():.0f}")
    ax.legend()
    plt.tight_layout()
    path = PLOTS_DIR / "error_distribution.png"
    plt.savefig(path, dpi=150)
    plt.close()
    log.info("Plot saved → %s", path)


def plot_feature_importance(model) -> None:
    """Top 20 feature importances from the XGBoost model."""
    xgb_model  = model.named_steps["xgb"]
    importances = xgb_model.feature_importances_

    with open(ARTIFACTS_DIR / "feature_cols.json") as f:
        feature_cols = json.load(f)

    fi = (
        pd.Series(importances, index=feature_cols)
        .sort_values(ascending=True)
        .tail(20)
    )

    fig, ax = plt.subplots(figsize=(8, 7))
    fi.plot(kind="barh", ax=ax, color="#3498db", edgecolor="white")
    ax.set_title("Top 20 — Importance des variables (XGBoost)")
    ax.set_xlabel("Importance (gain)")
    plt.tight_layout()
    path = PLOTS_DIR / "feature_importance.png"
    plt.savefig(path, dpi=150)
    plt.close()
    log.info("Plot saved → %s", path)


def plot_tier_mape(tiers_df: pd.DataFrame) -> None:
    """Bar chart of MAPE per confidence tier."""
    fig, ax = plt.subplots(figsize=(6, 4))
    color_map = {"Haute": "#2ecc71", "Moyenne": "#f39c12", "Faible": "#e74c3c"}
    colors = [color_map[tier] for tier in tiers_df.index]
    tiers_df["MAPE"].plot(kind="bar", ax=ax, color=colors[:len(tiers_df)], edgecolor="white")
    ax.set_title("MAPE par tier de confiance")
    ax.set_ylabel("MAPE (%)")
    ax.set_xlabel("")
    ax.set_xticklabels(tiers_df.index, rotation=0)
    for i, v in enumerate(tiers_df["MAPE"]):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=10)
    plt.tight_layout()
    path = PLOTS_DIR / "mape_by_tier.png"
    plt.savefig(path, dpi=150)
    plt.close()
    log.info("Plot saved → %s", path)


# ── Save ────────────────────────────────────────────────────────────────────
def save(prod_df: pd.DataFrame, summary: dict, tiers_df: pd.DataFrame) -> None:
    prod_df.to_csv(ARTIFACTS_DIR / "evaluation_report.csv", index=False, encoding="utf-8-sig")
    log.info("Per-product report saved → %s", ARTIFACTS_DIR / "evaluation_report.csv")

    summary["tier_metrics"] = tiers_df.reset_index().to_dict(orient="records")
    with open(ARTIFACTS_DIR / "evaluation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log.info("Summary saved → %s", ARTIFACTS_DIR / "evaluation_summary.json")


# ── Main ────────────────────────────────────────────────────────────────────
def run():
    df, model, feature_cols = load_all()
    _, test                 = split(df)
    test                    = predict(model, test, feature_cols)
    summary                 = aggregate_metrics(test)
    tiers_df                = tier_metrics(test)
    prod_df                 = per_product_metrics(test)

    plot_actual_vs_predicted(test)
    plot_error_distribution(test)
    plot_feature_importance(model)
    plot_tier_mape(tiers_df)

    save(prod_df, summary, tiers_df)
    log.info("Evaluation complete.")


if __name__ == "__main__":
    run()