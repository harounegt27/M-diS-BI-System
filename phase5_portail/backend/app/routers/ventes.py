from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import ventes_service

router = APIRouter(prefix="/api/ventes", tags=["Ventes"])

@router.get("/kpis")
def kpis(db: Session = Depends(get_db)):
    return ventes_service.get_kpis(db)

@router.get("/mensuelles")
def mensuelles(db: Session = Depends(get_db)):
    return ventes_service.get_ventes_mensuelles(db)

@router.get("/top-produits")
def top_produits(limit: int = 10, db: Session = Depends(get_db)):
    return ventes_service.get_top_produits(db, limit)

@router.get("/top-clients")
def top_clients(limit: int = 10, db: Session = Depends(get_db)):
    return ventes_service.get_top_clients(db, limit)