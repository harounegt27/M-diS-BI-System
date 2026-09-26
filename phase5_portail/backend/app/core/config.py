from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_SERVER: str = "DESKTOP-R3PHCES"
    DB_NAME:   str = "DW_Medis"
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    MODEL_PATH: str = "app/ml/model_xgboost.json"

    @property
    def connection_string(self) -> str:
        driver = self.DB_DRIVER.replace(" ", "+")
        return (
            f"mssql+pyodbc://@{self.DB_SERVER}/{self.DB_NAME}"
            f"?driver={driver}&trusted_connection=yes"
        )

    class Config:
        env_file = ".env"

settings = Settings()