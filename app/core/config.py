import os
# ... imports ...

load_dotenv()
MY_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-3-flash-preview")
print(f"DEBUG: I am trying to use model: {MY_MODEL}") # <--- YE PRINT LAGAYEIN

model = genai.GenerativeModel(MY_MODEL)