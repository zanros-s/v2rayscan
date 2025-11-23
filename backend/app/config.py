import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)


class Settings:
    PROJECT_NAME: str = "v2rayscan"
    DB_URL: str = os.getenv(
        "DB_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'data.db')}",
    )


    XRAY_PATH: str = os.getenv("XRAY_PATH", "/usr/local/bin/xray")
    XRAY_TEST_URL: str = os.getenv(
        "XRAY_TEST_URL",
        "https://www.google.com/generate_204",
    )
    XRAY_STARTUP_DELAY: float = float(os.getenv("XRAY_STARTUP_DELAY", "0.8"))
    XRAY_REQUEST_TIMEOUT: float = float(os.getenv("XRAY_REQUEST_TIMEOUT", "8.0"))
    XRAY_MONITOR_REQUEST_TIMEOUT: float = float(os.getenv("XRAY_MONITOR_REQUEST_TIMEOUT", "0.5"))

    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "CHANGE_ME_TO_SOMETHING_REALLY_RANDOM_AND_LONG",
    )


settings = Settings()
