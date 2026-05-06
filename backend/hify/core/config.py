from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从 .env 文件读取，支持环境变量覆盖。"""

    # MySQL
    MYSQL_DSN: str = "mysql+aiomysql://root:dk123456@127.0.0.1:3306/hify"
    MYSQL_POOL_SIZE: int = 10
    MYSQL_MAX_OVERFLOW: int = 20
    MYSQL_POOL_RECYCLE: int = 1800

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # JWT
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # LLM
    OPENAI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    # API
    API_PREFIX: str = "/api"
    API_VERSION: str = "v1"

    # Server
    LOG_LEVEL: str = "DEBUG"
    PORT: int = 8080

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def api_v1_prefix(self) -> str:
        return f"{self.API_PREFIX}/{self.API_VERSION}"


settings = Settings()
