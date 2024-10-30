import os
import pathlib
import sqlite3

from parser.pdf_parse import Page

_DB_FILE_EXTENSION = ".db"

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

        self.root_db_path = pathlib.Path(data_root) / root_db_name
        self.root_conn = sqlite3.connect(str(self.root_db_path))

        # create the table if it does not exist
        self._create_table(self.root_conn, **_root_metadata_table)
    
    def _create_table(self, conn, table_name: str, columns: list[str]):
        columns_str = ", ".join(columns)
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})")
        conn.commit()

    def close(self):
        self.root_conn.close()

    def has_document(self, document_hash: str) -> bool:
        cursor = self.root_conn.cursor()
        cursor.execute(f"SELECT * FROM {_root_metadata_table['table_name']} WHERE document_hash = ?", (document_hash,))
        return cursor.fetchone() is not None

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
        cursor = self.root_conn.cursor()
        cursor.execute(
            "SELECT * FROM root_metadata WHERE faiss_id = ? OR document_hash = ?",
            (faiss_id, document_hash)
        )
        if cursor.fetchone():
            raise ValueError("Document already exists in the database")

        self.root_conn.execute(
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
        self.root_conn.commit()


    def add_document(
            self, subindex_filename, faiss_ids, pages, text_chunks, overwrite=False
    ):
        tmp_db_path = os.path.join(self.subindex_path, f"{subindex_filename}.{_DB_FILE_EXTENSION}")
        tmp_db = sqlite3.connect(tmp_db_path)
        self._create_table(tmp_db, **_document_metadata_table)

        for faiss_id, page, text_chunk in zip(faiss_ids, pages, text_chunks):
            tmp_db.execute(
                f"INSERT INTO {_document_metadata_table['table_name']} (faiss_id, page_number, text_chunk) VALUES (?, ?, ?)",
                (faiss_id, page, text_chunk)
            )
        
        tmp_db.commit()
        tmp_db.close()


    def get_documents_for_ids(self, faiss_ids: list[int]) -> list[str]:
        cursor = self.root_conn.cursor()
        cursor.execute("SELECT file_path FROM root_metadata WHERE faiss_id in (?)", (faiss_ids,))
        return cursor.fetchall()

