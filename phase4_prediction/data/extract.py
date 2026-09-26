"""
extract.py — Phase 4: Sales Prediction Model
=============================================
Pulls data from DW_Medis (SQL Server) and produces a clean monthly
aggregated DataFrame ready for feature engineering.

Source tables used:
  - Fait_Ventes  → VenteKey, Quantite, PrixVente, MontantTotalVente, RemisePct, TypeMouvement
  - Dim_Produit  → ReferenceProduit, DesignationProduit, Famille, FormeGalenique, Activite
  - Dim_Client   → Type, Marche, Type_Transaction
  - Dim_Date     → Annee, Mois, Trimestre, DateComplete

Output: data/monthly_sales.csv  ← one row per (ReferenceProduit, Annee, Mois)
"""

import pandas as pd
import sqlalchemy as sa
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
SQL_SERVER  = "DESKTOP-R3PHCES"
DATABASE    = "DW_Medis"
DRIVER      = "ODBC Driver 17 for SQL Server"

OUTPUT_DIR  = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "monthly_sales.csv"

EXCLUDE_AVOIR        = True   # remove returns (Quantite < 0)
EXCLUDE_INTERCOMPANY = True   # remove INTERCO rows (pending Zied confirmation)


# ── DB connection ───────────────────────────────────────────────────────────
def get_engine() -> sa.Engine:
    conn_str = (
        f"mssql+pyodbc://@{SQL_SERVER}/{DATABASE}"
        f"?driver={DRIVER.replace(' ', '+')}&trusted_connection=yes"
    )
    engine = sa.create_engine(conn_str, fast_executemany=True)
    log.info("Engine created → %s / %s", SQL_SERVER, DATABASE)
    return engine


# ── Raw extraction query ────────────────────────────────────────────────────
RAW_QUERY = """
SELECT
    fv.VenteKey,
    fv.Societe,
    fv.PrixVente,
    fv.Quantite,
    fv.MontantTotalVente,
    fv.MontantTheorique,
    fv.RemiseMontant,
    fv.RemisePct,
    fv.TypeMouvement,
    dp.ProduitKey,
    dp.ReferenceProduit,
    dp.DesignationProduit,
    dp.Famille,
    dp.Forme,
    dp.Activite,
    dp.FormeGalenique,
    dp.Coef,
    dc.ClientKey,
    dc.CodeClient,
    dc.Type,
    dc.Marche,
    dc.Pays,
    dc.Region,
    dc.Type_Transaction,
    dd.DateKey,
    dd.DateComplete,
    dd.Jour,
    dd.Mois,
    dd.Trimestre,
    dd.Annee
FROM
    dbo.Fait_Ventes      fv
    JOIN dbo.Dim_Produit dp ON fv.ProduitKey = dp.ProduitKey
    JOIN dbo.Dim_Client  dc ON fv.ClientKey  = dc.ClientKey
    JOIN dbo.Dim_Date    dd ON fv.DateKey    = dd.DateKey
"""


def extract_raw(engine: sa.Engine) -> pd.DataFrame:
    log.info("Extracting raw sales from Fait_Ventes ...")
    df = pd.read_sql(RAW_QUERY, engine)
    log.info("Raw rows extracted: %d", len(df))
    return df


# ── Filtering ───────────────────────────────────────────────────────────────
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    original = len(df)

    if EXCLUDE_AVOIR:
        df = df[df["Quantite"] > 0].copy()
        log.info("After AVOIR filter: %d rows (removed %d)", len(df), original - len(df))

    if EXCLUDE_INTERCOMPANY and "Type_Transaction" in df.columns:
        before = len(df)
        df = df[~df["Type_Transaction"].str.upper().isin(["ICO TN", "ICO SN"])].copy()
        log.info("After INTERCO filter: %d rows (removed %d)", len(df), before - len(df))

    return df


