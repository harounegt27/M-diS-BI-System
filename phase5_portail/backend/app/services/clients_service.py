from sqlalchemy.orm import Session
from sqlalchemy import text

def get_all_clients(db: Session, search: str = "", limit: int = 200):
    query = """
        SELECT TOP (:limit)
            c.CodeClient,
            c.Client,
            c.Pays,
            c.Region,
            c.Type,
            SUM(f.MontantTotalVente) AS ca_total,
            COUNT(*)                  AS nb_commandes
        FROM Dim_Client c
        LEFT JOIN Fait_Ventes f ON f.ClientKey = c.ClientKey
    """
    if search:
        query += """
        WHERE c.Client LIKE :search
        OR c.CodeClient LIKE :search
        """
    query += """
        GROUP BY c.CodeClient, c.Client, c.Pays, c.Region, c.Type
        ORDER BY ca_total DESC
    """
    params = {"limit": limit}
    if search:
        params["search"] = f"%{search}%"
    rows = db.execute(text(query), params).fetchall()
    return [
        {
            "code_client": r.CodeClient,
            "client":      r.Client,
            "pays":        r.Pays,
            "region":      r.Region,
            "type":        r.Type,
            "ca_total":    round(float(r.ca_total or 0), 2),
            "nb_commandes": r.nb_commandes or 0
        }
        for r in rows
    ]


def get_client_detail(db: Session, code_client: str):
    historique = db.execute(text("""
        SELECT
            d.Annee,
            d.Mois,
            d.NomMois,
            SUM(f.MontantTotalVente) AS ca,
            SUM(f.Quantite)          AS quantite
        FROM Fait_Ventes f
        JOIN Dim_Client c ON f.ClientKey = c.ClientKey
        JOIN Dim_Date d   ON f.DateKey   = d.DateKey
        WHERE c.CodeClient = :code
        GROUP BY d.Annee, d.Mois, d.NomMois
        ORDER BY d.Annee, d.Mois
    """), {"code": code_client}).fetchall()
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