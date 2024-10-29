import io
from dataclasses import dataclass

import PyPDF2 


@dataclass
class Page:
    page_number: int
    text: str

@dataclass
class Chunk:
    page_number: int
    text: str


def convert(pdf_file: str | bytes) -> str:
    
    # if is a file path, it is an online file
    # TODO: try to download it

    if not isinstance(pdf_file, bytes):
        return "Not implemented"
    

    pdf = PyPDF2.PdfFileReader(pdf_file)
    # pages = []

    content = io.StringIO()
    for page_number, page_content in enumerate(pdf.pages):
        # pages.append(
        #     Page(
        #         page_number=page_number,
        #         text=page_content.extract_text()
        #     )
        # )
        content.write(page_content.extract_text())
        
    return content.getvalue()

def to_chunks(pdf_file: str | bytes, chunk_size: int, overlap: int) -> list[str]:
    content = convert(pdf_file)
    
    chunks = []
    offset = chunk_size
    while offset < len(content):
        start = offset - overlap
        end = start + chunk_size
        chunks.append(content[start:end])
        offset += chunk_size - overlap
    return chunks
    