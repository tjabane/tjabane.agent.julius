from openai import OpenAI
from krabs_domain.models.agent import Message

_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client

class Agent:
    def __init__(self, model: str, system_prompt: str, tools: list, messages: list[Message]) -> None:
        self.model = model
        self.tools = tools
        self.messages = [ {"role": "system", "content": system_prompt}, *[{"role": m.role, "content": m.content} for m in messages],] or []
        self._client =  _get_client()
    
    def send_message(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})
        response = self._client.chat.completions.create(
            model=self.model,
            tools=self.tools,
            messages=self.messages,
        )
        reply = response.choices[0]
        print("Response:", reply.message.content)
        return "hello world"
    
    # while True:
    #     response = client.chat.completions.create(
    #         model=_MODEL,
    #         tools=ALL_DEFINITIONS,
    #         messages=messages,
    #     )

    #     choice = response.choices[0]
    #     if choice.finish_reason == "stop":
    #         reply = choice.message.content or ""
    #         session.messages.append(Message(role="assistant", content=reply))
    #         sessions.save(session)
    #         return reply

    #     if choice.finish_reason == "tool_calls":
    #         messages.append(choice.message)
    #         for tool_call in choice.message.tool_calls:
    #             inputs = json.loads(tool_call.function.arguments)
    #             result = _call_tool(tool_call.function.name, inputs, tool_deps)
    #             messages.append({
    #                 "role": "tool",
    #                 "tool_call_id": tool_call.id,
    #                 "content": result,
    #             })