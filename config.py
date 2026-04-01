from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict (
        env_file=".env",
        env_file_encoding="utf-8"
    )

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    max_upload_size_bytes: int = 5 * 1024 * 1024 ## 5 MB

    posts_per_page: int = 10

    reset_token_expire_minutes: int = 60

    mail_server: str = "localhost"
    mail_port: int = 587
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "noreply@example.com"
    mail_use_tls: bool = False

    frontend_url: str = "http://localhost:8000"
    # This value is intentionally defined as a static configuration (via .env) rather than being derived from incoming requests.
    #
    # The request "Host" header and similar attributes are controlled by the client and can be
    # manipulated (e.g., Host Header Injection). Relying on them to build URLs (such as password
    # reset links or email verification links) can lead to vulnerabilities.

settings = Settings()