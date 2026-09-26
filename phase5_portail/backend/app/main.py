from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ventes, produits, clients , predictions

app = FastAPI(title="MediS Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ventes.router)
app.include_router(produits.router)
app.include_router(clients.router)
app.include_router(predictions.router)

@app.get("/health")
def health():
    return {"status": "ok"}