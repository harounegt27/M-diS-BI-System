import joblib
import os

_model = None

def get_model():
    global _model
    if _model is None:
        path = os.path.join(os.path.dirname(__file__), "model.joblib")
        _model = joblib.load(path)
    return _model