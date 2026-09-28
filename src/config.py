import sys
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_base_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "data"
    return Path("data")


_base_data = _resolve_base_data_dir()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Naughty AI Assistant"
    HOST: str = "127.0.0.1"
    PORT: int = 8069
    DEBUG: bool = False

    # Persistence
    DATA_DIR: Path = _base_data
    DATABASE_PATH: Path = _base_data / "naughty_ai.db"

    # Local LLM Inference endpoints
    DEFAULT_RUNNER: str = "ollama"  # "ollama" | "lmstudio" | "custom"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LMSTUDIO_BASE_URL: str = "http://localhost:1234/v1"
    CUSTOM_BASE_URL: str = ""
    CUSTOM_API_KEY: str = ""

    # Default model and generation hyperparameters
    DEFAULT_MODEL: str = ""
    DEFAULT_TEMPERATURE: float = 0.85
    DEFAULT_TOP_P: float = 0.90
    DEFAULT_MIN_P: float = 0.05
    DEFAULT_REPEAT_PENALTY: float = 1.15
    DEFAULT_MAX_TOKENS: int = 2048

    # Memory and context bounds
    CONTEXT_SLIDING_WINDOW_TURNS: int = 20
    ENABLE_FACT_EXTRACTION: bool = True
    FACT_EXTRACTION_MODEL: str = ""  # If empty, uses active model

    # Stable Diffusion WebUI Forge
    FORGE_PATH: str = "C:/Users/droxa/stable-diffusion-webui-forge"
    FORGE_BASE_URL: str = "http://127.0.0.1:7860"
    IMAGES_DIR: Path = _base_data / "images"
    DEFAULT_IMAGE_WIDTH: int = 512
    DEFAULT_IMAGE_HEIGHT: int = 768
    DEFAULT_IMAGE_STEPS: int = 25
    DEFAULT_IMAGE_CFG: float = 7.0
    DEFAULT_NEGATIVE_PROMPT: str = "blurry, bad anatomy, deformed hands, extra limbs, low quality, artifacts, watermark, disfigured, bad eyes, poorly drawn face"

    # Security & CORS
    CORS_ORIGINS: list[str] = ["*"]

    def setup_directories(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.IMAGES_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.setup_directories()
