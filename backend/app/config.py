from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://research:research@localhost:5432/research_agent"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    fetch_interval_hours: int = 6
    arxiv_categories: str = "cs.AI,cs.CL,cs.LG,cs.RO,cs.CV"
    cors_origins: str = "http://localhost:3000"
    twitter_bearer_token: str | None = None


settings = Settings()
