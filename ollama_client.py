import requests

def ask_granite(prompt):
    """Send prompt to Granite model via Ollama"""
    url = "http://localhost:11434/api/generate"
    
    data = {
        "model": "granite3.1-dense:2b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature":0.8
         } 
    }
    
    try:
        res = requests.post(url, json=data, timeout=60)
        return res.json()["response"]
    except Exception as e:
        return f"AI service unavailable: {str(e)}"