from pydantic import BaseModel
from typing import Optional

class KPIVentes(BaseModel):
    ca_total: float
    nb_commandes: int
    nb_clients_actifs: int
    quantite_totale: int

class VenteMensuelle(BaseModel):
    annee: int
    mois: int
    nom_mois: str
    ca: float
    quantite: int

class TopProduit(BaseModel):
    reference_produit: str
    designation: str
    famille: Optional[str]
    ca: float
    quantite: int

class TopClient(BaseModel):
    code_client: str
    client: str
    pays: Optional[str]
    ca: float

class ProduitItem(BaseModel):
    reference_produit: str
    designation: str
    famille: Optional[str]
    activite: Optional[str]
    ca_total: float
    quantite_totale: int

class ClientItem(BaseModel):
    code_client: str
    client: str
    pays: Optional[str]
    region: Optional[str]
    ca_total: float
    nb_commandes: int

class PredictionRequest(BaseModel):
    reference_produit: str
    horizon: int = 3

class PredictionResult(BaseModel):
    mois: str
    prediction: float
    confiance: str