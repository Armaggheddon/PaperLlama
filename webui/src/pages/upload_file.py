import io
import requests
import streamlit as st


def upload_file(filename, file_bytes: bytes) -> tuple[bool, str]:
    file = {"document": (filename, file_bytes, "application/pdf")}
    response = requests.post("http://backend:8000/add_document", files=file,
                             )
    if response.status_code != 200:
        return (False, response.content)
    
    response_data = response.json()
    return (response_data["is_success"], response_data["message"])
    

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

    

