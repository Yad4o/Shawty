import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
ASSISTANT_NAME = os.getenv('ASSISTANT_NAME', 'Jarvis')
