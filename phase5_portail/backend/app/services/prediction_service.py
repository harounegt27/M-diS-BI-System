import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.ml.model_loader import get_model
from datetime import datetime

def get_historique_produit(db: Session, reference: str) -> pd.DataFrame:
    rows = db.execute(text("""
        SELECT
            d.Annee,
            d.Mois,
            d.Trimestre,
            SUM(f.Quantite)          AS quantite,
            AVG(f.RemisePct)         AS remise_moy_pct,
            COUNT(DISTINCT f.ClientKey) AS nb_clients_distincts,
            p.Famille,
            p.FormeGalenique,
            p.Activite
        FROM Fait_Ventes f
        JOIN Dim_Produit p ON f.ProduitKey = p.ProduitKey
        JOIN Dim_Date d    ON f.DateKey    = d.DateKey
        WHERE p.ReferenceProduit = :ref
        GROUP BY d.Annee, d.Mois, d.Trimestre,
                 p.Famille, p.FormeGalenique, p.Activite
        ORDER BY d.Annee, d.Mois
    """), {"ref": reference}).fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([dict(r._mapping) for r in rows])
    df["date"] = pd.to_datetime(
        df["Annee"].astype(str) + "-" + df["Mois"].astype(str) + "-01"
    )
    df = df.sort_values("date").reset_index(drop=True)
    return df


def build_features(df: pd.DataFrame, target_annee: int, target_mois: int) -> dict:
    q = df["quantite"].values

    def lag(n):
        return float(q[-n]) if len(q) >= n else 0.0

    rolling3 = q[-3:] if len(q) >= 3 else q
    rolling6 = q[-6:] if len(q) >= 6 else q

    mois_sin = np.sin(2 * np.pi * target_mois / 12)
    mois_cos = np.cos(2 * np.pi * target_mois / 12)

    trend_3m = float(q[-1] - q[-3]) if len(q) >= 3 else 0.0
    trend_6m = float(q[-1] - q[-6]) if len(q) >= 6 else 0.0

    cv_quantite = float(np.std(q) / np.mean(q)) if np.mean(q) != 0 else 0.0
    pct_zero = float(np.sum(q == 0) / len(q)) if len(q) > 0 else 1.0

    # Encodage ordinal simple (ordre alphabétique stable)
    famille_vals = sorted(df["Famille"].dropna().unique().tolist())
    forme_vals   = sorted(df["FormeGalenique"].dropna().unique().tolist())
    activite_vals = sorted(df["Activite"].dropna().unique().tolist())

    famille     = df["Famille"].iloc[-1]
    forme       = df["FormeGalenique"].iloc[-1]
    activite    = df["Activite"].iloc[-1]

    return {
        "Lag_1":               lag(1),
        "Lag_2":               lag(2),
        "Lag_3":               lag(3),
        "Lag_6":               lag(6),
        "Lag_12":              lag(12),
        "Rolling_Mean_3":      float(np.mean(rolling3)),
        "Rolling_Mean_6":      float(np.mean(rolling6)),
        "Rolling_Std_3":       float(np.std(rolling3)),
        "Rolling_Max_3":       float(np.max(rolling3)),
        "Trend_3M":            trend_3m,
        "Trend_6M":            trend_6m,
        "Mois_Sin":            mois_sin,
        "Mois_Cos":            mois_cos,
        "Est_Debut_Annee":     1 if target_mois <= 2 else 0,
        "Est_Fin_Annee":       1 if target_mois >= 11 else 0,
        "Famille_enc":         famille_vals.index(famille) if famille in famille_vals else 0,
        "FormeGalenique_enc":  forme_vals.index(forme) if forme in forme_vals else 0,
        "Activite_enc":        activite_vals.index(activite) if activite in activite_vals else 0,
        "Remise_Moy_Pct":      float(df["remise_moy_pct"].iloc[-1] or 0),
        "Nb_Clients_Distincts": float(df["nb_clients_distincts"].iloc[-1]),
        "CV_Quantite":         cv_quantite,
        "Pct_Periodes_Zero":   pct_zero,
        "Lag12_Disponible":    1 if len(q) >= 12 else 0,
        "Mois":                target_mois,
        "Trimestre":           (target_mois - 1) // 3 + 1,
        "Annee":               target_annee,
    }


