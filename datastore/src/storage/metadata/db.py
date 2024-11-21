from pathlib import Path
import sqlite3

from . import tables

from api_models import DocumentInfo


# The extension for the sqlite database files
_EXT = "db"

class MetadataDB:
    """
    Represents a metadata database that stores metadata for documents and
    allows for querying and updating the metadata. It is composed of a root
    database that stores metadata for all documents and sub-databases that
    store metadata for individual documents.
    """
    
    def __init__(
        self,
        data_root: str,
        root_db_name: str,
        sub_index_path: str
    ) -> None:
        """
        Initializes the MetadataDB object with the given parameters.

        Args:
        - data_root (str): The root directory for the database files.
        - root_db_name (str): The name of the root database file.
        - sub_index_path (str): The path to the sub-database files.
        """
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
        """
        Checks if the given document hash is in the metadata database.
        
        Args:
        - document_hash (str): The hash of the document to check.
        
        Returns:
        - bool: True if the document hash is in the metadata database, 
            False otherwise.
        """
        query_str = f"SELECT * FROM metadata WHERE document_hash = ?"
        with self._root_db as conn:
            cursor = conn.execute(query_str, (document_hash,))
            return cursor.fetchone() is not None
        
    def has_document_uuid(
        self,
        document_uuid: str
    ) -> bool:
        """
        Checks if the given document uuid is in the metadata database.

        Args:
        - document_uuid (str): The uuid of the document to check.

        Returns:
        - bool: True if the document uuid is in the metadata database,
            False otherwise.
        """
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
        """
        Adds the given metadata to the root database.
        
        Args:
        - faiss_id (int): The faiss ID (of the root index) of the document.
        - uuid (str): The UUID of the document.
        - document_hash (str): The hash of the document.
        - document_filename (str): The filename of the document.
        - summary (str): The summary of the document.
        """
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
        """
        Removes the document with the given UUID from the root database.
        
        Args:
        - document_uuid (str): The UUID of the document to remove.
        """
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
        """
        Queries the root database with the given faiss IDs and returns the
        UUIDs and summaries of the documents with the given faiss IDs.
        
        Args:
        - faiss_ids (int | list[int]): The faiss ID or list of faiss IDs to query.
        
        Returns:
        - list[tuple[int, str]]: A list of tuples containing the UUIDs and 
            summaries of the documents with the given faiss IDs. Each tuple
            contains the UUID and summary of a document as (uuid, summary).
        """
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
        """
        Adds the given document metadata to the sub-database with the given UUID.
        
        Args:
        - uuid (str): The UUID of the document.
        - faiss_ids (list[int]): The faiss IDs of the document.
        - page_numbers (list[int]): The page numbers of the text chunks.
        - text_chunks (list[str]): The text chunks of the document.
        
        Returns:
        - list[int]: The IDs of the added embeddings.
        """
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
        """
        Queries the sub-database with the given UUID and faiss IDs and returns
        the page numbers and text chunks of the documents with the given 
        faiss IDs.

        Args:
        - uuid (str): The UUID of the document.
        - faiss_ids (list[int]): The faiss IDs of the document.

        Returns:
        - list[tuple[int, str]]: A list of tuples containing the page numbers
            and text chunks of the documents with the given faiss IDs. 
            Each tuple contains the page number and text chunk of a 
            document as (page_number, text).
        """
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
        """
        Gets the metadata for all documents in the root database.
        
        Returns:
        - list[DocumentInfo]: A list of DocumentInfo objects containing the
            metadata for all documents in the root database.
        """
        query_str = f"SELECT uuid, document_hash, document_filename, summary FROM metadata"
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
        
    def get_document_info(
        self,
        document_uuid: str
    ) -> list[DocumentInfo]:
        """
        Gets the metadata for the document with the given UUID.

        Args:
        - document_uuid (str): The UUID of the document to get metadata for.

        Returns:
        - list[DocumentInfo]: A list containing the DocumentInfo object 
            with the metadata for the document with the given UUID.
        """
        query_str = f"SELECT uuid, document_hash, document_filename, summary FROM metadata WHERE uuid = ?"
        with self._root_db as conn:
            cursor = conn.execute(query_str, (document_uuid,))
            row = cursor.fetchone()
            return [DocumentInfo(
                document_uuid=row[0],
                document_hash_str=row[1],
                document_filename=row[2],
                document_summary=row[3]
            )]