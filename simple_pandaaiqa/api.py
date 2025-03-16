"""
PandaAIQA API
Provides Web interface for querying and file uploads
"""

import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends,
    APIRouter,
    BackgroundTasks,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from simple_pandaaiqa.text_processor import TextProcessor
from simple_pandaaiqa.pdf_processor import PDFProcessor

# from simple_pandaaiqa.video_processor import VideoProcessor
from simple_pandaaiqa.embedder import Embedder
from simple_pandaaiqa.vector_store import VectorStore
from simple_pandaaiqa.generator import Generator
from simple_pandaaiqa.utils.helpers import extract_file_extension
from simple_pandaaiqa.config import MAX_TEXT_LENGTH

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Define API models
class QueryRequest(BaseModel):
    text: str = Field(..., description="Query text")
    top_k: int = Field(3, description="Maximum number of results to return")


class QueryResponse(BaseModel):
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    context: List[Dict[str, Any]] = Field(..., description="Relevant context")


class StatusResponse(BaseModel):
    status: str = Field(..., description="System status")
    document_count: int = Field(
        ..., description="Number of documents in the knowledge base"
    )


class LMStudioStatusResponse(BaseModel):
    connected: bool = Field(..., description="LM Studio连接状态")
    message: str = Field(..., description="连接状态消息")
    api_base: str = Field(..., description="LM Studio API基础URL")


class MessageResponse(BaseModel):
    message: str = Field(..., description="Response message")


class SaveRequest(BaseModel):
    directory: str = Field(..., description="Directory to save the knowledge base")


class LoadRequest(BaseModel):
    directory: str = Field(..., description="Directory to load the knowledge base from")


# Create FastAPI application
app = FastAPI(title="PandaAIQA", description="本地知识问答系统")

# Initialize components
text_processor = TextProcessor()
pdf_processor = PDFProcessor()
embedder = Embedder()
vector_store = VectorStore(embedder=embedder)
generator = Generator()

# Create routers
main_router = APIRouter(prefix="/api")
docs_router = APIRouter(prefix="/api/docs")

# Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define dependency for components
def get_components():
    return {
        "text_processor": text_processor,
        "vector_store": vector_store,
        "generator": generator,
        "pdf_processor": pdf_processor,
        # "video_processor": video_processor,
    }


@app.get("/")
async def root():
    """Root path endpoint, returns the frontend page"""
    return FileResponse("simple_pandaaiqa/static/index.html")


