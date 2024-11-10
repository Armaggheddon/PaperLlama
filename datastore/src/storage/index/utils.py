import numpy as np

def embeddings_to_np(embeddings: list[list[float]]) -> np.ndarray:
    return np.array(embeddings, dtype=np.float32)

def generate_ids(start: int, count: int) -> list[int]:
    return [i for i in range(start, start + count)]

def ids_to_np(ids: list[int]) -> np.ndarray:
    return np.array(ids)