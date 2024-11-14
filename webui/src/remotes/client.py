import requests
from typing import Iterable
import json

from . import endpoints
from . import api_models


def upload_file(filename, file_bytes: bytes) -> api_models.UploadFileResponse:
    file = {"document": (filename, file_bytes, "application/pdf")}
    response = requests.post(
        endpoints.ADD_DOCUMENT_URL, 
        files=file,
    )

    if response.status_code != 200:
        return False, response.content
    
    upload_file_response = api_models.UploadFileResponse(
        **response.json()
    )
    return upload_file_response


def stream_query(
    user_query: str,
    history: list[dict[str, str]] = None
) -> Iterable[str]:
    request = {
        "text": user_query,
        "history": history or []
    }

    stream = requests.post(
        endpoints.QUERY_URL,
        json=request,
        stream=True
    )

    for chunk in stream.iter_lines():
        json_chunk = json.loads(chunk)
        yield json_chunk["message"]["content"]

def get_available_documents() -> list[api_models.DocumentInfo]:
    response = requests.get(endpoints.DOCUMENT_INFO_URL)

    if response.status_code != 200:
        raise Exception(response.content)
    
    documents_info_response = api_models.DocumentInfoResponse(
        **response.json()
    )
    return documents_info_response.documents_info


def has_document_uuid(document_uuid: str) -> bool:
    response = requests.get(
        endpoints.HAS_DOCUMENT_UUID_URL,
        params={"document_uuid": document_uuid}
    )
    if not response.status_code == 200:
        return False
    has_document_response = api_models.HasDocumentResponse(
        **response.json()
    )
    return has_document_response.has_document


def document_info(document_uuid: str) -> api_models.DocumentInfo:
    response = requests.get(
        endpoints.DOCUMENT_INFO_URL,
        params={"document_uuid": document_uuid}
    )

    if not response.status_code == 200:
        raise Exception(response.content)
    
    document_info_response = api_models.DocumentInfoResponse(
        **response.json()
    )
    return document_info_response.documents_info[0]


def stream_document_query(
        document_uuid: str,
        user_query: str,
        history: list[dict[str, str]] = None
) -> Iterable[str]:
    
    request = {
        "document_uuid": document_uuid,
        "query_str": user_query,
        "history": history or []
    }

    stream = requests.post(
        endpoints.QUERY_DOCUMENT_URL,
        json=request,
        stream=True
    )

    for chunk in stream.iter_lines():
        json_chunk = json.loads(chunk)
        yield json_chunk["message"]["content"]

def delete_all_documents() -> bool:
    response = requests.delete(endpoints.DELETE_ALL_URL)
    return response.status_code == 200


def delete_document(document_uuid: int) -> bool:
    response = requests.delete(
        endpoints.DELETE_DOCUMENT_URL, 
        params={"document_uuid": document_uuid})
    return response.status_code == 200
