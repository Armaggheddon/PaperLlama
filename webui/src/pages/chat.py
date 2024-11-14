import streamlit as st

import remotes.client as client


def stream_response(message):
    history = (
        [] 
        if not st.session_state.include_history 
        else st.session_state.messages
    )
    
    for chunk in client.stream_query(message, history):
        yield chunk

st.sidebar.markdown("## Info")
st.sidebar.markdown("Chat with all the documents in the knowledge base.")
st.sidebar.divider()
st.sidebar.markdown("## Settings")
st.session_state.include_history = st.sidebar.checkbox("Append history to query", value=True)
if st.sidebar.button("Clear chat"):
    st.session_state.messages = []


st.title("Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about transformers"):
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = stream_response(prompt)
        response = st.write_stream(stream)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
