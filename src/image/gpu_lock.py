import asyncio

# Global cooperative lock between LLM inference and Stable Diffusion Forge image generation.
# Prevents concurrent GPU compute to avoid VRAM overcommitment, out-of-memory errors, and driver crashes.
gpu_lock = asyncio.Lock()
