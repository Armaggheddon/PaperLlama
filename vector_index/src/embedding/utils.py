import os

def get_embedding_model_name():
    return os.getenv("EMBEDDING_MODEL_NAME", "nomic-embed-text")