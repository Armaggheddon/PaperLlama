import os
import pathlib

import faiss
import numpy as np

from . import utils

DB_STORE_PATH = "/vector_index/data"
ROOT_INDEX_NAME = "root.index"
SUB_INDEX_PATH = "/vector_index/data/sub_indexes"

class VectorDB:
    def __init__(self, embedding_length: int):
        self.embedding_length = embedding_length
        self.root_index_path = pathlib.Path(DB_STORE_PATH) / ROOT_INDEX_NAME
        if not os.path.isfile(str(self.root_index_path)):
            faiss.write_index(faiss.IndexFlatL2(embedding_length), str(self.root_index_path))
        if not os.path.isdir(SUB_INDEX_PATH):
            os.makedirs(SUB_INDEX_PATH)

        self.root_index = faiss.read_index(str(self.root_index_path))
        self.index_map = {
            "root": str(self.root_index_path)
        }

    def _touch_index(self, index_name: str):
        if index_name not in self.index_map:
            index_path = pathlib.Path(SUB_INDEX_PATH) / index_name
            self.index_map[index_name] = str(index_path)
            faiss.write_index(faiss.IndexFlatL2(self.embedding_length), str(index_path))
        
        return faiss.read_index(self.index_map[index_name])

    def add(self, index_name: str, vectors: np.ndarray):
        
        tmp_index = self._touch_index(index_name)
        tmp_index.add(vectors)

        tmp_index.close()

    def query(self, index_name: str, vector: np.ndarray, top_k: int):
        if index_name not in self.index_map:
            raise ValueError(f"Index {index_name} not found")

        index = faiss.read_index(self.index_map[index_name])
        D, I = index.search(vector, top_k)
        return D, I


