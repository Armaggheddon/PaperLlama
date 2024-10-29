import os
import pathlib
import sqlite3

from parser.types import PDFFile

class MetadataDB:
    def __init__(self, data_root: str, subindex_path: str, root_db_name: str):

        self.subindex_path = subindex_path

        if not os.path.isdir(data_root):
            os.makedirs(data_root)

        self.db_path = pathlib.Path(data_root) / root_db_name
        self.conn = sqlite3.connect(str(self.db_path))

        # create the table if it does not exist
        self._create_table(
            table_name="root_metadata",
            columns=[
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "faiss_id INTEGER",
                "subindex_filename TEXT",
                "pdffile_path TEXT",
                "document_hash TEXT",
                "document_summary TEXT",
            ]
        )
    
    def _create_table(self, table_name: str, columns: list[str]):
        columns_str = ", ".join(columns)
        self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})")
        self.conn.commit()

    def close(self):
        self.conn.close()

    def add_document_to_root(
        self, 
        faiss_id: int, 
        subindex_filename: str, 
        pdf_file_path: str,
        document_hash: str,
        document_summary: str
    ):
        
        # ensure that no other file with the same faiss_id or document_hash exists
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM root_metadata WHERE faiss_id = ? OR document_hash = ?",
            (faiss_id, document_hash)
        )
        if cursor.fetchone():
            raise ValueError("Document already exists in the database")

        self.conn.execute(
            "INSERT INTO root_metadata "
            "(faiss_id, subindex_filename, pdffile_path, document_hash, document_summary) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                faiss_id, 
                subindex_filename, 
                pdf_file_path, 
                document_hash, 
                document_summary
            )
        )
        self.conn.commit()

    def create_db_for_document(self, db_name: str, faiss_ids: list[int], pages: list[int], text_chunks: list[str]):

        db_path = pathlib.Path(self.subindex_path) / db_name
        conn = sqlite3.connect(str(db_path))

        # create the table if it does not exist
        self._create_table(
            table_name="document_metadata",
            columns=[
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "faiss_id INTEGER",
                "page_number INTEGER",
                "text_chunk TEXT",
            ]
        )

        for faiss_id, page_number, text_chunk in zip(faiss_ids, pages, text_chunks):
            conn.execute(
                "INSERT INTO document_metadata (faiss_id, page_number, text_chunk) VALUES (?, ?, ?)",
                (faiss_id, page_number, text_chunk)
            )

        conn.commit()
        conn.close()


    def get_documents_for_ids(self, faiss_ids: list[int]) -> list[str]:

        cursor = self.conn.cursor()
        cursor.execute("SELECT file_path FROM root_metadata WHERE faiss_id in (?)", (faiss_ids,))
        return cursor.fetchall()

