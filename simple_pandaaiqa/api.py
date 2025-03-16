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
    Request,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from simple_pandaaiqa.text_processor import TextProcessor
from simple_pandaaiqa.pdf_processor import PDFProcessor
from simple_pandaaiqa.video_processor import VideoProcessor
from simple_pandaaiqa.image_processor import ImageProcessor

from simple_pandaaiqa.embedder import Embedder
from simple_pandaaiqa.vector_store import VectorStore
from simple_pandaaiqa.generator import Generator
from simple_pandaaiqa.summarize_generator import SummarizeGenerator
from simple_pandaaiqa.utils.helpers import extract_file_extension
from simple_pandaaiqa.config import MAX_TEXT_LENGTH
from simple_pandaaiqa.role_generators import get_role_generator
from tempfile import NamedTemporaryFile
import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Define API models
class QueryRequest(BaseModel):
    text: str = Field(..., description="Query text")
    top_k: int = Field(3, description="Maximum number of results to return")
    role: str = Field(None, description="Role for the query")


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
    connected: bool = Field(..., description="LM Studio connection status")
    message: str = Field(..., description="connection status message")
    api_base: str = Field(..., description="LM Studio API base URL")


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
video_processor = VideoProcessor()
image_processor = ImageProcessor()

embedder = Embedder()
vector_store = VectorStore(embedder=embedder)
generator = Generator()
summarize_generator = SummarizeGenerator()

# create global components dictionary
COMPONENTS = {
    "text_processor": text_processor,
    "vector_store": vector_store,
    "generator": generator,
    "pdf_processor": pdf_processor,
    "video_processor": video_processor,
    "image_processor": image_processor,
    "summarize_generator": summarize_generator
}

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
        
    return COMPONENTS


@app.on_event("startup")
async def startup_event():
    """initialize components"""
    app.state.components = COMPONENTS
    logger.info("application started, components initialized")


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
        if ext not in [
            "txt",
            "md",
            "csv",
            "pdf",
            "mp4",
            "jpg",
            "jpeg",
            "png",
            "bmp",
            "gif",
        ]:
            logger.warning(f"Unsupported file type: {ext}")
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"Unsupported file type: {ext}. Only txt, md, csv, pdf, mp4, jpg, jpeg, png, bmp, gif are supported"
                },
            )

        # read file content
        content = await file.read()

        # check file size
        if (
            len(content) > MAX_TEXT_LENGTH * 2
        ):  # allow file to be slightly larger than pure text
            logger.warning(f"File too small: {len(content)} bytes")
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"File too small. Maximum allowed size is {MAX_TEXT_LENGTH * 2} bytes"
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
        elif ext in ["jpg", "jpeg", "png", "bmp", "gif"]:
            documents = components["image_processor"].process_image(content)
        else:  # video files
            with NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                video_file_path = tmp_file.name
            documents = components["video_processor"].process_video(
                video_file_path, metadata
            )

            os.unlink(tmp_file.name)

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

        # Get the appropriate generator for the role
        generator = get_role_generator(request.role)

        # Generate answer
        answer = generator.generate(request.text, results)
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


# safe get vector store dependency function
def get_vector_store():
    """safe get global vector_store object"""
    return vector_store

# safe get summarize generator dependency function
def get_summarize_generator():
    """safe get or create summarize generator"""
    return summarize_generator

@app.post("/api/summarize")
async def generate_summary():
    """generate summary of all documents in the knowledge base"""
    import traceback
    try:
    
        
        # check current vector store
        current_vs = None
        
        # try to get existing vector store
        try:
            # first try to use global variable
            if 'vector_store' in globals() and globals()['vector_store'] is not None:
                current_vs = globals()['vector_store']
                logger.info("using global vector store")
            # then try to get from COMPONENTS
            elif 'COMPONENTS' in globals() and globals()['COMPONENTS'].get('vector_store') is not None:
                current_vs = globals()['COMPONENTS']['vector_store']
                logger.info("using vector store from COMPONENTS")
        except Exception as e:
            logger.error(f"error getting existing vector store: {e}")
            # continue to execute, we will create a new vector store
        
        # if cannot get existing vector store, create a new one
        if current_vs is None:
            logger.info("creating new vector store")
            temp_embedder = Embedder()
            current_vs = VectorStore(embedder=temp_embedder)
        
        # get documents
        documents = getattr(current_vs, 'documents', [])
        logger.info(f"retrieved {len(documents)} documents for summary")
        
        if not documents:
            return JSONResponse(
                status_code=200,
                content={"summary": "no documents in the knowledge base. please upload documents first."}
            )
        
        # create summarize generator and generate summary
        summarizer = SummarizeGenerator()
        summary = summarizer.generate_summary(documents)
        
        return JSONResponse(
            status_code=200,
            content={"summary": summary}
        )
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"error generating summary: {e}\n{error_trace}")
        return JSONResponse(
            status_code=500,
            content={"error": f"error generating summary: {str(e)}"}
        )


@app.post("/api/visualization")
async def get_visualization_data():
    """get knowledge base document visualization data"""
    try:
        # get all documents from vector store
        if 'vector_store' not in globals() or globals()['vector_store'] is None:
            return JSONResponse(
                status_code=500,
                content={"error": "vector store not initialized"}
            )
        
        # get all documents from vector store
        vs = globals()['vector_store']
        documents = getattr(vs, 'documents', [])
        logger.info(f"retrieved {len(documents)} documents for visualization")
        
        if not documents:
            return JSONResponse(
                status_code=200,
                content={"nodes": [], "edges": [], "message": "no documents in the knowledge base"}
            )
        
        # extract texts and metadata
        texts = []
        doc_names = []
        
        for i, doc in enumerate(documents):
            text = doc.get("text", "")
            if not text:
                continue
                
            texts.append(text)
            
            # get document name
            metadata = doc.get("metadata", {})
            source = metadata.get("source", f"document {i+1}")
            doc_names.append(source)
        
        # if there are at least 2 documents, calculate document similarity
        if len(texts) >= 2:
            # use TF-IDF to vectorize texts
            vectorizer = TfidfVectorizer(max_features=100)
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # use PCA to reduce document vectors to 2D space for visualization
            pca = PCA(n_components=2)
            coords = pca.fit_transform(tfidf_matrix.toarray())
            
            # calculate document similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = cosine_similarity(tfidf_matrix)
            
            # create nodes and edges
            nodes = []
            edges = []
            
            # add nodes
            for i, name in enumerate(doc_names):
                nodes.append({
                    "id": i,
                    "name": name,
                    "x": float(coords[i][0]),
                    "y": float(coords[i][1]),
                    "size": len(texts[i]) / 1000  # set node size based on text length
                })
            
            # add edges (only keep high similarity connections)
            for i in range(len(texts)):
                for j in range(i+1, len(texts)):
                    if similarity[i, j] > 0.2:  # similarity threshold
                        edges.append({
                            "source": i,
                            "target": j,
                            "weight": float(similarity[i, j])
                        })
            
            return JSONResponse(
                status_code=200,
                content={"nodes": nodes, "edges": edges}
            )
        else:
            # insufficient documents to create network graph
            return JSONResponse(
                status_code=200,
                content={"message": "insufficient documents to create visualization"}
            )
            
    except Exception as e:
        logger.exception(f"error generating visualization data: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"error generating visualization data: {str(e)}"}
        )


# Mount static files
app.mount("/static", StaticFiles(directory="simple_pandaaiqa/static"), name="static")

# Include routers
app.include_router(main_router)
app.include_router(docs_router)
