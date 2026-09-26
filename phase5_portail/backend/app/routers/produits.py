from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import produits_service

router = APIRouter(prefix="/api/produits", tags=["Produits"])

@router.get("/")
def liste_produits(
    search: str = Query(default=""),
    db: Session = Depends(get_db)
):
    return produits_service.get_all_produits(db, search)

@router.get("/{reference}")
def detail_produit(reference: str, db: Session = Depends(get_db)):
    return produits_service.get_produit_detail(db, reference)