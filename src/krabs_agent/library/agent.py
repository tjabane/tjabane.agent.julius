from openai import OpenAI

class Agent:
    def __init__(self, model: str, prompt: str, tools: list) -> None:
        self.model = model
        self.prompt = prompt
        self.tools = tools
        self.messages = []
        self._client =  OpenAI()
    
    def send_message(self, message: str) -> str:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": message},
        ]