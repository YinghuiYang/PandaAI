"""
Vector Store module for PandaAIQA
Uses llama_index VectorStoreIndex for efficient document storage and retrieval
"""

import logging
import os
from typing import List, Dict, Any, Optional, Union
import numpy as np

from llama_index.core import Document as LlamaDocument
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import NodeWithScore
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from simple_pandaaiqa.config import DEFAULT_TOP_K, CHUNK_SIZE, CHUNK_OVERLAP
from simple_pandaaiqa.embedder import Embedder

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store using llama_index for document storage and retrieval"""
    
    def __init__(self, embedder: Optional[Embedder] = None):
        """Initialize vector store"""
        self.embedder = embedder
        # 创建文档存储和存储上下文
        self.document_store = SimpleDocumentStore()
        self.storage_context = StorageContext.from_defaults(
            docstore=self.document_store
        )
        
        self.node_parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        
        # 使用HuggingFace嵌入模型
        self.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # 设置全局嵌入模型
        Settings.embed_model = self.embed_model
            
        self.index = None
        self.documents = []  # Keep for backward compatibility
        logger.info("Initialized vector store with llama_index")
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """
        Add multiple text documents to the store
        
        Args:
            texts: List of document texts
            metadatas: Optional list of metadata dictionaries
            
        Returns:
            List of indices for the added documents
        """
        try:
            if not texts:
                logger.warning("Empty list of texts provided")
                return []
                
            # Process metadatas
            if metadatas is None:
                metadatas = [{} for _ in texts]
            elif len(metadatas) != len(texts):
                logger.warning("Length of metadatas doesn't match length of texts")
                metadatas = metadatas[:len(texts)] + [{} for _ in range(len(texts) - len(metadatas))]
            
            # Create llama_index Documents
            llama_docs = []
            for i, (text, metadata) in enumerate(zip(texts, metadatas)):
                doc_id = f"doc_{len(self.documents) + i}"
                llama_doc = LlamaDocument(
                    text=text,
                    metadata=metadata,
                    doc_id=doc_id
                )
                llama_docs.append(llama_doc)
                
                # Keep track of documents for backward compatibility
                self.documents.append({"text": text, "metadata": metadata})
            
            # Create or update the index
            if self.index is None:
                # 使用当前设置的embedding模型
                self.index = VectorStoreIndex.from_documents(
                    llama_docs,
                    storage_context=self.storage_context,
                    transformations=[self.node_parser]
                )
            else:
                self.index.insert_nodes(
                    self.node_parser.get_nodes_from_documents(llama_docs)
                )
            
            logger.info(f"Added {len(texts)} documents to vector store")
            return list(range(len(self.documents) - len(texts), len(self.documents)))
            
        except Exception as e:
            logger.error(f"Error adding texts: {e}", exc_info=True)
            return []
    
    def add_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Add a single text document to the store
        
        Args:
            text: Document text
            metadata: Optional metadata
            
        Returns:
            Index of the added document
        """
        try:
            result = self.add_texts([text], [metadata] if metadata else None)
            return result[0] if result else -1
        except Exception as e:
            logger.error(f"Error adding text: {e}", exc_info=True)
            return -1
    
    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing document text, metadata, and score
        """
        try:
            if not self.index or len(self.documents) == 0:
                logger.warning("Vector store is empty, no documents to search")
                return []
            
            # Create retriever with specified top_k
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=top_k
            )
            
            # Retrieve nodes
            nodes = retriever.retrieve(query)
            
            # Format results
            results = []
            for node in nodes:
                # Try to find original document by matching text and metadata
                source_doc = None
                node_text = node.node.text if hasattr(node, 'node') else node.text
                node_metadata = node.node.metadata if hasattr(node, 'node') else node.metadata
                
                # Format result
                result = {
                    "text": node_text,
                    "metadata": node_metadata,
                    "score": float(node.score) if hasattr(node, 'score') else 0.0
                }
                results.append(result)
                
            logger.info(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}", exc_info=True)
            return []
    
    def clear(self) -> None:
        """Clear all documents and vectors from the store"""
        try:
            # 重新创建文档存储和存储上下文
            self.document_store = SimpleDocumentStore()
            self.storage_context = StorageContext.from_defaults(
                docstore=self.document_store
            )
            
            self.index = None
            self.documents = []
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}", exc_info=True)
            
    def save_to_disk(self, directory: str) -> bool:
        """
        Save the vector store to disk
        
        Args:
            directory: Directory to save to
            
        Returns:
            Success status
        """
        try:
            if self.index is None:
                logger.warning("No index to save")
                return False
                
            os.makedirs(directory, exist_ok=True)
            self.index.storage_context.persist(persist_dir=directory)
            logger.info(f"Vector store saved to {directory}")
            return True
        except Exception as e:
            logger.error(f"Error saving vector store: {e}", exc_info=True)
            return False
            
    def load_from_disk(self, directory: str) -> bool:
        """
        Load the vector store from disk
        
        Args:
            directory: Directory to load from
            
        Returns:
            Success status
        """
        try:
            if not os.path.exists(directory):
                logger.warning(f"Directory {directory} does not exist")
                return False
                
            # 使用最新版本的加载方法
            # 先加载存储上下文
            storage_context = StorageContext.from_defaults(persist_dir=directory)
            # 使用加载的存储上下文创建索引
            self.index = VectorStoreIndex.from_storage(storage_context)
            self.storage_context = storage_context
            
            # 重建documents列表以保持向后兼容性
            self.documents = []
            # 遍历文档存储中的所有文档
            if hasattr(self.index, 'docstore') and hasattr(self.index.docstore, 'docs'):
                for node_id, node in self.index.docstore.docs.items():
                    if hasattr(node, 'text'):
                        self.documents.append({
                            "text": node.text,
                            "metadata": node.metadata if hasattr(node, 'metadata') else {}
                        })
                    
            logger.info(f"Vector store loaded from {directory} with {len(self.documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Error loading vector store: {e}", exc_info=True)
            return False 