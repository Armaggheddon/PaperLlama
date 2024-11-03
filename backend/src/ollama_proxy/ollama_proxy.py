import json
import asyncio
from ollama import AsyncClient

from . import utils
from . import prompts

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

        self.instruct_model_name = utils.get_instruct_model_name()

        self.qa_messages = [
            {"role": "system", "content": prompts.QA_SYSTEM_PROMPT}
        ]
    
    async def embed(self, text: str | list[str]) -> list[list[float]]:
        if isinstance(text, str):
            text = [text]
        text_embeddings = await self.client.embed(
            model=self.embed_model_name, 
            input=text
        )
        print(text_embeddings.keys())
        return text_embeddings["embeddings"]
    
    async def chat(self, user_input: str, context: list[str] = None):
        # TODO: format message to include context
        _query_with_context = self.qa_messages + [{
            "role": "user",
            "content": utils.format_query(context, user_input)
        }]
        response = await self.client.chat(
            model=self.chat_model_name,
            messages=_query_with_context, 
            stream = True,
            # format='json'
        )

        async for chunk in response:
            yield json.dumps(chunk) + '\n'

    async def summarize(self, text: list[str]):
        _summary_task = [
            {"role": "system", "content": prompts.SUMMARIZE_SYSTEM_PROMPT},
            {"role": "user", "content": utils.format_summary_prompt(text)}
        ]
        summary = await self.client.chat(
            model=self.instruct_model_name,
            messages=_summary_task,
        )

        return summary["message"]["content"]
    
    async def rerank(self, user_query, text_chunks: list[str]) -> list[str]:
        _rerank_system_prompt = [
            {"role": "system", "content": prompts.DOCUMENT_RERANK_SYSTEM_PROMPT}
        ]
        relevant_document_chunks = []
        for chunk in text_chunks:
            _rerank_task = _rerank_system_prompt + [
                {"role": "user", "content": utils.format_rerank_prompt(chunk, user_query)}
            ]

            rerank_response = await self.client.chat(
                model=self.instruct_model_name,
                messages=_rerank_task,
            )

            is_relevant: bool = "yes" in rerank_response["message"]["content"]
            if is_relevant:
                relevant_document_chunks.append(chunk)

        return relevant_document_chunks