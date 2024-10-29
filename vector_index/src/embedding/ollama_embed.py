from ollama import AsyncClient

from . import utils

class OllamaEmbed:

    @staticmethod
    async def create(host, port):
        _client = AsyncClient(f"http://{host}:{port}")
        model_name = utils.get_embedding_model_name()
        available_models = await _client.list()
        if model_name not in available_models:
            await _client.pull(model_name)
            
        model_info = await _client.show(model_name)
        family = model_info["details"]["family"]
        embedding_length = model_info["model_info"][f"{family}.embedding_length"]
        return OllamaEmbed(host, port, model_name, family, embedding_length)

    def __init__(self, host, port, model_name:str, family: str, embedding_length: int):
        self.client = AsyncClient(f"http://{host}:{port}")
        self.model_name = model_name
        self.family = family
        self.embedding_length = embedding_length

    async def embed(self, text: str | list[str]):
        return await self.client.embed(model=self.model_name, input=text)
