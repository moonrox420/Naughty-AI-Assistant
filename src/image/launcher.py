import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict
import httpx

from src.config import settings

logger = logging.getLogger(__name__)


async def is_forge_running() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{settings.FORGE_BASE_URL.rstrip('/')}/sdapi/v1/sd-models")
            return res.status_code == 200
    except Exception:
        return False


def launch_forge_background() -> Dict[str, Any]:
    """
    Spawns webui-user.bat from Forge directory as a detached background process on Windows.
    """
    forge_dir = Path(settings.FORGE_PATH)
    if not forge_dir.exists():
        return {
            "success": False,
            "error": f"Forge directory not found at configured path: {settings.FORGE_PATH}",
        }

    # Search for launcher batch file
    target_bat = forge_dir / "webui-user.bat"
    if not target_bat.exists():
        target_bat = forge_dir / "webui.bat"
    if not target_bat.exists():
        return {
            "success": False,
            "error": f"Could not find webui-user.bat or webui.bat inside {forge_dir}",
        }

    try:
        # Windows detached process flags
        creation_flags = 0
        if os.name == "nt":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008  # DETACHED_PROCESS

        proc = subprocess.Popen(
            [str(target_bat)],
            cwd=str(forge_dir),
            creationflags=creation_flags,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )

        logger.info(f"Launched Forge process PID {proc.pid} from {target_bat}")
        return {
            "success": True,
            "pid": proc.pid,
            "message": "Forge launched in background. Checkpoint loading usually takes 20-40 seconds.",
        }
    except Exception as ex:
        logger.error(f"Failed to launch Forge: {ex}")
        return {"success": False, "error": str(ex)}
