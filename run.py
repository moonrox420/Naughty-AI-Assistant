import argparse
import multiprocessing
import sys
import threading
import time
import webbrowser
import uvicorn
from src.config import settings

import json
import urllib.request

def _open_browser_delayed(url: str, delay: float = 1.2):
    time.sleep(delay)
    webbrowser.open(url)

def _is_already_running(host: str, port: int) -> bool:
    try:
        url = f"http://{host}:{port}/api/health"
        req = urllib.request.Request(url, headers={"User-Agent": "NaughtyAI-HealthChecker"})
        with urllib.request.urlopen(req, timeout=1.0) as res:
            if res.status == 200:
                data = json.loads(res.read().decode())
                return data.get("app") == settings.APP_NAME
    except Exception:
        return False
    return False

def main():
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="Run the Naughty-AI-Assistant local companion server.")
    parser.add_argument("--host", type=str, default=settings.HOST, help=f"Host interface to bind (default: {settings.HOST})")
    parser.add_argument("--port", type=int, default=settings.PORT, help=f"Port to bind (default: {settings.PORT})")
    parser.add_argument("--reload", action="store_true", default=settings.DEBUG, help="Enable auto-reload for development")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch web browser")

    args = parser.parse_args()

    app_url = f"http://{args.host}:{args.port}"

    # If Naughty AI is already running on this port, simply open browser and exit cleanly
    if _is_already_running(args.host, args.port):
        print(f"\n=======================================================")
        print(f"  {settings.APP_NAME} is ALREADY running on {app_url}!")
        print(f"  Opening active session in your web browser...")
        print(f"=======================================================\n")
        if not args.no_browser:
            webbrowser.open(app_url)
        sys.exit(0)

    print(f"\n=======================================================")
    print(f"  Starting {settings.APP_NAME}")
    print(f"  URL: {app_url}")
    print(f"  Local Ollama target: {settings.OLLAMA_BASE_URL}")
    print(f"  Local LM Studio target: {settings.LMSTUDIO_BASE_URL}")
    print(f"  SD WebUI Forge target: {settings.FORGE_BASE_URL}")
    print(f"=======================================================\n")

    if not args.no_browser:
        threading.Thread(target=_open_browser_delayed, args=(app_url,), daemon=True).start()

    try:
        is_frozen = getattr(sys, "frozen", False)
        if is_frozen:
            from src.main import app
            uvicorn.run(
                app,
                host=args.host,
                port=args.port,
                reload=False,
                log_level="info",
            )
        else:
            uvicorn.run(
                "src.main:app",
                host=args.host,
                port=args.port,
                reload=args.reload,
                log_level="info",
            )
    except OSError as err:
        if "10048" in str(err) or getattr(err, "winerror", None) == 10048:
            print(f"\n[ERROR] Port {args.port} is already in use by another running instance.")
            print(f"[TIP] Close any running Naughty AI Assistant window, or start with --port <number>.\n")
            sys.exit(1)
        raise

if __name__ == "__main__":
    main()
