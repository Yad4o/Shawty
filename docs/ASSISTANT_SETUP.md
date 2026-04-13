# Windows AI Assistant - Project Implementation Guide

This document outlines the entire setup process, architecture logic, and what code needs to go into each file to build your production-ready "Jarvis" style Windows AI Assistant.

## 1. Step-by-Step Setup Instructions

### Environment Preparation
1. **Open your terminal locally** in your project folder (`c:\Users\Administrator\Projects\Shawty`).
2. **Create a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. **Install the dependencies:**
   Run `pip install -r requirements.txt`. (See required dependencies below).
4. **Update `.env`**:
   Open the `.env` file just created in the root folder and add your actual `GROQ_API_KEY`.

### Required Dependencies (`requirements.txt`)
Create a `requirements.txt` in the root folder with the following:
```text
fastapi
uvicorn
groq
pyttsx3
SpeechRecognition
pyaudio
vosk
pyautogui
python-dotenv
pydantic
```
*(Note: If `pyaudio` fails to install on Windows, you usually need to install it via a downloaded `.whl` file from Christoph Gohlke's unofficial binaries or use `pipwin install pyaudio`.)*

---

## 2. Project Architecture & File Logic

Below is the structured breakdown of your application. Create these files in your IDE as needed. `main.py` is your starting point.

### Root Level

**`config.py`**
*   **Purpose:** Load and manage environment variables.
*   **What to add:** Use `dotenv` to load `.env`. Create a settings class/dict that makes `GROQ_API_KEY`, `ASSISTANT_NAME`, and voice settings globally accessible in the app.

**`main.py`**
*   **Purpose:** The main entry point of the FastAPI application and the lifecycle manager.
*   **What to add:**
    *   Initialize the `FastAPI()` app.
    *   On startup event: spin up the `core/loop.py` continuous voice listening thread in the background.
    *   Provide endpoints (e.g., `/status`, `/stop`) to manage the assistant via HTTP if needed.

### `voice/` Module

**`voice/input.py`**
*   **Purpose:** Handle real-time continuous Speech-to-Text.
*   **What to add:** 
    *   Initialize the `SpeechRecognition` library or directly wrap `Vosk` for offline audio stream processing.
    *   Create a `listen()` generator or callback function that yields text from the microphone.
    *   Keep it blocking or running in its own thread so it listens until a wake word (or constantly captures phrases).

**`voice/output.py`**
*   **Purpose:** Handle fast Text-to-Speech without freezing the app.
*   **What to add:**
    *   Initialize `pyttsx3` Engine. Set speed to ~180-200.
    *   *Crucial fix for pyttsx3:* Run the `engine.say()` and `engine.runAndWait()` in a secondary Thread or use an audio queue. If you run it on the main thread, it blocks the listening loop.

### `brain/` Module

**`brain/prompt.py`**
*   **Purpose:** Store the system instructions for the LLM.
*   **What to add:** A robust system prompt specifying strictly JSON output.
    *   *Example snippet:* "You are a Windows System Assistant. Parse the user's intent and output strictly in JSON format: `{\"commands\": [{\"action\": \"OPEN_APP\", \"target\": \"chrome.exe\"}, {\"action\": \"SEARCH\", \"query\": \"python latest version\"}]}`. Do NOT output markdown or conversational text."

**`brain/llm.py`**
*   **Purpose:** The Groq API wrapper.
*   **What to add:**
    *   Initialize the `Groq()` client using the key from `config.py`.
    *   Create a function `process_command(user_text)`.
    *   Send the text referencing the system prompt to the `mixtral-8x7b-32768` model. Set `response_format={\"type\": \"json_object\"}`.
    *   Return the raw JSON string.

**`brain/parser.py`**
*   **Purpose:** Validate and deserialize the LLM output.
*   **What to add:** 
    *   Use `pydantic` schemas or standard `json.loads()` to deserialize the Groq response.
    *   Ensure the structure strictly matches a list of actionable commands before passing it to the executor. Give graceful fallback if decoding fails.

### `actions/` Module

**This module is your actual "hands" on the OS.**

**`actions/apps.py`**
*   **What to add:** Functions to handle process creation. Use `subprocess.Popen` or `os.startfile()` to launch applications (e.g., Notepad, Chrome, Explorer).

**`actions/browser.py`**
*   **What to add:** Functions wrapping Python's `webbrowser` library to open URLs in new tabs, or `pyautogui` logic connected with `apps.py` to type in the URL bar.

**`actions/system.py`**
*   **What to add:** OS-level controls.
    *   Volume control (using `pycaw` or OS hotkeys).
    *   Shutdown/Sleep commands (using `os.system("shutdown /s /t 1")`).
    *   Killing self (`os._exit(0)`).

**`actions/controller.py`**
*   **What to add:** Wrappers for `pyautogui` for raw HID simulation.
    *   `type_text(text)`
    *   `press_key(key)`
    *   `click_at(x, y)`

### `core/` Module

**`core/executor.py`**
*   **Purpose:** Routes extracted JSON actions to the right `actions/` function.
*   **What to add:** A function `execute_plan(json_plan)`. It iterates through the list of parsed actions and triggers the respective functions safely. Includes `try/except` error handling for failed executions.

**`core/loop.py`**
*   **Purpose:** The infinite AI control loop.
*   **What to add:**
    *   `while True:` loop running in a daemon thread.
    *   `text = wait_for_voice()` (calls `voice/input.py`).
    *   `if text:` -> `json_plan = process_command(text)` (calls `brain/llm.py`).
    *   `execute_plan(json_plan)` (calls `core/executor.py`).
    *   Trigger TTS confirmation (calls `voice/output.py`).

### `utils/` Module

**`utils/logger.py`**
*   **What to add:** Configure Python's built-in `logging`. Make sure errors in parsing or execution are logged neatly to terminal and a local `.log` file so you can debug "silent failures" happening in background threads.

---

## 3. Windows Startup Configuration

To make the assistant start automatically with Windows:

### Method A: The Startup Folder (Fastest setup)
1. Press `Win + R`, type `shell:startup`, and press Enter.
2. Inside this folder, create a `.bat` file (e.g., `jarvis_start.bat`).
3. Add these contents:
   ```bat
   @echo off
   cd C:\Users\Administrator\Projects\Shawty
   call venv\Scripts\activate.bat
   start /B pythonw main.py
   ```
*(Note: using `pythonw` runs it without opening a visible cmd window).*

### Method B: PyInstaller (Standalone EXE)
1. Install pyinstaller: `pip install pyinstaller`
2. Run build command (after everything is working well):
   ```powershell
   pyinstaller --noconfirm --onedir --windowed --add-data "venv/Lib/site-packages/vosk/model;vosk/model" main.py
   ```
3. You can set the resulting `main.exe` to run on Windows Startup via Task Scheduler or Registry.

---

## 4. Execution Flow Refresher
1. **User speaks**: "Open Notepad and type hello world."
2. **`voice/input.py`** captures audio chunk → transcription → "open notepad and type hello world".
3. **`core/loop.py`** sends text to **`brain/llm.py`**.
4. **`brain/llm.py`** pings Groq API. Replies with JSON:
   ```json
   {
       "actions": [
           {"type": "APP_START", "target": "notepad"},
           {"type": "KEYBOARD_TYPE", "target": "hello world"}
       ]
   }
   ```
5. **`brain/parser.py`** verifies the JSON.
6. **`core/executor.py`** calls `actions.apps.start("notepad")`, pauses slightly, calls `actions.controller.type_text("hello world")`.
7. **`voice/output.py`** announces, "Done."
