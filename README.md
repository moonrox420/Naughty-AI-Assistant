# Naughty AI Assistant 💋

> [!WARNING]
> ### 🔞 ADULT CONTENT ADVISORY — NOT SUITABLE FOR MINORS (18+)
> **This software is strictly intended for adults (18 years of age or older / age of majority in your jurisdiction). It is NOT suitable for minors.**
> This application is an uncensored roleplay and companion platform capable of generating mature, adult, and sexually explicit textual and visual content via locally hosted artificial intelligence models. By installing, running, downloading, or using this software, you confirm that you are of legal adult age in your jurisdiction and consent to viewing mature and adult content.

A production-grade, local-first, uncensored conversational companion and roleplay platform built in Python. Designed for complete privacy, unconstrained creativity, long-term memory retention, and on-demand scene photo synthesis using local open-weight LLMs (Ollama / LM Studio) and Stable Diffusion WebUI Forge.

---

## ✨ Features

- **Local & 100% Private:** Zero third-party cloud data leaks or surveillance. Runs entirely on your local machine against Ollama (`http://localhost:11434`) or LM Studio (`http://localhost:1234/v1`).
- **Stable Diffusion WebUI Forge Integration:**
  - One-click photorealistic scene rendering via on-demand `📸 Photo` buttons on assistant turns.
  - `/image <prompt>` slash command for immediate standalone scene generation.
  - Character-specific visual appearance tags and negative prompts embedded in Character Cards.
  - Interactive full-resolution lightbox viewer for generated photographs.
  - One-click detached background launcher for Stable Diffusion WebUI Forge.
- **Strict VRAM & GPU Safety:**
  - Integrated cooperative GPU lock (`src.image.gpu_lock`) ensuring LLM text generation and Forge image generation never execute concurrently on the GPU, completely eliminating VRAM spikes and CUDA out-of-memory errors.
- **Dynamic Auto-Discovery:** Automatically probes and detects active local models with zero manual JSON tweaking.
- **Full Roleplay Formatting:** Visual distinction between *physical actions / body language*, "spoken dialogue", and (inner thoughts).
- **Tavern V1 / V2 Character Card Support:** Seamlessly import and export `.json` character cards compatible with SillyTavern and the Tavern specification, including visual generation tags.
- **Bundled Uncensored Presets:** Pre-configured with rich companions out-of-the-box (Scarlet Blake, Roxie 'Glitch' Vex, Evelyn Vance, Lilith Voss) with pre-tuned visual appearance prompts.
- **Hybrid Memory Architecture:**
  - Sliding context window for local LLM token safety.
  - Background asynchronous fact extractor automatically saves user preferences, secrets, and relationship milestones into persistent SQLite storage.
  - Live session scratchpad always injected into active context.
- **Full Roleplay Interaction Suite:**
  - Token-by-token real-time WebSocket streaming with instantaneous "Stop" abort capability.
  - Swipe alternative generations (`[ < 1/3 > ]`).
  - Inline message editing and branching message deletion.
  - "Continue" generation to keep the companion writing seamlessly.
- **Multi-Persona & Multi-Chat:** Manage multiple independent chat sessions per companion and switch between customizable user profiles.
- **Glassmorphic Obsidian UI:** Modern, zero-dependency dark aesthetic frontend built with Vanilla CSS and HTML5, served directly by FastAPI.
- **Desktop Launchers & Packaging Suite:**
  - One-click `start_app.bat` and `start_all.bat` (launches both Forge and Assistant).
  - `create_desktop_shortcut.bat` for instant Windows desktop shortcuts.
  - `build_exe.bat` for compiling a standalone `dist/NaughtyAI.exe` via PyInstaller.
  - `installer.iss` for building a native Windows installer (`NaughtyAI_Setup.exe`) via Inno Setup.

---

## 🚀 One-Click Windows Launchers

Double-click any of the provided batch scripts in the repository root:
- **`start_app.bat`**: Starts the Assistant server and automatically opens your default browser to `http://127.0.0.1:8069`.
- **`start_all.bat`**: Starts Stable Diffusion WebUI Forge (`webui-user.bat`) in a detached window, initializes Naughty AI Assistant, and launches the browser.
- **`create_desktop_shortcut.bat`**: Creates desktop shortcuts on your Windows desktop.
- **`build_exe.bat`**: Compiles the standalone executable `dist/NaughtyAI.exe` using PyInstaller.

---

## 🛠️ Manual Quick Start

