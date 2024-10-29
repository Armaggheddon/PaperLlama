import io

import gradio as gr
from ollama import Client

client = Client(host="http://ollama:11434")
print(client.list())
if "llama3.2:1b" not in client.list():
    client.pull("llama3.2:1b")

def response(message, history):
    print(f"Message: {message}")
    print(f"History: {history}")
    _history = [{"role": item["role"], "content": item["content"]} for item in history]
    stream = client.chat(
        model="llama3.2:1b",
        messages=[*_history, {"role": "user", "content": message["text"]}],
        stream=True,
    ) 
    full_response = io.StringIO()
    for chunk in stream:
        print(chunk)
        full_response.write(chunk["message"]["content"])
        yield full_response.getvalue()
    

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