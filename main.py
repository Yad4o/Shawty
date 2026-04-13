from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import os
import threading

app = FastAPI(title="Jarvis AI API")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serves our small testing dashboard UI"""
    # Simply read and return the HTML file
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Frontend index.html not found!</h1>")

@app.post("/api/test_command")
async def test_endpoint(payload: dict):
    """Lets us send text commands from the UI to test the LLM without voice."""
    user_text = payload.get("text", "")
    
    # TODO: Pass 'user_text' to brain.llm.process_command() later!
    
    return {"status": "Processing", "received": user_text, "simulated_action": "None yet"}

@app.on_event("startup")
def startup_event():
    # TODO: In the future, this is where we start the voice listening loop:
    # threading.Thread(target=start_assistant_loop, daemon=True).start()
    pass