@main_router.post("/upload", response_model=MessageResponse)
async def upload_file(
    file: UploadFile = File(...), components: Dict[str, Any] = Depends(get_components)
):
    """Upload a file and process its content"""
    try:
        logger.info(f"Uploading file: {file.filename}")

        # check file type
        ext = extract_file_extension(file.filename)
        if ext not in ["txt", "md", "csv", "pdf", "mp4"]:
            logger.warning(f"Unsupported file type: {ext}")
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"Unsupported file type: {ext}. Only txt, md, and csv files are supported"
                },
            )

        # read file content
        content = await file.read()

        # check file size
        if (
            len(content) > MAX_TEXT_LENGTH * 2
        ):  # allow file to be slightly larger than pure text
            logger.warning(f"File too large: {len(content)} bytes")
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"File too large. Maximum allowed size is {MAX_TEXT_LENGTH * 2} bytes"
                },
            )

        documents = []
        metadata = {"source": file.filename, "type": ext}

        if ext in ["txt", "md", "csv"]:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text = content.decode("latin-1")
                    logger.info("Using latin-1 encoding to decode file")
                except:
                    logger.error("Failed to decode file content")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "message": "Failed to decode file content. Ensure the file is a valid text file."
                        },
                    )
            documents = components["text_processor"].process_text(text, metadata)
        elif ext == "pdf":
            documents = components["pdf_processor"].process_pdf(content, metadata)
        # else:  # video files
        # text = components["video_processor"].extract_text_from_video(content)

        # # decode text
        # try:
        #     text = content.decode("utf-8")
        # except UnicodeDecodeError:
        #     # try other encodings
        #     try:
        #         text = content.decode("latin-1")
        #         logger.info("Using latin-1 encoding to decode file")
        #     except:
        #         logger.error("Failed to decode file content")
        #         return JSONResponse(
        #             status_code=400,
        #             content={
        #                 "message": "Failed to decode file content. Please ensure the file is a valid text file"
        #             },
        #         )

        # # process text
        # # metadata = {"source": file.filename, "type": "file"}
        # documents = components["text_processor"].process_text(text, metadata)

        if not documents:
            logger.warning("No documents generated from file")
            return JSONResponse(
                status_code=400,
                content={"message": "No documents generated from uploaded file"},
            )

        # extract text and metadata
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]

        # add to vector store
        components["vector_store"].add_texts(texts, metadatas)
        logger.info(f"Successfully processed {len(documents)} documents from file")

        return {
            "message": f"Successfully processed {len(documents)} documents from {file.filename}"
        }

    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@main_router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest, components: Dict[str, Any] = Depends(get_components)
):
    """process query and return answer"""
    try:
        logger.info(f"Processing query: {request.text}")

        # search related documents
        results = components["vector_store"].search(request.text, top_k=request.top_k)

        if not results:
            logger.warning("No documents found related to the query")
            return {
                "query": request.text,
                "answer": "No relevant information found.",
                "context": [],
            }

        # generate answer
        answer = components["generator"].generate(request.text, results)
        logger.info("Generated answer for the query")

        return {"query": request.text, "answer": answer, "context": results}

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@main_router.get("/status", response_model=StatusResponse)
async def status(components: Dict[str, Any] = Depends(get_components)):
    """get system status"""
    try:
        doc_count = len(components["vector_store"].documents)
        logger.info(f"Status request: {doc_count} documents in vector store")
        return {"status": "ready", "document_count": doc_count}
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@main_router.delete("/clear", response_model=MessageResponse)
async def clear(components: Dict[str, Any] = Depends(get_components)):
    """clear all documents"""
    try:
        components["vector_store"].clear()
        logger.info("Vector store cleared")
        return {"message": "All documents have been cleared"}
    except Exception as e:
        logger.error(f"Error clearing vector store: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@main_router.get("/lm-status", response_model=LMStudioStatusResponse)
async def lm_studio_status(components: Dict[str, Any] = Depends(get_components)):
    """check LM Studio connection status"""
    try:
        generator = components["generator"]
        is_connected, message = generator.check_connection()
        logger.info(f"LM Studio connection status check: {is_connected}, {message}")

        return {
            "connected": is_connected,
            "message": message,
            "api_base": generator.api_base,
        }
    except Exception as e:
        logger.error(f"Error checking LM Studio status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@main_router.post("/save", response_model=MessageResponse)
async def save_knowledge_base(
    request: SaveRequest, components: Dict[str, Any] = Depends(get_components)
):
    """Save the current knowledge base to disk"""
    try:
        logger.info(f"Saving knowledge base to {request.directory}")

        # Ensure directory exists
        os.makedirs(request.directory, exist_ok=True)

        # Save vector store
        success = components["vector_store"].save_to_disk(request.directory)

        if success:
            return {
                "message": f"Successfully saved knowledge base to {request.directory}"
            }
        else:
            return JSONResponse(
                status_code=500, content={"message": "Failed to save knowledge base"}
            )

    except Exception as e:
        logger.error(f"Error saving knowledge base: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@main_router.post("/load", response_model=MessageResponse)
async def load_knowledge_base(
    request: LoadRequest, components: Dict[str, Any] = Depends(get_components)
):
    """Load a knowledge base from disk"""
    try:
        logger.info(f"Loading knowledge base from {request.directory}")

        # Check if directory exists
        if not os.path.exists(request.directory):
            return JSONResponse(
                status_code=404,
                content={"message": f"Directory {request.directory} does not exist"},
            )

        # Load vector store
        success = components["vector_store"].load_from_disk(request.directory)

        if success:
            doc_count = len(components["vector_store"].documents)
            return {
                "message": f"Successfully loaded knowledge base with {doc_count} documents"
            }
        else:
            return JSONResponse(
                status_code=500, content={"message": "Failed to load knowledge base"}
            )

    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files
app.mount("/static", StaticFiles(directory="simple_pandaaiqa/static"), name="static")

# Include routers
app.include_router(main_router)
app.include_router(docs_router)
