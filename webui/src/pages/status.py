import streamlit as st

import remotes.api_models as api_models
import remotes.client as client


def get_service_health_title(service_name: str, service_health: str) -> str:
    healthy = "🟢"
    unhealthy = "🔴"
    return (
        f"#### {healthy if service_health == 'healthy' else unhealthy}"
        f" {service_name}"
    )


if "service_health" not in st.session_state:
    st.session_state.service_health = client.services_health()

st.title("Service status")


st.divider()


st.markdown(get_service_health_title("Backend", st.session_state.service_health.backend.status))
backend_health = st.session_state.service_health.backend
st.write(f"Uptime: {int(backend_health.up_time)} seconds")

st.divider()

st.markdown(get_service_health_title("Datastore", st.session_state.service_health.datastore.status))
datastore_health = st.session_state.service_health.datastore
st.write(f"Uptime: {int(datastore_health.up_time)} seconds")

st.divider()

st.markdown(get_service_health_title("Document converter", st.session_state.service_health.document_converter.status))
document_converter_health = st.session_state.service_health.document_converter
st.write(f"Uptime: {int(document_converter_health.up_time)} seconds")

st.divider()

st.sidebar.markdown(
    "Live status of the services. Click the button below to refresh the status."
    " If the status is unhealthy, a red icon will be displayed, 🔴."
)
if st.sidebar.button("Refresh", icon="🔄"):
    st.session_state.service_health = client.services_health()