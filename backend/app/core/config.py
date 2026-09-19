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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
