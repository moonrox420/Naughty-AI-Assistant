import asyncio
from typing import Any, Dict, List
import httpx

from src.config import settings
from src.llm.models import ModelInfo


async def probe_ollama(base_url: str = settings.OLLAMA_BASE_URL) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                models: List[ModelInfo] = []
                for m in data.get("models", []):
                    model_name = m.get("name", "")
                    details = m.get("details", {})
                    size_gb = round(m.get("size", 0) / (1024**3), 2)
                    models.append(
                        ModelInfo(
                            id=model_name,
                            name=model_name,
                            runner="ollama",
                            size=f"{size_gb} GB" if size_gb > 0 else None,
                            modified_at=m.get("modified_at"),
                            family=details.get("family"),
                        )
                    )
                return {"online": True, "runner": "ollama", "models": models, "url": base_url}
    except Exception:
        pass
    return {"online": False, "runner": "ollama", "models": [], "url": base_url}


async def probe_lmstudio(base_url: str = settings.LMSTUDIO_BASE_URL) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/models"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                models: List[ModelInfo] = []
                for m in data.get("data", []):
                    model_id = m.get("id", "")
                    models.append(
                        ModelInfo(
                            id=model_id,
                            name=model_id,
                            runner="lmstudio",
                            size=None,
                            modified_at=None,
                            family=None,
                        )
                    )
                return {"online": True, "runner": "lmstudio", "models": models, "url": base_url}
    except Exception:
        pass
    return {"online": False, "runner": "lmstudio", "models": [], "url": base_url}


async def detect_all_runners() -> Dict[str, Any]:
    """Probes all configured local runners concurrently."""
    ollama_task = probe_ollama(settings.OLLAMA_BASE_URL)
    lmstudio_task = probe_lmstudio(settings.LMSTUDIO_BASE_URL)
    ollama_res, lmstudio_res = await asyncio.gather(ollama_task, lmstudio_task)

    all_models: List[ModelInfo] = []
    all_models.extend(ollama_res.get("models", []))
    all_models.extend(lmstudio_res.get("models", []))

    return {
        "ollama": ollama_res,
        "lmstudio": lmstudio_res,
        "models": all_models,
        "active_runner": "ollama" if ollama_res["online"] else ("lmstudio" if lmstudio_res["online"] else "none"),
    }
