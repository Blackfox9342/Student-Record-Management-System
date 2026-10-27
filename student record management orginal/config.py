import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "prakash-dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///prakash_university.db",
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
