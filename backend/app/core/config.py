from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env.

    Nothing here is hardcoded: secrets and connection strings always come
    from the environment so they never end up committed to Git.
    """

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "*"
    # OAuth client ID from Google Cloud Console. Empty means Google
    # sign-in is simply unavailable (the endpoint returns 501) rather
    # than failing confusingly at token-verify time.
    google_client_id: str = ""

    # Outbound email (verification codes, password resets), sent via an
    # authenticated Gmail account over SMTP. Empty username/password
    # means email sending is simply off: the API falls back to
    # returning the code directly in the response instead (dev/
    # prototype mode — see app/core/email.py and Token.dev_verification_code).
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Amahirwe"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_username and self.smtp_password)


settings = Settings()
