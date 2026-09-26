from fastapi import APIRouter, Depends, HTTPException ,Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import prediction_service

router = APIRouter(prefix="/api/predictions", tags=["Prédictions"])


@router.get("/all")
def predict_all(
    periode: str = Query(..., description="Format YYYY-MM, ex: 2026-06"),
    db: Session = Depends(get_db)
):
    """
    Prédit la demande de TOUS les produits pour une période donnée.
    Retourné trié par quantité prédite décroissante.
    """
    try:
        annee, mois = int(periode.split("-")[0]), int(periode.split("-")[1])
    except Exception:
        raise HTTPException(status_code=400, detail="Format période invalide. Utilisez YYYY-MM")

    results = prediction_service.predict_all(db, annee, mois)

    if not results:
        raise HTTPException(status_code=404, detail="Aucun produit trouvé")

    return {
        "periode": periode,
        "nb_produits": len(results),
        "predictions": results
    }


@router.get("/{reference}")
def predict(
    reference: str,
    horizon: int = 3,
    db: Session = Depends(get_db)
):
    if horizon < 1 or horizon > 6:
        raise HTTPException(status_code=400, detail="Horizon doit être entre 1 et 6")

    results = prediction_service.predict(db, reference, horizon)

    if not results:
        raise HTTPException(status_code=404, detail="Produit non trouvé ou sans historique")

    return {
        "reference_produit": reference,
        "horizon": horizon,
        "predictions": results
    }