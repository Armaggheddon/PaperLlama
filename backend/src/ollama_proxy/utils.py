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

def get_chat_model_max_input_tokens():
    return int(os.getenv("CHAT_MODEL_MAX_INPUT_TOKENS", 8192))

def format_message(context: list[str], user_input: str) -> str:
    _context = "\n\n".join(context)
    return (
        f"{prompts.BEGIN_CONTEXT_TOKEN} {_context} {prompts.END_CONTEXT_TOKEN} "
        f"{prompts.BEGIN_USER_INPUT_TOKEN} {user_input} {prompts.END_USER_INPUT_TOKEN}"
    )

def format_query(context: list[str], user_input: str) -> str:
    _context = "\n\n".join(context)
    return prompts.QA_USER_PROMPT_TEMPLATE.format(
        context_str=_context,
        query_str=user_input
    )
    