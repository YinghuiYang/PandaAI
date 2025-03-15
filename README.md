# PandaAIQA - Local Knowledge Question Answering System

PandaAIQA is a simple local knowledge question answering system that supports answering questions based on Retrieval Augmented Generation (RAG) technology.

## Features

- Local knowledge base management
- Text chunking and vector embedding
- Support for text and file uploads
- Question answering based on similarity search
- Integration with LM Studio for local generation

## Installation

1. Clone the repository
2. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Run the following command to start the service:

```bash
python -m simple_pandaaiqa.app
```

Then access in your browser: http://localhost:8000

## Technology Stack

- **Backend**: FastAPI, Python
- **Frontend**: HTML, CSS, JavaScript
- **Embedding**: LM Studio API integration
- **Text Generation**: LM Studio API integration

## LM Studio Integration

This project supports integration with [LM Studio](https://lmstudio.ai/) to provide higher quality answer generation.

Steps to use:
1. Install LM Studio locally and start the server
2. Make sure LM Studio is listening on http://localhost:1234
3. Configure the API endpoints in `config.py`
4. Start the LM Studio Server

If LM Studio cannot be connected, the system will automatically display an error message.