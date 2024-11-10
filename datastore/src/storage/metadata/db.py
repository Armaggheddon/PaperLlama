from pathlib import Path
import sqlite3

from . import tables

from api_models import DocumentInfo

_EXT = "db"

class MetadataDB:
    
    def __init__(
        self,
        data_root: str,
        root_db_name: str,
        sub_index_path: str
    ) -> None:
        self._root_db_path = Path(data_root) / f"{root_db_name}.{_EXT}"
        self._sub_index_path = Path(sub_index_path)

        # In python 3.12.7 sqlite3.threadsafety is 3
        # which means that using modules, connections and cursors across 
        # different threads is safe since operations will be serialized
        # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
        self._root_db = sqlite3.connect(
            str(self._root_db_path), 
            check_same_thread=False
        )
        with self._root_db as conn:
            conn.execute(tables.root_creation_str)

    def close(self) -> None:
        self._root_db.close()

    def has_document(
        self,
        document_hash: str
    ) -> bool:
        query_str = f"SELECT * FROM metadata WHERE document_hash = ?"
        with self._root_db as conn:
            cursor = conn.execute(query_str, (document_hash,))
            return cursor.fetchone() is not None
        
    def has_document_uuid(
        self,
        document_uuid: str
    ) -> bool:
        query_str = f"SELECT * FROM metadata WHERE uuid = ?"
        with self._root_db as conn:
            cursor = conn.execute(query_str, (document_uuid,))
            return cursor.fetchone() is not None
        
    def add_root_metadata(
        self,
        faiss_id: int,
        uuid: str,
        document_hash: str,
        document_filename: str,
        summary: str
    ) -> None:
        with self._root_db as conn:
            conn.execute(
                tables.root_insert_str, 
                (
                    faiss_id, 
                    uuid, 
                    document_hash,
                    document_filename, 
                    summary
                )    
            )

    def remove_from_root(
        self,
        document_uuid: str
    ) -> tuple[int, str]:
        faiss_id_query = f"SELECT faiss_id, document_filename FROM metadata WHERE uuid = ?" 
        delete_str = f"DELETE FROM metadata WHERE uuid = ?"
        with self._root_db as conn:
            cursor = conn.execute(faiss_id_query, (document_uuid,))
            faiss_id, document_filename = cursor.fetchone()
            conn.execute(delete_str, (document_uuid,))
            return faiss_id, document_filename

    def clear_root(self) -> None:
        query_str = f"DELETE FROM metadata"
        with self._root_db as conn:
            conn.execute(query_str)
    
    def query_root(
        self,
        faiss_ids: int | list[int]
    ) -> list[tuple[int, str]]:
        if isinstance(faiss_ids, int):
            faiss_ids = [faiss_ids]
        
        query_str = (
            f"SELECT uuid, summary FROM metadata "
            "WHERE faiss_id IN "
            f"({', '.join(['?' for _ in faiss_ids])})"
        )
        with self._root_db as conn:
            cursor = conn.execute(query_str, faiss_ids)
            return [(row[0], row[1]) for row in cursor.fetchall()]
        
    
        
    def add(
        self,
        uuid: str,
        faiss_ids: list[int],
        page_numbers: list[int],
        text_chunks: list[str]
    ) -> None:
        db_path = self._sub_index_path / f"{uuid}.{_EXT}"
        _conn = sqlite3.connect(str(db_path), check_same_thread=False)
        with _conn as conn:
            conn.execute(tables.document_creation_str)
            for faiss_id, page_number, text_chunk in zip(faiss_ids, page_numbers, text_chunks):
                conn.execute(
                    tables.document_insert_str, 
                    (
                        faiss_id, 
                        page_number, 
                        text_chunk
                    )
                )

    def query(
        self,
        uuid: str,
        faiss_ids: list[int]
    ) -> list[tuple[int, str]]:
        query_str = (
            f"SELECT page_number, text FROM metadata "
            "WHERE faiss_id IN "
            f"({', '.join(['?' for _ in faiss_ids])})"
        )
        db_path = self._sub_index_path / f"{uuid}.{_EXT}"
        _conn = sqlite3.connect(str(db_path), check_same_thread=False)
        with _conn as conn:
            cursor = conn.execute(query_str, faiss_ids)
            return [(row[0], row[1]) for row in cursor.fetchall()]
        
    def remove(
        self,
        uuid: str
    ) -> None:
        db_path = self._sub_index_path / f"{uuid}.{_EXT}"
        db_path.unlink()

    def get_documents_info(self) -> list[DocumentInfo]:
        query_str = f"SELECT uuid, document_hash, document_filename summary FROM metadata"
        with self._root_db as conn:
            cursor = conn.execute(query_str)
            return [
                DocumentInfo(
                    document_uuid=row[0],
                    document_hash_str=row[1],
                    document_filename=row[2],
                    document_summary=row[3]
                )
                for row in cursor.fetchall()
            ]