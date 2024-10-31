from ollama import AsyncClient

from . import utils

# class OllamaEmbed:

#     @staticmethod
#     async def create(host, port):
#         _client = AsyncClient(f"http://{host}:{port}")
#         model_name = utils.get_embedding_model_name()
#         available_models = await _client.list()
#         if model_name not in available_models:
#             await _client.pull(model_name)
            
#         model_info = await _client.show(model_name)
#         family = model_info["details"]["family"]
#         embedding_length = model_info["model_info"][f"{family}.embedding_length"]
#         return OllamaEmbed(host, port, model_name, family, embedding_length)

#     def __init__(self, host, port, model_name:str, family: str, embedding_length: int):
#         self.client = AsyncClient(f"http://{host}:{port}")
#         self.model_name = model_name
#         self.family = family
#         self.embedding_length = embedding_length

#     async def embed(self, text: str | list[str]):
#         return await self.client.embed(model=self.model_name, input=text)

class OllamaProxy:

    @staticmethod
    async def create(host, port):
        _client = AsyncClient(f"http://{host}:{port}")
        embed_model_name = utils.get_embedding_model_name()
        chat_model_name = utils.get_chat_model_name()
        available_models = await _client.list()
        if embed_model_name not in available_models:
            await _client.pull(embed_model_name)
        if chat_model_name not in available_models:
            await _client.pull(chat_model_name)
        
        return OllamaProxy(_client)

    def __init__(self, _client: AsyncClient):
        self.client = _client

        self.embed_model_name = utils.get_embedding_model_name()
        self.embed_model_output = utils.get_embedding_model_output()
        self.embed_model_max_input_tokens = utils.get_embedding_model_max_input_tokens()

        self.chat_model_name = utils.get_chat_model_name()
        self.chat_model_max_input_tokens = utils.get_chat_model_max_input_tokens()
    
    async def embed(self, text: list[str]) -> list[list[float]]:
        text_embeddings = await self.client.embed(
            model=self.embed_model_name, 
            input=text
        )
        print(text_embeddings.keys())
        return text_embeddings["embeddings"]
    
    async def chat(self, user_input: str, context: list[str] = None):
        # TODO: format message to include context
        messages = [
            {"role": "system", "content": "You are a smart llm that will chat with the following context. Please chat with the following context."},
            {"role": "user", "content": user_input}
        ]
        response = await self.client.chat(
            model=self.chat_model_name, 
            messages=messages, 
            stream = True
        )

        async for chunk in response:
            yield chunk["message"]["content"]

    async def summarize(self, text: list[str]):
        messages = [{"role": "system", "content": "You are a smart llm that will summarize the following texts. Please summarize the following texts."}]
        messages.append({"role": "user", "content": "".join(text)})
        summary = await self.client.chat(
            model=self.chat_model_name,
            messages=messages,
        )

        return summary["message"]["content"]