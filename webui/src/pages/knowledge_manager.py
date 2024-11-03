import requests

import pandas as pd
import streamlit as st


def get_available_files() -> list[dict[int, str, str]]:
    response = requests.get("http://backend:8000/available_documents")
    
    json_response = response.json()
    formatted = {}
    for entry in json_response:
        _id = entry["id"]
        _file_name = entry["user_filename"]
        _summary = entry["document_summary"]

        formatted[_id] = {"file_name": _file_name, "summary": _summary}

    return formatted

def delete_all_files_request():
    data = {"confirm": True}
    response = requests.post("http://backend:8000/delete_all", json=data)
    print(response.text)

def batch_delete_request(ids_to_delete: list[int]):
    data = {"index_ids": ids_to_delete}
    response = requests.post("http://backend:8000/delete_document_by_id", json=data)
    print(response.text)


event = None

@st.dialog("Are you sure?")
def delete_files(delete_all: bool):
    def on_click_yes():
        if delete_all:
            delete_all_files_request()
            st.session_state.pop("files")
        else:
            if event and event.selection:
                ids_to_delete = data_df.iloc[event.selection["rows"]]["file_id"].tolist()
                batch_delete_request(ids_to_delete)
                st.session_state.pop("files")
                event.selection.clear()
        st.rerun()

    def on_click_no():
        st.rerun()

    if event and event.selection:
        # selected = data_df.iloc[event.selection["rows"]]
        ids_to_delete = data_df.iloc[event.selection["rows"]]["file_id"].tolist()
        print(ids_to_delete)

    if delete_all:
        st.markdown("All the data will be permanently deleted")
    else:
        st.markdown("The selected data will be deleted permanently")
    cols = st.columns(spec=[0.5, 0.5])
    with cols[0]:
        if st.button("Cancel"):
            on_click_no()
    with cols[1]:
        if st.button("Yes", type="primary"):
            on_click_yes()



if "files" not in st.session_state:
    st.session_state["files"] = get_available_files()


st.title("Manage knowledge")
st.markdown(
    "This page allows you to manage the documents that the model "
    "can access for contextual information. Here, you can view a "
    "list of all uploaded documents that the model references when "
    "generating responses. To keep the knowledge base relevant and "
    "up-to-date, you can delete any documents you no longer need or "
    "that are outdated. This helps ensure the model only has access "
    "to accurate and essential information for generating responses."
)


st.divider()
cols = st.columns(3)
with cols[0]:
    if st.button("Refresh", icon="🔃"):
        st.session_state.pop("files")
        st.rerun()
with cols[1]:
    st.button("Delete selected", type="secondary", on_click=delete_files, args=[False])
with cols[2]:
    st.button("Delete all", type="primary", on_click=delete_files, args=[True])
st.divider()


if len(st.session_state["files"]) != 0:
    
    data_df = pd.DataFrame(
        {
            "file_id": [file_id for file_id in st.session_state["files"].keys()],
            "File name": [info["file_name"] for info in st.session_state["files"].values()],
            "Summary": [info["summary"] for info in st.session_state["files"].values()]
        }
    )
    event = st.dataframe(
        data_df,
        column_order=("File name", "Summary"),
        use_container_width=True,
        hide_index=True,
        on_select="rerun"
    )
      

else:
    st.subheader("It looks like there are no documents available, upload a new one!")