### 1. Prerequisites
- Windows 10 / 11 (64-bit)
- Python 3.12+ (or 3.14+)
- [Ollama](https://ollama.com/) or [LM Studio](https://lmstudio.ai/)
- (Optional) [Stable Diffusion WebUI Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge)

### 2. Setup Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### 3. Launch Application
```powershell
.\.venv\Scripts\python.exe run.py
```
Open your browser to:
👉 **[http://127.0.0.1:8069](http://127.0.0.1:8069)**

---

## 🏗️ Architecture Overview

```
Naughty-AI-Assistant/
├── run.py                     # Application entry point with browser auto-launch
├── start_app.bat              # One-click assistant launcher
├── start_all.bat              # Combined SD Forge + Assistant launcher
├── create_desktop_shortcut.bat# Windows desktop shortcut generator
├── build_exe.bat              # PyInstaller executable compilation script
├── naughty_ai.spec            # PyInstaller build specification
├── installer.iss              # Inno Setup Windows installer script
├── requirements.txt           # Python dependencies
├── .env.example               # Default environment settings
├── src/
│   ├── config.py              # Pydantic BaseSettings & path resolution
│   ├── main.py                # FastAPI application & static mounting
│   ├── api/
│   │   ├── routes.py          # REST endpoints (characters, personas, sessions, images)
│   │   └── websocket.py       # WebSocket streaming & cancellation engine
│   ├── cards/
│   │   ├── parser.py          # Tavern V1/V2 character card import & export
│   │   └── presets.py         # Built-in uncensored companions & visual tags
│   ├── db/
│   │   ├── database.py        # aiosqlite connection pool & WAL migrations
│   │   ├── schema.sql         # SQLite schema definitions
│   │   └── repository.py      # Asynchronous data access layer
│   ├── image/
│   │   ├── client.py          # Stable Diffusion WebUI Forge txt2img client
│   │   ├── launcher.py        # Detached background process spawner
│   │   └── gpu_lock.py        # Mutual exclusion lock protecting GPU VRAM
│   ├── llm/
│   │   ├── client.py          # Streaming LLM client for Ollama & LM Studio
│   │   ├── detector.py        # Active runner and model probing
│   │   └── models.py          # Typed generation parameter models
│   └── memory/
│       ├── manager.py         # Context assembler (sliding window + facts + notes)
│       └── extractor.py       # Background LLM worker for persistent facts
└── static/
    ├── index.html             # Single Page Application
    ├── css/style.css          # Glassmorphic dark UI design system
    └── js/
        ├── markdown.js        # Roleplay syntax formatter
        ├── personas.js        # User persona manager
        ├── settings.js        # Settings & Forge status manager
        ├── cards.js           # Character card editor & importer
        ├── chat.js            # Chat streaming, photo generation, & lightbox
        └── app.js             # Application initialization
```

---

## ⚙️ Configuration (.env)

| Key | Default | Description |
|---|---|---|
| `HOST` | `127.0.0.1` | Network binding interface |
| `PORT` | `8069` | HTTP and WebSocket port |
| `DEFAULT_RUNNER` | `ollama` | Default inference backend (`ollama` or `lmstudio`) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `LMSTUDIO_BASE_URL` | `http://localhost:1234/v1` | LM Studio OpenAI-compatible endpoint |
| `FORGE_PATH` | `C:/Users/droxa/stable-diffusion-webui-forge` | Path to SD WebUI Forge directory |
| `FORGE_BASE_URL` | `http://127.0.0.1:7860` | Forge API endpoint |
| `DEFAULT_TEMPERATURE` | `0.85` | Default sampling temperature |
| `DEFAULT_TOP_P` | `0.90` | Nucleus sampling probability |
| `DEFAULT_MIN_P` | `0.05` | Min-p sampling threshold |
| `DEFAULT_REPEAT_PENALTY`| `1.15` | Repetition penalty factor |
| `DEFAULT_MAX_TOKENS` | `2048` | Maximum output tokens per turn |
| `CONTEXT_SLIDING_WINDOW_TURNS` | `20` | Max recent messages in sliding context |
| `ENABLE_FACT_EXTRACTION` | `true` | Enable background fact extraction |

---

## 📜 License & Disclaimers

### Disclaimer of Liability & AI-Generated Content

**IMPORTANT LEGAL NOTICE: PLEASE READ CAREFULLY BEFORE USING THIS SOFTWARE.**

1. **AI Output & Non-Liability:**
   This application is a user interface and orchestration layer that connects to third-party, locally hosted Large Language Models (LLMs) and diffusion image generation engines (such as Ollama, LM Studio, and Stable Diffusion WebUI Forge). The author and developer, **Dustin Hill**, has zero control over, and assumes **NO RESPONSIBILITY OR LIABILITY** whatsoever for any text, imagery, dialogue, outputs, roleplay content, prompts, ideas, or materials generated, synthesized, displayed, stored, or transmitted by or through this software.
2. **User Responsibility:**
   All inputs, prompts, characters, cards, images, and interactions are solely initiated, directed, and controlled by the end user. You, the user, bear sole legal and moral responsibility for how you utilize this software and for any content produced. You agree not to generate, save, or distribute any material that violates applicable local, state, federal, or international laws, including but not limited to laws governing obscenity, intellectual property rights, and protection of minors.
3. **Age Requirement (18+ Only):**
   This software is strictly intended for adults (18 years of age or older / the age of majority in your legal jurisdiction). **Dustin Hill** is not responsible for unauthorized access or use by minors.
4. **Standard Software Disclaimer (AS-IS):**
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, ACCURACY, AND NONINFRINGEMENT. IN NO EVENT SHALL **DUSTIN HILL** OR ANY CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS, DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES, ARISING OUT OF OR IN CONNECTION WITH THE SOFTWARE, ITS USE, OR THE INABILITY TO USE THE SOFTWARE.
5. **Local Execution & Privacy Assurance:**
   This software runs locally on your machine. **Dustin Hill** does not operate central servers, collect telemetry, monitor your sessions, or possess access to any data or images created on your system.

---

### License

This project is licensed under the [MIT License](LICENSE) with the express inclusion of the above disclaimers. See the [`LICENSE`](LICENSE) file for complete details.

