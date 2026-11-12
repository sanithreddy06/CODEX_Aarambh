import os

class AppConfig:
    PROJECT_NAME = "NovaCommerce API"
    VERSION = "2.1.0"
    SECRET_KEY = "demo-super-secret-jwt-key-not-for-prod"
    DATABASE_URL = "sqlite:///./sample_shop.db"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

config = AppConfig()