def get_confiance(df: pd.DataFrame) -> str:
    n = len(df)
    q = df["quantite"].values
    cv = float(np.std(q) / np.mean(q)) if np.mean(q) != 0 else 999
    pct_zero = float(np.sum(q == 0) / n) if n > 0 else 1.0

    if n >= 12 and cv < 0.5 and pct_zero < 0.1:
        return "Haute"
    elif n >= 6 and cv < 1.0 and pct_zero < 0.3:
        return "Moyenne"
    else:
        return "Faible"


from datetime import datetime

def predict(db: Session, reference: str, horizon: int = 3) -> list:
    df = get_historique_produit(db, reference)
    if df.empty:
        return []

    model     = get_model()
    confiance = get_confiance(df)

    # ── Point de départ = max(dernier mois historique, mois actuel) ──
    last_row   = df.iloc[-1]
    last_annee = int(last_row["Annee"])
    last_mois  = int(last_row["Mois"])

    now        = datetime.now()
    curr_annee = now.year
    curr_mois  = now.month

    # Si l'historique est en retard sur aujourd'hui → on part d'aujourd'hui
    if (last_annee, last_mois) < (curr_annee, curr_mois):
        start_annee = curr_annee
        start_mois  = curr_mois
    else:
        start_annee = last_annee
        start_mois  = last_mois

    NOM_MOIS = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
        5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
        9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
    }

    results = []
    df_sim  = df.copy()

    for i in range(horizon):
        next_mois  = start_mois + i + 1
        next_annee = start_annee + (next_mois - 1) // 12
        next_mois  = ((next_mois - 1) % 12) + 1

        features = build_features(df_sim, next_annee, next_mois)
        X        = pd.DataFrame([features])
        pred     = float(model.predict(X)[0])
        pred     = max(0, round(pred, 2))

        results.append({
            "mois":             f"{NOM_MOIS[next_mois]} {next_annee}",
            "quantite_predite": pred,
            "confiance":        confiance
        })

        new_row            = df_sim.iloc[-1].copy()
        new_row["Mois"]    = next_mois
        new_row["Annee"]   = next_annee
        new_row["quantite"] = pred
        df_sim = pd.concat([df_sim, new_row.to_frame().T], ignore_index=True)

    return results


def predict_all(db: Session, annee: int, mois: int) -> list:
    # Récupère tous les produits distincts ayant des ventes
    refs = db.execute(text("""
        SELECT DISTINCT p.ReferenceProduit, p.DesignationProduit, p.Famille
        FROM Dim_Produit p
        JOIN Fait_Ventes f ON f.ProduitKey = p.ProduitKey
    """)).fetchall()

    now = datetime.now()
    if (annee, mois) <= (now.year, now.month):
        annee = now.year
        mois  = now.month + 1
        if mois > 12:
            mois   = 1
            annee += 1

    model = get_model()
    results = []

    for r in refs:
        df = get_historique_produit(db, r.ReferenceProduit)
        if df.empty or len(df) < 3:
            continue

        confiance = get_confiance(df)
        features  = build_features(df, annee, mois)
        X         = pd.DataFrame([features])
        pred      = float(model.predict(X)[0])
        pred      = max(0, round(pred, 2))

        results.append({
            "reference_produit":  r.ReferenceProduit,
            "designation":        r.DesignationProduit,
            "famille":            r.Famille,
            "quantite_predite":   pred,
            "confiance":          confiance
        })

    # Tri décroissant par quantité prédite
    results.sort(key=lambda x: x["quantite_predite"], reverse=True)
    return results