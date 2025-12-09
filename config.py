from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):

    database_url: str 
    secret_key: str
    algorithm: str 
    access_token_expire_minutes: int
    

    app_name: str = "Hotel Management System"
    debug: bool = True
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

settings = Settings()