import io
import httpx
import requests
import json

import gradio as gr

headers = {}
headers["Content-Type"] = "application/json"
headers["Accept"] = "application/json"
backend_client = httpx.Client(
    base_url="http://backend:8000",
    follow_redirects=True,
    timeout=None,
    headers=headers
)

def streaming_response(message):
    def inner():
        with httpx.stream("GET", "http://backend:8000/query", params={"text": message}) as r:
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                e.response.read()
                raise RuntimeError(e.response.text, e.response.status_code) from None

            for line in r.iter_lines():
                partial = json.loads(line)
                if e := partial.get('error'):
                    raise RuntimeError(e)
                yield partial
    
    return inner()

def response(message, history):
    # _history = [{"role": item["role"], "content": item["content"]} for item in history]
    stream = requests.get("http://backend:8000/query", params={"text": message["text"]}, stream=True)
    running_response = io.StringIO()
    for chunk in stream.iter_lines():
        print(chunk)
        json_chunk = json.loads(chunk)
        running_response.write(json_chunk["message"]["content"])
        yield running_response.getvalue()
    

def add_data(text):
    print(f"Data: {text}")
    return "Data added successfully"

def delete_user_files(req: gr.Request):
    pass



chat_ui = gr.ChatInterface(
    fn=response,
    type="messages",
    title="PaperLlama",
    multimodal=True,
    delete_cache=(3600, 1000),
)

data_add_ui = gr.Interface(
    fn=add_data,
    inputs=["text"],
    outputs="text",
)

iface = gr.TabbedInterface([chat_ui, data_add_ui], tab_names=["Chat", "Add Data"])

# iface.unload(delete_user_files)
iface.launch(server_name="0.0.0.0", server_port=80)