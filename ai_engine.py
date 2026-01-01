import ollama
from ollama import Client

class AIEngine:
    def __init__(self, host="http://localhost:11434"):
        self.host = host
        self.client = Client(host=self.host)

    def process(self, text, system_prompt, model_name="llama3"):
        """
        Process the transcribed text through an LLM using the given system prompt.
        """
        if not text:
            return ""

        # If no system prompt is provided, just return the raw text (pass-through)
        if not system_prompt or not system_prompt.strip():
            return text

        try:
            # Construct the message history
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': text}
            ]

            response = self.client.chat(model=model_name, messages=messages)
            return response['message']['content']

        except Exception as e:
            print(f"AI Processing Error: {e}")
            # Fallback: return raw text if AI fails (e.g., Ollama not running)
            return f"[AI Error: {e}] \n\n{text}"

    def list_models(self):
        try:
            models_info = self.client.list()
            # The structure of models_info might vary slightly by version, 
            # usually it's {'models': [{'name': 'llama3:latest', ...}]}
            return [m['name'] for m in models_info.get('models', [])]
        except Exception:
            return []
