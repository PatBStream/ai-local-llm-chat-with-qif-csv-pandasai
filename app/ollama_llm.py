# app/ollama_llm.py
# from pandasai.llm.base import LLM
# from pandasai.helpers.memory import Memory
# from pandasai.prompts.base import BasePrompt
# from ollama import Client, ChatResponse

# class OllamaLLM(LLM):
#     """
#     LLM adapter for Ollama. Uses the official `ollama` Python client.
#     """
#     def __init__(self, api_base: str, model: str, **kwargs):
#         # Initialize Ollama Python client with the server URL (e.g. http://host:port)
#         self.host = api_base.rstrip("/")
#         self.client = Client(self.host)
#         self.model = model
#         self._invocation_params = kwargs

#     def chat_completion(self, prompt: str, memory: Memory) -> str:
#         # Build messages list like OpenAI expects
#         messages = memory.to_openai_messages() if memory else []
#         messages.append({"role": "user", "content": prompt})

#         # Call Ollama via Python client
#         resp: ChatResponse = self.client.chat(
#             model=self.model,
#             messages=messages,
#             stream=False,
#             **self._invocation_params
#         )
#         return resp.message.content

#     def call(self, instruction: BasePrompt, context=None) -> str:
#         p = instruction.to_string()
#         mem = context.memory if context else None
#         return self.chat_completion(p, mem)

#     @property
#     def type(self) -> str:
#         return "ollama"

# app/ollama_llm.py
import os
from pandasai_litellm import LiteLLM

# Point LiteLLM at your local Ollama server + Llama3.2 model
OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama/llama3.1:8b")

# Instantiate a LiteLLM client for PandasAI
llm = LiteLLM(api_base=OLLAMA_URL, model=OLLAMA_MODEL)
