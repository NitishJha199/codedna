from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "codedna"
    app_env: str = "development"
    log_level: str = "INFO"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "codedna"
    postgres_user: str = "codedna"
    postgres_password: str = ""

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    github_webhook_secret: str = "dev-github-secret"
    gitlab_webhook_secret: str = "dev-gitlab-secret"
    pagerduty_webhook_secret: str = "dev-pagerduty-secret"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
