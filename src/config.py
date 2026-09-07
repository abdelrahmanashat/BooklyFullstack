from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL : str
    JWT_SECRET : str
    JWT_ALGORITHM : str
    REDIS_URL : str = "redis://localhost:6379/0"
    DOMAIN: str
    MAIL_API_KEY : str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    
    # For Celery
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_PORT: Optional[int] = None
    MAIL_SERVER: Optional[str] = None
    
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # 2. Add a validator to enforce them ONLY on localhost
    @model_validator(mode='after')
    def validate_celery_vars_for_localhost(self):
        if "localhost" in self.DOMAIN:
            missing = [
                var for var, val in {
                    "MAIL_USERNAME": self.MAIL_USERNAME,
                    "MAIL_PASSWORD": self.MAIL_PASSWORD,
                    "MAIL_PORT": self.MAIL_PORT,
                    "MAIL_SERVER": self.MAIL_SERVER
                }.items() if val is None
            ]
            
            if missing:
                raise ValueError(f"Missing Celery variables for localhost: {', '.join(missing)}")
                
        return self
    
Config = Settings()

broker_url = Config.REDIS_URL
result_backend = Config.REDIS_URL
