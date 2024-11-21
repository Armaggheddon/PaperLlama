"""
Contains the client functions to interact with the backend services. 
Abstracting the error handling and response parsing from the user.

The client functions are:
    - upload_file
    - stream_query
    - get_available_documents
    - has_document_uuid
    - document_info
    - stream_document_query
"""

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

    if not response or response.status_code != 200:
        return api_models.UploadFileResponse(
            is_success=False,
            message=response.content
        )
    
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

def delete_all_documents() -> api_models.DeleteDocumentResponse:
    response = requests.delete(endpoints.DELETE_ALL_URL)
    if not response or response.status_code != 200:
        return api_models.DeleteDocumentResponse(
            is_success=False,
            error_message=response.content
        )
    
    delete_document_response = api_models.DeleteDocumentResponse(
        **response.json()
    )
    return delete_document_response


def delete_document(document_uuid: int) -> api_models.DeleteDocumentResponse:
    response = requests.delete(
        endpoints.DELETE_DOCUMENT_URL, 
        params={"document_uuid": document_uuid})
    if not response or response.status_code != 200:
        return api_models.DeleteDocumentResponse(
            is_success=False,
            error_message=response.content
        )
    delete_document_response = api_models.DeleteDocumentResponse(
        **response.json()
    )
    return delete_document_response
 

def services_health() -> api_models.HealthCheckResponse:
    response = requests.get(endpoints.SERVICES_HEALTH_URL)
    if not response or response.status_code != 200:
        return api_models.HealthCheckResponse(
            backend=api_models.ServiceHealth(
                up_time=0, 
                status="unhealthy"
            ),
            datastore=api_models.ServiceHealth(
                up_time=0, 
                status="unhealthy"
            ),
            document_converter=api_models.ServiceHealth(
                up_time=0, 
                status="unhealthy"
            )
        )
    
    health_check_response = api_models.HealthCheckResponse(
        **response.json()
    )
    return health_check_response