# PandaAI Platform 

Picture an intelligent assistant that dives into your local knowledge base, harnessing cutting-edge Retrieval Augmented Generation (RAG) 
technology to deliver precise answers to your every question! The PandaAI Platform is a versatile powerhouse, supporting text, images, videos, 
and all sorts of files, while seamlessly adapting to any role—be it a college advisor, customer support guru, technical expert, or even a trusty notetaker. 
Fully customizable and endlessly adaptable, it empowers you to conquer any scenario with ease!

## Features

- Local knowledge base management
- Text chunking and vector embedding
- Support for text and file uploads
- Question answering based on similarity search
- Integration with LM Studio for local generation
- Role selection when handling different user scenario

## Installation

1. Clone the repository
2. Install dependencies


```bash
pip install -r requirements.txt
```



## For Advanced Feature (video and image file input), you can skip this if you only have txt based file!
1. We need Rust compiler(https://www.rust-lang.org/tools/install)

### Install ffmpeg (do not forget this step if you want to upload video : )
1. Install ffmpeg from https://ffmpeg.org/download.html
2. Add ffmpeg to the system path

### Install Tesseract (do not forget this step if you want to upload image : )
1. Install Tesseract from https://github.com/tesseract-ocr/tesseract?tab=readme-ov-file#installing-tesseract
2. Add Tesseract to the system path

```bash
pip install -r videorequirements.txt
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

