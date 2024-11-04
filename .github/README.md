<div id="top"></div>
<br/>
<br/>
<br/>


<p align="center">
  <img src="images/paper_llama_nobg_border.png" width="180">
</p>
<h1 align="center">
    <a href="https://github.com/Armaggheddon/PaperLlama">PaperLlama</a>
</h1>
<p align="center">
    <a href="https://github.com/Armaggheddon/PaperLlama/commits/master">
    <img src="https://img.shields.io/github/last-commit/Armaggheddon/PaperLlama">
    </a>
    <a href="https://github.com/Armaggheddon/PaperLlama">
    <img src="https://img.shields.io/badge/Maintained-yes-green.svg">
    </a>
    <a href="https://github.com/Armaggheddon/PaperLlama/issues">
    <img src="https://img.shields.io/github/issues/Armaggheddon/PaperLlama">
    </a>
    <a href="https://github.com/Armaggheddon/PaperLlama/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/Armaggheddon/PaperLlama">
    </a>
</p>
<p align="center">
    Your fully local, AI-powered Q&A assistant—meet PaperLlama!
    <br/>
    <br/>
    <a href="https://github.com/Armaggheddon/PaperLlama/issues">Report Bug</a>
    •
    <a href="https://github.com/Armaggheddon/PaperLlama/issues">Request Feature</a>
</p>

---

Welcome to **PaperLlama**! 🦙🎓 Your personal academic assistant that’s powered up and ready to help you sift through stacks of papers, PDFs, and academic docs for those *must-have* insights! Using a combo of state-of-the-art AI magic (thanks to Ollama's LLaMA 3.2 models) and custom-built tech, PaperLlama makes document-based Q&A a breeze.


## 🏗️ Project Components
PaperLlama is made up of three powerhouse components:

1. **🦙 Ollama**
    - TODO

1. **🚀 Backend**
    - TODO

1. **🖥️ Web UI**
    - TODO

## 🖼️ User Interface Overview
Here's a quick tour of what's on the PaperLlama dashboard!

### 💬 Chat Interface
The heart of PaperLlama! Ask questions directly here, and get answers powered by your uploaded documents. Perfect for digging into those long reports and finding what you need fast.

### 📚 Knowledge Manager
This page is your overview of everything PaperLlama has indexed. You’ll see all the uploaded documents, metadata, and the data that can be used for generating answers.

### 📂 PDF Uploader
Got more PDFs? Head here to add them to PaperLlama. Each upload is automatically embedded and indexed so it’s ready for action.

> [!NOTE]
> For now, we only support PDFs. But we’re always working on expanding to more document types! 📄✨


## 🚀 Getting Started
With **Docker Compose**, you can spin up the whole PaperLlama suite in one go! Here's how:
1. Clone the repository:
    ```bash
    git clone https://github.com/Armaggheddon/PaperLlama.git
    cd PaperLlama
    ```

1. Chose either the `docker-compose.yml` for cpu-only setups or `gpu-docker-compose.yml` if you have an Nvidia GPU. Launch the containers with
    ```bash
    docker compose up -f <compose_file> up -d
    ```

1. Once everything's up, navigate to `http://localhost:8501` to start using PaperLlama. 

1. Start Exploring! Upload a PDF, ask a question, and let PaperLlama pull the info you need in seconds!

> [!NOTE]
> GPU support requires the NVIDIA Container Toolkit. Look [here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) for the installation guide.