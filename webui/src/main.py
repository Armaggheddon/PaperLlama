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
    

def delete_user_files(req: gr.Request):
    pass



iface = gr.ChatInterface(
    fn=response,
    type="messages",
    title="PaperLlama",
    multimodal=True,
    delete_cache=(3600, 1000),
)
# iface.unload(delete_user_files)
iface.launch(server_name="0.0.0.0", server_port=80)