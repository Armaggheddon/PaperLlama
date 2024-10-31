import os

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