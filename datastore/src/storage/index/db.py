import os
import pathlib

import faiss

from . import utils


_EXT = "faiss"

class VectorIndex:
    def __init__(
        self,
        embedding_length: int,
        data_root: str,
        root_index_name: str,
        sub_index_path: str
    ) -> None:
        
        self.embedding_length = embedding_length
        self.sub_index_path = pathlib.Path(sub_index_path)
        self.root_path = pathlib.Path(data_root) / f"{root_index_name}.{_EXT}"

        if not self.root_path.exists():
            tmp_index = faiss.IndexFlatL2(embedding_length)
            tmp_id_index = faiss.IndexIDMap(tmp_index)
            faiss.write_index(tmp_id_index, str(self.root_path))
            del tmp_id_index
            del tmp_index
        
        self.root_index: faiss.IndexIDMap = faiss.read_index(str(self.root_path))

    def close(self):
        faiss.write_index(
            self.root_index,
            str(self.root_path)
        )

    def _get_index(
        self,
        index_path: pathlib.Path
    ) -> faiss.IndexFlatL2:
        if not index_path.exists():
            tmp_index = faiss.IndexFlatL2(self.embedding_length)
            faiss.write_index(tmp_index, str(index_path))
            del tmp_index
        
        return faiss.read_index(str(index_path))
    
    def root_index_size(self) -> int:
        return self.root_index.ntotal
    
    def add_to_root(
        self,
        embedding: list[float],
    ):
        embeddings = [embedding]
        ids = utils.generate_ids(
            self.root_index_size(),
            1
        )
        index_embeddings = utils.embeddings_to_np(embeddings)
        faiss.normalize_L2(index_embeddings)
        self.root_index.add_with_ids(index_embeddings, ids)
        return ids[0]
    
    def remove_from_root(
        self,
        ids: int | list[int]
    ):
        if isinstance(ids, int):
            ids = [ids]
        np_ids = utils.ids_to_np(ids)
        ids_to_remove = faiss.IDSelectorArray(
            len(ids),
            faiss.swig_ptr(np_ids)
        )
        self.root_index.remove_ids(ids_to_remove)


    def query_root(
        self,
        query_embedding: list[float],
        top_k: int = 5
    ) -> list[int]:
        query_embedding = utils.embeddings_to_np([query_embedding])
        faiss.normalize_L2(query_embedding)
        _, ids = self.root_index.search(query_embedding, min(top_k, self.root_index_size()))
        return ids[0].tolist()
    
    def clear_root(self):
        self.root_index.reset()

    def add(
        self,
        uuid: str,
        embeddings: list[list[float]]
    ) -> list[int]:
        index_path = self.sub_index_path / f"{uuid}.{_EXT}"
        index = self._get_index(index_path)
        index_embeddings = utils.embeddings_to_np(embeddings)
        faiss.normalize_L2(index_embeddings)
        index.add(index_embeddings)
        faiss.write_index(index, str(index_path))
        return [i for i in range(len(embeddings))]

    def remove(
        self,
        index_name: str
    ) -> None:
        
        index_path = self.sub_index_path / f"{index_name}.{_EXT}"
        if os.path.isfile(index_path):
            os.remove(index_path)
    
    def query(
        self,
        uuid: str,
        query_embedding: list[float],
        top_k: int = 5
    ) -> list[int]:
        index_path = self.sub_index_path / f"{uuid}.{_EXT}"
        index = self._get_index(index_path)
        query_embedding = utils.embeddings_to_np([query_embedding])
        faiss.normalize_L2(query_embedding)
        # print(index.ntotal)
        _, ids = index.search(query_embedding, min(top_k, index.ntotal))
        return ids[0].tolist()