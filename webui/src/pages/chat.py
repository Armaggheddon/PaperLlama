import requests
import json

import streamlit as st


def stream_response(message):
    # _history = [{"role": item["role"], "content": item["content"]} for item in history]
    request = {"text": message, "history": []}
    stream = requests.post("http://backend:8000/query", json=request, stream=True)
    for chunk in stream.iter_lines():
        print(chunk)
        json_chunk = json.loads(chunk)
        # running_response.write(json_chunk["message"]["content"])
        yield json_chunk["message"]["content"]


st.sidebar.markdown("## Settings")
if st.sidebar.button("Clear chat"):
    st.session_state.messages = []


st.title("PaperLlama")
# with st.expander("Details"):
#     st.write('''
#         Example extra text that is displayed on dropdown menu
#     ''')

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
