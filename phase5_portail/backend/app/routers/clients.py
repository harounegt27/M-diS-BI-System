from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import clients_service

router = APIRouter(prefix="/api/clients", tags=["Clients"])

@router.get("/")
def liste_clients(
    search: str = Query(default=""),
    limit: int  = Query(default=200),
    db: Session = Depends(get_db)
):
    return clients_service.get_all_clients(db, search, limit)


@router.get("/{code_client}")
def detail_client(code_client: str, db: Session = Depends(get_db)):
    return clients_service.get_client_detail(db, code_client)