from ctypes import util
import os
import pathlib

import faiss

from . import utils

_INDEX_EXTENSION = "index"

class VectorDB:
    def __init__(
        self, 
        embedding_length: int, 
        data_root: str, 
        root_index_name: str, 
        sub_index_path: str
    ) -> None:
        self.embedding_length = embedding_length
        self.root_index_path = pathlib.Path(data_root) / f"{root_index_name}.{_INDEX_EXTENSION}"
        
        if not os.path.isfile(str(self.root_index_path)):
            tmp_index = faiss.IndexFlatL2(self.embedding_length)
            tmp_index_with_id = faiss.IndexIDMap(tmp_index)
            faiss.write_index(tmp_index_with_id, str(self.root_index_path))
            del tmp_index
            del tmp_index_with_id
        
        self.sub_index_path = sub_index_path

        self.root_index: faiss.IndexIDMap = faiss.read_index(str(self.root_index_path))

    def _create_empty_index(self):
        return faiss.IndexFlatL2(self.embedding_length)
    
    def _touch_index(self, index_path: str, ovwerwrite: bool=False):
        if not os.path.isfile(index_path):
            # index does not exist
            faiss.write_index(self._create_empty_index(), index_path)
        elif ovwerwrite:
            os.remove(index_path)
            faiss.write_index(self._create_empty_index(), index_path)
        return faiss.read_index(index_path)

    def get_root_offset_id(self) -> int:
        return self.root_index.ntotal

    def add_to_root(self, vectors: list[float] | list[list[float]]) -> int:
        if isinstance(vectors[0], float):
            vectors = [vectors]
        offset_id = self.get_root_offset_id()
        ids = utils.generate_index_ids(offset_id, len(vectors))
        index_embeddings = utils.embeddings_to_numpy(vectors)
        faiss.normalize_L2(index_embeddings)
        self.root_index.add_with_ids(index_embeddings, ids)
        return offset_id
    
    def remove_from_root(self, ids: int | list[int]):
        if isinstance(ids, int):
            ids = [ids]
        np_ids = utils.list_to_numpy(ids)
        ids_to_remove = faiss.IDSelectorBatch(len(ids), np_ids)
        self.root_index.remove_ids(ids_to_remove)

    def add(self, index_name: str, vectors: list[list[float]], ovwerwrite: bool=False) -> list[int]:
        index_path = pathlib.Path(self.sub_index_path) / f"{index_name}.{_INDEX_EXTENSION}"
        tmp_index: faiss.IndexFlatL2 = self._touch_index(str(index_path), ovwerwrite)
        index_embeddings = utils.embeddings_to_numpy(vectors)
        faiss.normalize_L2(index_embeddings)
        tmp_index.add(index_embeddings)
        faiss.write_index(tmp_index, str(index_path))
        return [i for i in range(0, len(vectors))]

    def remove(self, index_name: str):
        index_path = pathlib.Path(self.sub_index_path) / f"{index_name}.{_INDEX_EXTENSION}"
        if os.path.isfile(index_path):
            os.remove(index_path)
    
    def get_index_offset_id(self, index_name: str):
        index_path = pathlib.Path(self.sub_index_path) / f"{index_name}.{_INDEX_EXTENSION}"
        tmp_index: faiss.IndexFlatL2 = self._touch_index(str(index_path))
        return tmp_index.ntotal

    def query_root(self, vector: list[float], top_k: int) -> list[int]:
        query_embedding = utils.embeddings_to_numpy(vector)
        faiss.normalize_L2(query_embedding)
        _, I = self.root_index.search(query_embedding, min(self.root_index.ntotal, top_k))
        return utils.indices_to_list(I[0])

    def query(self, index_name: str, vector: list[float], top_k: int) -> list[int]:
        index_path = pathlib.Path(self.sub_index_path) / f"{index_name}.{_INDEX_EXTENSION}"
        if not os.path.isfile(index_path):
            raise ValueError(f"Index {index_path} does not exist")

        tmp_index: faiss.IndexFlatL2 = faiss.read_index(str(index_path))
        query_embedding = utils.embeddings_to_numpy(vector)
        faiss.normalize_L2(query_embedding)
        _, I = tmp_index.search(query_embedding, min(tmp_index.ntotal, top_k))
        return utils.indices_to_list(I[0])

    def close(self):
        faiss.write_index(self.root_index, str(self.root_index_path))
