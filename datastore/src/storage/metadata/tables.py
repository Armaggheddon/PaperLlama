_root_table = {
    "table_name": "metadata",
    "columns": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "faiss_id INTEGER",
        "uuid TEXT",
        "document_hash TEXT",
        "document_filename TEXT",
        "summary TEXT"
    ]
}
root_creation_str = (
    f"CREATE TABLE IF NOT EXISTS {_root_table['table_name']} "
    f"({', '.join(_root_table['columns'])})"
)
root_insert_str = (
    f"INSERT INTO {_root_table['table_name']} "
    f"({', '.join([col.split(" ")[0] for col in _root_table['columns'][1:]])}) "
    f"VALUES ({', '.join(['?' for _ in _root_table['columns'][1:]])})"
)
    
_document_table = {
    "table_name": "metadata",
    "columns": [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "faiss_id INTEGER",
        "page_number INTEGER",
        "text TEXT"
    ]
}
document_creation_str = (
    f"CREATE TABLE IF NOT EXISTS {_document_table['table_name']} "
    f"({', '.join(_document_table['columns'])})"
)
document_insert_str = (
    f"INSERT INTO {_document_table['table_name']} "
    f"({', '.join([col.split()[0] for col in _document_table['columns'][1:]])}) "
    f"VALUES ({', '.join(['?' for _ in _document_table['columns'][1:]])})"
)