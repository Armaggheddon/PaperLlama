import json
import asyncio
from typing import AsyncGenerator
from itertools import batched
from ollama import AsyncClient

from . import utils
from . import prompts
import api_models


class OllamaProxy:
    """
    Acts as a proxy to the Ollama API, exposing methods to interact with the 
    models in a more user-friendly way.
    """
    @staticmethod
    async def create(host: str, port: int) -> 'OllamaProxy':
        """
        Creates an instance of the OllamaProxy class by connecting to the 
        Ollama API. The models are pulled from the server if they are not
        already available (this might take a while), and the instance 
        is returned.

        Args:
        - host (str): The hostname of the Ollama API server.
        - port (int): The port number of the Ollama API server.

        Returns:
        - OllamaProxy: An instance of the OllamaProxy class.
        """
        _client = AsyncClient(f"http://{host}:{port}")
        embed_model_name = utils.get_embedding_model_name()
        chat_model_name = utils.get_chat_model_name()
        instruct_model_name = utils.get_instruct_model_name()
        available_models = await _client.list()
        if embed_model_name not in available_models:
            await _client.pull(embed_model_name)
        if chat_model_name not in available_models:
            await _client.pull(chat_model_name)
        if instruct_model_name not in available_models:
            await _client.pull(instruct_model_name)
        
        return OllamaProxy(_client)

    def __init__(self, _client: AsyncClient) -> None:
        """
        Initializes the OllamaProxy instance with the given AsyncClient.
        
        Args:
        - _client (AsyncClient): The AsyncClient instance to use for 
            interacting with the Ollama API.
        """
        self.client = _client

        # Get the model names and other model-specific information
        # Embedding model used for embedding text
        self.embed_model_name = utils.get_embedding_model_name()
        self.embed_model_output = utils.get_embedding_model_output()
        self.embed_model_max_input_tokens = utils.get_embedding_model_max_input_tokens()

        # Chat model used for chatting with the user
        self.chat_model_name = utils.get_chat_model_name()
        self.chat_model_max_input_tokens = utils.get_chat_model_max_input_tokens()

        # Instruct model used for summarizing and reranking text
        self.instruct_model_name = utils.get_instruct_model_name()

        # System message to send to the chat model
        self.chat_system_message = {
            "role": "system", 
            "content": prompts.QA_SYSTEM_PROMPT
        }
    
    async def embed(self, text: str | list[str]) -> list[list[float]]:
        """
        Embeds the given text using the embedding model.
        
        Args:
        - text (str | list[str]): The text to embed. If a list of strings 
            is provided, each string is embedded separately as a batch.
            
        Returns:
        - list[list[float]]: A list of embeddings, where each embedding is 
            a list of floats.
        """
        if isinstance(text, str):
            text = [text]
        text_embeddings = await self.client.embed(
            model=self.embed_model_name, 
            input=text
        )
        return text_embeddings["embeddings"]
    
    async def chat(
        self, 
        user_input: str, 
        chat_history: list[api_models.ChatMessage] = None, 
        context: list[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Initiates a chat with the chat model, using the given user input,
        chat history, and context. The chat history and context are used
        to provide a more coherent conversation. The response is returned
        as a stream of json objects separated by newlines. Uses the chat
        model to chat with the user.

        Args:
        - user_input (str): The user input to start the chat with.
        - chat_history (list[ChatMessage]): The chat history to provide to the 
            chat model. Each string in the list represents a message in the
            chat history.
        - context (list[str]): The context to provide to the chat model. Each
            string in the list represents a message in the context. The context
            represents the document or conversation that the chat is based on.

        Returns:
        - str: The json stream response from the chat model.
        """
        # Prepare the chat query with the context
        _query_with_context = [
            self.chat_system_message,
        ]
        if chat_history:
            _query_with_context += [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in chat_history
            ]
        _query_with_context += [
            {
                "role": "user",
                "content": utils.format_query(context, user_input)
            }
        ]
        response = await self.client.chat(
            model=self.chat_model_name,
            messages=_query_with_context, 
            stream = True,
        )

        # Yield the response as a stream of json objects
        async for chunk in response:
            yield json.dumps(chunk) + '\n'

    async def summarize(
        self, 
        text: list[str], 
        parallel_req_count: int=4
    ) -> str:
        """
        Summarizes the given text by splitting it into chunks and summarizing
        each chunk separately. The summaries are then concatenated and
        summarized again to get the final summary. Uses the instruct model
        to summarize the text.
        
        Args:
        - text (list[str]): The text to summarize. The text is split into 
            chunks, and each chunk is summarized separately.
        - parallel_req_count (int): The number of parallel requests to make
            to the summarization model. This affects the speed of the 
            summarization process.
        
        Returns:
        - str: The final summary of the text.
        """
        # Summarize each chunk separately
        chunk_summaries = []
        for batch in batched(text, parallel_req_count):
            chunk_summaries += await asyncio.gather(*[
                self.client.generate(
                    model=self.instruct_model_name,
                    system=prompts.SUMMARIZE_SYSTEM_PROMPT,
                    prompt=chunk,
                    options={"temperature": 0.1}
                )
                for chunk in batch
            ])

        # Summarize the summaries
        summary = await self.client.generate(
            model=self.instruct_model_name,
            system=prompts.SUMMARIZE_SYSTEM_PROMPT,
            prompt=" ".join([summary["response"] for summary in chunk_summaries]),
            options={"temperature": 0.1}
        )

        return summary["response"]
    
    async def filter_out_irrelevant_chunks(
        self, 
        user_query: str, 
        text_chunks: list[str]
    ) -> list[str]:
        """
        Reranks the given text chunks based on the user query. The user query
        is used to determine the relevance of each text chunk, and the relevant
        chunks are returned. Uses the instruct model to rerank the text chunks.
        In reality this method instead of reranking filters out
        irrelevant text chunks.
        
        Args:
        - user_query (str): The user query to use for reranking the text chunks.
        - text_chunks (list[str]): The text chunks to rerank.
        
        Returns:
        - list[str]: The relevant text chunks.
        """
        _rerank_system_prompt = [
            {
                "role": "system", 
                "content": prompts.DOCUMENT_RERANK_SYSTEM_PROMPT
            }
        ]
        relevant_document_chunks = []
        for chunk in text_chunks:
            _rerank_task = _rerank_system_prompt + [
                {
                    "role": "user", 
                    "content": utils.format_rerank_prompt(
                        chunk, 
                        user_query
                    )}
            ]

            rerank_response = await self.client.chat(
                model=self.instruct_model_name,
                messages=_rerank_task,
            )

            is_relevant: bool = "yes" in rerank_response["message"]["content"]
            if is_relevant:
                relevant_document_chunks.append(chunk)

        return relevant_document_chunks