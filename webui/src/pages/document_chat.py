import requests
import json
import streamlit as st



def check_document_exists(document_uuid):
    response = requests.get(
        "http://backend:8000/has_document_uuid",
        params={"document_uuid": document_uuid}
    )
    print(response.text)
    if not response.status_code == 200:
        return False
    return response.json()["has_document"]
 
def stream_response(prompt):
    document_request = {
        "document_uuid": st.session_state.current_document_uuid,
        "query_str": prompt,
        "history": []
    }
    stream = requests.post(
        "http://backend:8000/query_document",
        json=document_request,
        stream=True
    )

    for chunk in stream.iter_lines():
        json_chunk = json.loads(chunk)
        yield json_chunk["message"]["content"]

if "document_messages" not in st.session_state:
    st.session_state.document_messages = []
if "current_document_uuid" not in st.session_state:
    st.session_state.current_document_uuid = None


st.title("Document chat")

st.sidebar.markdown("## Settings")
document_uuid = st.sidebar.text_input(label="Document uuid", placeholder="Document uuid")
if st.sidebar.button("Use document"):
    if not check_document_exists(document_uuid):
        st.sidebar.error("Requested document does not exist!")
    else:
        st.sidebar.success("Document is ready!")
        st.session_state.current_document_uuid = document_uuid
st.sidebar.divider()
st.sidebar.markdown("Clear the chat history")
if st.sidebar.button("Clear"):
        st.session_state.document_messages = []

if not st.session_state.current_document_uuid:
    st.warning("Select a document using the sidebar to being the conversation! You can find the document uuid in the Knowledge manager page")
else:
    st.text(f"Using document: {st.session_state.current_document_uuid}" )


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

