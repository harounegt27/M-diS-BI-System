from sqlalchemy.orm import Session
from sqlalchemy import text

def get_kpis(db: Session):
    row = db.execute(text("""
        SELECT
            SUM(f.MontantTotalVente)         AS ca_total,
            COUNT(*)                          AS nb_commandes,
            COUNT(DISTINCT f.ClientKey)       AS nb_clients_actifs,
            SUM(f.Quantite)                   AS quantite_totale
        FROM Fait_Ventes f
    """)).fetchone()
    return {
        "ca_total": round(float(row.ca_total), 2),
        "nb_commandes": row.nb_commandes,
        "nb_clients_actifs": row.nb_clients_actifs,
        "quantite_totale": row.quantite_totale
    }

def get_ventes_mensuelles(db: Session):
    rows = db.execute(text("""
        SELECT
            d.Annee,
            d.Mois,
            d.NomMois,
            SUM(f.MontantTotalVente) AS ca,
            SUM(f.Quantite)          AS quantite
        FROM Fait_Ventes f
        JOIN Dim_Date d ON f.DateKey = d.DateKey
        GROUP BY d.Annee, d.Mois, d.NomMois
        ORDER BY d.Annee, d.Mois
    """)).fetchall()
    return [
        {
            "annee": r.Annee,
            "mois": r.Mois,
            "nom_mois": r.NomMois,
            "ca": round(float(r.ca), 2),
            "quantite": r.quantite
        }
        for r in rows
    ]

def get_top_produits(db: Session, limit: int = 10):
    rows = db.execute(text("""
        SELECT TOP (:limit)
            p.ReferenceProduit,
            p.DesignationProduit,
            p.Famille,
            SUM(f.MontantTotalVente) AS ca,
            SUM(f.Quantite)          AS quantite
        FROM Fait_Ventes f
        JOIN Dim_Produit p ON f.ProduitKey = p.ProduitKey
        GROUP BY p.ReferenceProduit, p.DesignationProduit, p.Famille
        ORDER BY ca DESC
    """), {"limit": limit}).fetchall()
    return [
        {
            "reference_produit": r.ReferenceProduit,
            "designation": r.DesignationProduit,
            "famille": r.Famille,
            "ca": round(float(r.ca), 2),
            "quantite": r.quantite
        }
        for r in rows
    ]

def get_top_clients(db: Session, limit: int = 10):
    rows = db.execute(text("""
        SELECT TOP (:limit)
            c.CodeClient,
            c.Client,
            c.Pays,
            SUM(f.MontantTotalVente) AS ca
        FROM Fait_Ventes f
        JOIN Dim_Client c ON f.ClientKey = c.ClientKey
        GROUP BY c.CodeClient, c.Client, c.Pays
        ORDER BY ca DESC
    """), {"limit": limit}).fetchall()
    return [
        {
            "code_client": r.CodeClient,
            "client": r.Client,
            "pays": r.Pays,
            "ca": round(float(r.ca), 2)
        }
        for r in rows
    ]