import streamlit as st

import remotes.api_models as api_models
import remotes.client as client


def check_document_exists(document_uuid):
    return client.has_document_uuid(document_uuid)


def get_document_info(document_uuid) -> api_models.DocumentInfo:
    return client.document_info(document_uuid)
 

def stream_response(prompt):
    history = (
        []
        if not st.session_state.current_document_include_history
        else st.session_state.document_messages
    )
    document_stream = client.stream_document_query(
        st.session_state.current_document_uuid, prompt, history
    )

    for message in document_stream:
        yield message


if "document_messages" not in st.session_state:
    st.session_state.document_messages = []
if "current_document_uuid" not in st.session_state:
    st.session_state.current_document_uuid = None
if "current_document_info" not in st.session_state:
    st.session_state.current_document_info = None


st.title("Document chat")
st.sidebar.markdown("## Settings")
document_uuid = st.sidebar.text_input(label="Document uuid", placeholder="Document uuid")
if st.sidebar.button("Use document"):
    if not check_document_exists(document_uuid):
        st.sidebar.error("Requested document does not exist!")
        st.session_state.current_document_uuid = None
        st.session_state.current_document_info = None
    else:
        st.sidebar.success("Document is ready!")
        st.session_state.document_messages = []
        st.session_state.current_document_uuid = document_uuid
        st.session_state.current_document_info = get_document_info(document_uuid)
st.sidebar.divider()
st.session_state.current_document_include_history = st.sidebar.checkbox("Append history to query", value=True)
if st.sidebar.button("Clear chat"):
        st.session_state.document_messages = []

if not st.session_state.current_document_uuid:
    st.warning("Select a document using the sidebar to being the conversation! You can find the document uuid in the Knowledge manager page")
else:
    with st.expander(f"Using document: {st.session_state.current_document_uuid}"):
        document_info: api_models.DocumentInfo = st.session_state.current_document_info
        if document_info:
            st.markdown("## Document info")
            st.markdown(f"- document_uuid: {document_info.document_uuid}")
            st.markdown(f"- file_name: {document_info.document_filename}")
            st.markdown(f"- document_hash: {document_info.document_hash_str}")
            
            st.markdown("## Summary")
            st.markdown(f"{document_info.document_summary}")
            st.text("This is the summary of the document...")


for message in st.session_state.document_messages:
     with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.session_state.current_document_uuid and (prompt := st.chat_input("Ask something ...")):

    st.session_state.document_messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = stream_response(prompt)
        response = st.write_stream(stream)

    st.session_state.document_messages.append({
        "role": "assistant",
        "content": response
    })

