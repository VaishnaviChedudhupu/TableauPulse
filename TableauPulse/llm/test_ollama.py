
import requests

url = "http://localhost:11434/api/generate"

payload = {
    "model": "llama3.2:1b",
    "prompt": "Explain in two sentences why businesses analyze sales and profit.",
    "stream": False
}

try:
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()

    result = response.json()

    print("Ollama connection successful!")
    print("\nModel response:")
    print(result["response"])

except requests.RequestException as error:
    print("Ollama connection failed:", error)
