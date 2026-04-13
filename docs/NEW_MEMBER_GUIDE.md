# 🚀 Project "Shawty" - Developer Onboarding Guide

Welcome to the team! This repository contains a headless, "Jarvis-style" Windows AI Voice Assistant built in Python 3.11.

It utilizes **FastAPI** for an underlying web server & test dashboard, **Vosk/SpeechRecognition** for voice input, **pyttsx3** for fast audio output, and the **Groq API** to process human intent into strict JSON commands that execute on the local OS.

---

## 🛠️ 1. First-Time Setup Instructions

Follow these steps exactly to get the project running on your local machine.

### Step 1: Install Python
Ensure that you have **Python 3.11** installed on your Windows machine.
You can verify this in your terminal:
```powershell
python --version
# Should output: Python 3.11.x
```

### Step 2: Clone & Prepare Environment
Clone the repository and set up your virtual environment. We use a local `venv` to keep dependencies isolated.
```powershell
git clone <repository_url>
cd Shawty
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
With your virtual environment activated, install all required packages:
```powershell
pip install -r requirements.txt
```
> **Note on PyAudio**: If `pip install` fails while building `pyaudio` on Windows, you can install the pre-compiled wheel directly by running: `pip install pipwin` followed by `pipwin install pyaudio`.

### Step 4: Environment Variables (`.env`)
Create a file named `.env` in the root directory of the project (if it isn't there already). 
Ask the Project Lead for the API keys, or generate your own Groq API key from [console.groq.com/keys](https://console.groq.com/keys).

Your `.env` file must look exactly like this:
```env
GROQ_API_KEY=your_groq_api_key_here
ASSISTANT_NAME=Jarvis
LLM_MODEL=mixtral-8x7b-32768
TTS_RATE=180
TTS_VOLUME=1.0
DEBUG_MODE=True
ENABLE_VOICE_FEEDBACK=True
```

---

## 🧪 2. How to Run & Test the Application

Since this is intended to eventually be a "headless" background voice assistant, we test it during development using a clean FastAPI Web Dashboard.

1. **Start the API Server**:
   Ensure your `venv` is active and run:
   ```powershell
   uvicorn main:app --reload
   ```
2. **Access the Testing Dashboard**:
   Open your browser and navigate to:
   [http://127.0.0.1:8000](http://127.0.0.1:8000)

3. **Simulate Voice Commands**:
   You can type text directly into the dashboard input (e.g., "Open chrome") to safely test the LLM logic without needing to speak into your microphone.

---

## 📁 3. Project Architecture (Where to write code)

The system is highly modular. If you are assigned a ticket, here is where you will work:

* `main.py`: Bootstraps the FastAPI server and serves the testing UI.
* `frontend/index.html`: The HTML/CSS for the testing dashboard.
* **`voice/`**: `input.py` (microphones/STT) and `output.py` (speakers/TTS).
* **`brain/`**: `llm.py` (Groq API calls), `prompt.py` (System prompts), and `parser.py` (Converting LLM text into JSON actions).
* **`actions/`**: The actual OS execution hooks (`apps.py` for subprocess, `browser.py` for URLs, `controller.py` for pyautogui mouse/keyboard simulation).
* **`core/`**: `loop.py` (The main infinite background loop) and `executor.py` (Routes parsed JSON actions to the `actions/` functions).

---

## 📝 Rules of the Codebase

1. **Stick to Python 3.11**.
2. **Do Not Push `.env`**: Never commit your `GROQ_API_KEY`. The `.gitignore` is already protecting it, don't bypass it.
3. **Strict JSON Engine**: All modifications to `brain/prompt.py` must ensure the Groq LLM continues to output **only valid JSON**. Do not allow the LLM to output conversational markdown.
4. **Asynchronous Execution**: pyttsx3 and speech listeners are blocking. Ensure any updates to `core/loop.py` utilize threading correctly so the OS does not freeze up.