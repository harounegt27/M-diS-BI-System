from sqlalchemy.orm import Session
from sqlalchemy import text

def get_all_produits(db: Session, search: str = ""):
    query = """
        SELECT
            p.ReferenceProduit,
            p.DesignationProduit,
            p.Famille,
            p.Activite,
            SUM(f.MontantTotalVente) AS ca_total,
            SUM(f.Quantite)          AS quantite_totale
        FROM Dim_Produit p
        LEFT JOIN Fait_Ventes f ON f.ProduitKey = p.ProduitKey
    """
    if search:
        query += """
        WHERE p.DesignationProduit LIKE :search
        OR p.ReferenceProduit LIKE :search
        """
    query += """
        GROUP BY p.ReferenceProduit, p.DesignationProduit, p.Famille, p.Activite
        ORDER BY ca_total DESC
    """
    params = {"search": f"%{search}%"} if search else {}
    rows = db.execute(text(query), params).fetchall()
    return [
        {
            "reference_produit": r.ReferenceProduit,
            "designation": r.DesignationProduit,
            "famille": r.Famille,
            "activite": r.Activite,
            "ca_total": round(float(r.ca_total or 0), 2),
            "quantite_totale": r.quantite_totale or 0
        }
        for r in rows
    ]

def get_produit_detail(db: Session, reference: str):
    historique = db.execute(text("""
        SELECT
            d.Annee,
            d.Mois,
            d.NomMois,
            SUM(f.MontantTotalVente) AS ca,
            SUM(f.Quantite)          AS quantite
        FROM Fait_Ventes f
        JOIN Dim_Produit p ON f.ProduitKey = p.ProduitKey
        JOIN Dim_Date d    ON f.DateKey    = d.DateKey
        WHERE p.ReferenceProduit = :ref
        GROUP BY d.Annee, d.Mois, d.NomMois
        ORDER BY d.Annee, d.Mois
    """), {"ref": reference}).fetchall()
    return [
        {
            "annee": r.Annee,
            "mois": r.Mois,
            "nom_mois": r.NomMois,
            "ca": round(float(r.ca), 2),
            "quantite": r.quantite
        }
        for r in historique
    ]