# ── Monthly aggregation ─────────────────────────────────────────────────────
def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Aggregating to monthly granularity ...")

    agg = (
        df.groupby(
            [
                "ReferenceProduit",
                "DesignationProduit",
                "Famille",
                "FormeGalenique",
                "Activite",
                "Annee",
                "Mois",
                "Trimestre",
            ],
            as_index=False,
        )
        .agg(
            Quantite_Totale      = ("Quantite",          "sum"),
            CA_Total             = ("MontantTotalVente",  "sum"),
            Remise_Moy_Pct       = ("RemisePct",          "mean"),
            Nb_Factures          = ("VenteKey",           "nunique"),
            Nb_Clients_Distincts = ("ClientKey",          "nunique"),
        )
    )

    agg["Date_Periode"] = pd.to_datetime(
        agg["Annee"].astype(str) + "-" + agg["Mois"].astype(str).str.zfill(2)
    )
    agg = agg.sort_values(["ReferenceProduit", "Date_Periode"]).reset_index(drop=True)

    log.info("Monthly rows after aggregation: %d", len(agg))
    return agg


# ── Complete time index per product ─────────────────────────────────────────
def fill_missing_periods(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Filling missing periods with zero ...")

    all_periods = pd.date_range(
        start=df["Date_Periode"].min(),
        end=df["Date_Periode"].max(),
        freq="MS",
    )

    products_meta = (
        df[["ReferenceProduit", "DesignationProduit", "Famille", "FormeGalenique", "Activite"]]
        .drop_duplicates("ReferenceProduit")
    )

    cross_index = pd.MultiIndex.from_product(
        [products_meta["ReferenceProduit"].values, all_periods],
        names=["ReferenceProduit", "Date_Periode"],
    )
    full_grid = pd.DataFrame(index=cross_index).reset_index()

    merged = full_grid.merge(
        df.drop(columns=["DesignationProduit", "Famille", "FormeGalenique", "Activite"], errors="ignore"),
        on=["ReferenceProduit", "Date_Periode"],
        how="left",
    ).merge(products_meta, on="ReferenceProduit", how="left")

    num_cols = ["Quantite_Totale", "CA_Total", "Remise_Moy_Pct", "Nb_Factures", "Nb_Clients_Distincts"]
    merged[num_cols] = merged[num_cols].fillna(0)

    merged["Annee"]     = merged["Date_Periode"].dt.year
    merged["Mois"]      = merged["Date_Periode"].dt.month
    merged["Trimestre"] = merged["Date_Periode"].dt.quarter

    merged = merged.sort_values(["ReferenceProduit", "Date_Periode"]).reset_index(drop=True)
    log.info("Rows after filling missing periods: %d", len(merged))
    return merged


# ── History depth & confidence tier ─────────────────────────────────────────
def add_history_stats(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Computing history stats per product ...")

    stats = (
        df.groupby("ReferenceProduit")
        .agg(
            Nb_Periodes_Historique = ("Quantite_Totale", lambda s: (s > 0).sum()),
            Mean_Quantite          = ("Quantite_Totale", "mean"),
            Std_Quantite           = ("Quantite_Totale", "std"),
            Pct_Periodes_Zero      = ("Quantite_Totale", lambda s: (s == 0).mean()),
        )
        .reset_index()
    )

    stats["CV_Quantite"] = (
        stats["Std_Quantite"] / stats["Mean_Quantite"].replace(0, float("nan"))
    ).fillna(0)

    def assign_confidence(row):
        if (
            row["Nb_Periodes_Historique"] >= 12
            and row["CV_Quantite"] < 0.5
            and row["Pct_Periodes_Zero"] < 0.3
        ):
            return "Haute"
        elif (
            row["Nb_Periodes_Historique"] >= 6
            and row["CV_Quantite"] < 1.0
            and row["Pct_Periodes_Zero"] < 0.5
        ):
            return "Moyenne"
        else:
            return "Faible"

    stats["Confiance_Donnees"] = stats.apply(assign_confidence, axis=1)

    df = df.merge(
        stats[["ReferenceProduit", "Nb_Periodes_Historique",
               "CV_Quantite", "Pct_Periodes_Zero", "Confiance_Donnees"]],
        on="ReferenceProduit",
        how="left",
    )

    dist = df.drop_duplicates("ReferenceProduit")["Confiance_Donnees"].value_counts()
    log.info("Confidence distribution:\n%s", dist.to_string())
    return df


# ── Save ────────────────────────────────────────────────────────────────────
def save(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    log.info("Saved → %s  (%d rows, %d columns)", path, len(df), len(df.columns))


# ── Fallback: load from Excel directly (dev/offline mode) ───────────────────
def extract_from_excel(
    vente_path:   str = "Class_Vente.xlsx",
    produit_path: str = "Class_Produit.xlsx",
    client_path:  str = "Class_Client.xlsx",
) -> pd.DataFrame:
    log.info("OFFLINE MODE — loading from Excel files ...")

    df_v = pd.read_excel(vente_path)
    df_p = pd.read_excel(produit_path)
    df_c = pd.read_excel(client_path)

    df_v = df_v.rename(columns={
        "Quantité":            "Quantite",
        "Reference_Produit":   "ReferenceProduit",
        "Code_Client":         "CodeClient",
        "Numéro_Facture":      "VenteKey",
        "Prix_Vente":          "PrixVente",
        "Montant_Total_Vente": "MontantTotalVente",
        "Societe":             "Societe",
    })
    df_v["RemisePct"]       = 0.0
    df_v["RemiseMontant"]   = 0.0
    df_v["MontantTheorique"]= df_v["MontantTotalVente"]
    df_v["TypeMouvement"]   = "VENTE"
    df_v["Type_Transaction"]= "NORMAL"

    df_p = df_p.rename(columns={
        "Reference Produit":   "ReferenceProduit",
        "Desgination Produit": "DesignationProduit",
        "Forme_galenique":     "FormeGalenique",
    })

    df_c = df_c.rename(columns={
        "CodeClient": "CodeClient",
        "Type":       "Type",
        "Marche":     "Marche",
    })
    df_c["Type_Transaction"] = "NORMAL"
    df_c["ClientKey"]        = range(len(df_c))

    df = df_v.merge(
        df_p[["ReferenceProduit", "DesignationProduit", "Famille", "FormeGalenique", "Activite", "Coef"]],
        on="ReferenceProduit", how="left",
    ).merge(
        df_c[["CodeClient", "Type", "Marche", "Type_Transaction", "ClientKey"]],
        on="CodeClient", how="left",
    )

    df["Date_Facture"] = pd.to_datetime(df["Date_Facture"])
    df["Annee"]        = df["Date_Facture"].dt.year
    df["Mois"]         = df["Date_Facture"].dt.month
    df["Trimestre"]    = df["Date_Facture"].dt.quarter
    df["DateComplete"] = df["Date_Facture"]
    df["ProduitKey"]   = df["ReferenceProduit"]

    log.info("Excel raw rows loaded: %d", len(df))
    return df


# ── Main ────────────────────────────────────────────────────────────────────
def run(use_excel: bool = False) -> pd.DataFrame:
    if use_excel:
        raw = extract_from_excel()
    else:
        engine = get_engine()
        raw    = extract_raw(engine)

    filtered = apply_filters(raw)
    monthly  = aggregate_monthly(filtered)
    full     = fill_missing_periods(monthly)
    enriched = add_history_stats(full)

    save(enriched, OUTPUT_FILE)
    return enriched


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 4 — Data Extraction")
    parser.add_argument(
        "--excel",
        action="store_true",
        help="Load from Excel source files instead of DW_Medis (offline/dev mode)",
    )
    args = parser.parse_args()

    df = run(use_excel=args.excel)
    print("\nSample output:")
    print(df.head(10).to_string(index=False))
    print(f"\nShape: {df.shape}")
    print(f"\nConfidence distribution:")
    print(df.drop_duplicates("ReferenceProduit")["Confiance_Donnees"].value_counts().to_string())