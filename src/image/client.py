import asyncio
import base64
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from src.config import settings

logger = logging.getLogger(__name__)

from src.image.gpu_lock import gpu_lock


class ForgeClient:
    def __init__(self, base_url: str = settings.FORGE_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.http_timeout = httpx.Timeout(180.0, connect=5.0)

    async def check_status(self) -> Dict[str, Any]:
        """Checks if Forge API is responsive on port 7860."""
        url = f"{self.base_url}/sdapi/v1/sd-models"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    models = res.json()
                    checkpoints = [
                        {
                            "title": m.get("title", ""),
                            "model_name": m.get("model_name", ""),
                            "hash": m.get("hash", ""),
                        }
                        for m in models
                    ]
                    return {
                        "online": True,
                        "url": self.base_url,
                        "checkpoints": checkpoints,
                        "count": len(checkpoints),
                    }
        except Exception:
            pass
        return {"online": False, "url": self.base_url, "checkpoints": [], "count": 0}

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = settings.DEFAULT_IMAGE_WIDTH,
        height: int = settings.DEFAULT_IMAGE_HEIGHT,
        steps: int = settings.DEFAULT_IMAGE_STEPS,
        cfg_scale: float = settings.DEFAULT_IMAGE_CFG,
    ) -> Dict[str, Any]:
        """
        Calls Forge /sdapi/v1/txt2img with exclusive lock to prevent VRAM overcommitment.
        Saves decoded image to data/images/ and returns image metadata and relative URL.
        """
        async with gpu_lock:
            url = f"{self.base_url}/sdapi/v1/txt2img"
            neg = negative_prompt if negative_prompt is not None else settings.DEFAULT_NEGATIVE_PROMPT

            payload = {
                "prompt": prompt,
                "negative_prompt": neg,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "width": width,
                "height": height,
                "sampler_name": "DPM++ 2M Karras",
                "batch_size": 1,
                "n_iter": 1,
                "restore_faces": True,
            }

            settings.setup_directories()

            try:
                async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                    res = await client.post(url, json=payload)
                    if res.status_code != 200:
                        err_text = res.text
                        logger.error(f"Forge txt2img error {res.status_code}: {err_text}")
                        return {
                            "success": False,
                            "error": f"Forge API returned status {res.status_code}: {err_text[:200]}",
                        }

                    data = res.json()
                    images = data.get("images", [])
                    if not images:
                        return {"success": False, "error": "No image data returned from Forge."}

                    # Decode base64 image data
                    img_b64 = images[0]
                    # Handle data URI prefix if present
                    if "," in img_b64:
                        img_b64 = img_b64.split(",", 1)[1]

                    img_bytes = base64.b64decode(img_b64)
                    filename = f"gen_{uuid.uuid4().hex}.png"
                    filepath = settings.IMAGES_DIR / filename
                    filepath.write_bytes(img_bytes)

                    # Return accessible static URL
                    image_url = f"/static/images/{filename}"
                    return {
                        "success": True,
                        "image_url": image_url,
                        "filename": filename,
                        "width": width,
                        "height": height,
                    }

            except httpx.ConnectError:
                return {
                    "success": False,
                    "error": f"Could not connect to Forge at {self.base_url}. Make sure Forge is started.",
                }
            except Exception as ex:
                logger.error(f"Image generation failed: {ex}")
                return {"success": False, "error": str(ex)}
