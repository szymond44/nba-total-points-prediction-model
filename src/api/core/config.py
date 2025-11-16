from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    PROJECT_NAME: str = "NTPPM API"
    API_V1_STR: str = "/api/v1"

settings = Settings()
