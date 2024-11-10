import streamlit as st


st.logo(
    image="src/paper_llama_nobg.png", 
    icon_image="src/paper_llama_nobg.png", 
    size="large")

pages = st.navigation([
    st.Page("pages/chat.py", title="Chat", icon="🤖"),
    # st.Page("pages/knowledge_manager.py", title="Knowledge manager", icon="🧠"),
    # st.Page("pages/upload_file.py", title="Upload new", icon="⚡")
])

pages.run()