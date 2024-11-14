import streamlit as st

import remotes.client as client


def upload_file(filename, file_bytes: bytes) -> tuple[bool, str]:
    response = client.upload_file(
        filename, 
        file_bytes
    )
    return response.is_success, response.message

st.title("Upload new file")

uploaded_file = st.file_uploader("Upload a pdf file", type="pdf")
if uploaded_file is not None:
    
    bytes_data = uploaded_file.getvalue()

    st.warning("Do not change page while the file is being processed!")

    # todo send request
    success, reason = upload_file(uploaded_file.name, bytes_data)

    if success:
        st.success("File succesfully added!")
    else:
        st.error(f"File upload failed: {reason}")

    

