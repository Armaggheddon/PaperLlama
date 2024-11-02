import os
import pathlib
import sqlite3

import faiss

from parser.pdf_parse import Page

from . import utils

_DB_FILE_EXTENSION = "db"

_root_metadata_table = {
    "table_name": "root_metadata",
    "columns": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "faiss_id INTEGER",
        "user_filename TEXT",
        "subindex_filename TEXT",
        "pdffile_path TEXT",
        "document_hash TEXT",
        "document_summary TEXT",
    ]
}

_document_metadata_table = {
    "table_name": "document_metadata",
    "columns": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "faiss_id INTEGER",
        "page_number INTEGER",
        "text_chunk TEXT",
    ]
}

class MetadataDB:
    def __init__(self, data_root: str, root_db_name: str, sub_index_path: str):

        self.subindex_path = sub_index_path

        if not os.path.isdir(data_root):
            os.makedirs(data_root)

        self.root_db_path = pathlib.Path(data_root) / f"{root_db_name}.{_DB_FILE_EXTENSION}"
        # In python 3.12.7 sqlite3.threadsafety is 3
        # which means that using modules, connections and cursors across 
        # different threads is safe since operations will be serialized
        # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
        self.root_conn = sqlite3.connect(str(self.root_db_path), check_same_thread=False)

        # create the table if it does not exist
        self._create_table(self.root_conn, **_root_metadata_table)
    
    def _create_table(self, db_conn: sqlite3.Connection, table_name: str, columns: list[str]):
        columns_str = ", ".join(columns)
        with db_conn as conn:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})")

    def close(self):
        self.root_conn.close()

    def has_document(self, document_hash: str) -> bool:
        cursor = self.root_conn.cursor()
        cursor.execute(f"SELECT * FROM {_root_metadata_table['table_name']} WHERE document_hash = ?", (document_hash,))
        result = cursor.fetchone() is not None
        cursor.close()
        return result

    def add_document_to_root(
        self, 
        faiss_id: int,
        user_filename: str, 
        subindex_filename: str, 
        pdf_file_path: str,
        document_hash: str,
        document_summary: str
    ):
        
        # ensure that no other file with the same faiss_id or document_hash exists
        if self.has_document(document_hash):
            raise ValueError("Document already exists in the database")

        with self.root_conn as conn:
            conn.execute(
                "INSERT INTO root_metadata "
                "(faiss_id, user_filename, subindex_filename, pdffile_path, document_hash, document_summary) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    faiss_id, 
                    user_filename,
                    subindex_filename, 
                    pdf_file_path, 
                    document_hash, 
                    document_summary
                )
            )

    def remove_document_from_root(self, document_ids: list[int]):
        with self.root_conn as conn:
            cursor = conn.cursor()
            for document_id in document_ids:
                cursor.execute(
                    f"DELETE FROM {_root_metadata_table['table_name']} WHERE faiss_id = ?",
                    (document_id,)
                )
            cursor.close()

    def add_document(
            self, subindex_filename, faiss_ids, pages, text_chunks, overwrite=False
    ):
        tmp_db_path = os.path.join(self.subindex_path, f"{subindex_filename}.{_DB_FILE_EXTENSION}")
        tmp_db_conn = sqlite3.connect(tmp_db_path)
        self._create_table(tmp_db_conn, **_document_metadata_table)

        with tmp_db_conn as conn:
            for faiss_id, page, text_chunk in zip(faiss_ids, pages, text_chunks):
                conn.execute(
                    f"INSERT INTO {_document_metadata_table['table_name']} (faiss_id, page_number, text_chunk) VALUES (?, ?, ?)",
                    (faiss_id, page, text_chunk)
                )
        
        tmp_db_conn.close()

    def get_documents_for_ids(self, faiss_ids: list[int]) -> list[str]:
        # placeholders = ", ".join(["?"] * len(faiss_ids))
        cursor = self.root_conn.cursor()
        cursor.execute(f"SELECT subindex_filename FROM {_root_metadata_table['table_name']} WHERE faiss_id IN ({utils.build_placeholder_string(len(faiss_ids))})", faiss_ids)
        file_names = cursor.fetchall()
        cursor.close()
        return [fn[0] for fn in file_names]
    
    def get_document_chunks_for_ids(self, db_name: str, chunk_ids: list[int]) -> list[str]:
        db_path = os.path.join(self.subindex_path, f"{db_name}.{_DB_FILE_EXTENSION}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT text_chunk FROM {_document_metadata_table['table_name']} WHERE faiss_id IN ({utils.build_placeholder_string(len(chunk_ids))})", chunk_ids)
        chunk_texts = cursor.fetchall()
        cursor.close()
        conn.close()
        return [ct[0] for ct in chunk_texts]
    
    def get_all_documents(self):
        cursor = self.root_conn.cursor()
        cursor.execute(f"SELECT id, user_filename, document_summary FROM {_root_metadata_table['table_name']}")
        documents = cursor.fetchall()
        cursor.close()
        return [{"id": d[0], "user_filename": d[1], "document_summary": d[2]} for d in documents]

    def clear_root(self):
        with self.root_conn as conn:
            conn.execute(f"DELETE FROM {_root_metadata_table['table_name']}")

    def delete(self, subindex_filename: str):
        db_path = os.path.join(self.subindex_path, f"{subindex_filename}.{_DB_FILE_EXTENSION}")
        if os.path.isfile(db_path):
            os.remove(db_path)