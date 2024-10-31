import numpy as np

def embeddings_to_numpy(embeddings: list[list[float]]) -> np.array:
    return np.array(embeddings, dtype=np.float32)
    

def generate_index_ids(start: int, count: int) -> list[int]:
    return [i for i in range(start, start + count)]

def list_to_numpy(ids: list[int]) -> np.ndarray:
    return np.array(ids)