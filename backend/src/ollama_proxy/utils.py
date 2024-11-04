import os

from .  import prompts


def get_embedding_model_name():
    return os.getenv("EMBEDDING_MODEL_NAME", "nomic-embed-text")

def get_embedding_model_output():
    return int(os.getenv("EMBEDDING_MODEL_OUTPUT_SIZE", 768))

def get_embedding_model_max_input_tokens():
    return int(os.getenv("EMBEDDING_MODEL_MAX_INPUT_TOKENS", 8192))

def get_chat_model_name():
    return os.getenv("CHAT_MODEL_NAME", "llama3.2:1b")

def get_instruct_model_name():
    return os.getenv("INSTRUCT_MODEL_NAME", "llama3.2:1b-instruct-q4_0")

def get_chat_model_max_input_tokens():
    return int(os.getenv("CHAT_MODEL_MAX_INPUT_TOKENS", 8192))

def format_summary_prompt(context: list[str]) -> str:
    _context = "\n\n".join(context)
    return prompts.SUMMARIZE_PROMPT_TEMPLATE.format(context_str=_context)

def format_query(context: list[str], user_input: str) -> str:
    _context = "\n\n".join(context)
    return prompts.QA_USER_PROMPT_TEMPLATE.format(
        context_str=_context,
        query_str=user_input
    )

def format_rerank_prompt(document_summary: str, user_query: str) -> str:
    return prompts.DOCUMENT_RERANK_PROMPT_TEMPLATE.format(
        document_summary=document_summary,
        user_query=user_query
    )
    