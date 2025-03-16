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
        # create the document store and storage context
        self.document_store = SimpleDocumentStore()
        self.storage_context = StorageContext.from_defaults(
            docstore=self.document_store
        )
        
        self.node_parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        
        # use the HuggingFace embedding model
        self.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # set the global embedding model
        Settings.embed_model = self.embed_model
            
        self.index = None
        self.documents = []  # keep for backward compatibility
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
                # use the current set embedding model
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
            # recreate the document store and storage context
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
                
            # use the latest loading method
            # first load the storage context
            storage_context = StorageContext.from_defaults(persist_dir=directory)
            # use the loaded storage context to create the index
            self.index = VectorStoreIndex.from_storage(storage_context)
            self.storage_context = storage_context
            
            # rebuild the documents list to maintain backward compatibility
            self.documents = []
            # iterate through all documents in the document store
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

    def list_collections(self) -> List[str]:
        """List all collections in the VectorStore."""
        collections = self.client.get_collections()
        return [c.name for c in collections.collections]

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get all documents from all collections in the vector store
        
        Returns:
            List of documents with text and metadata
        """
        logger.info("Retrieving all documents from vector store")
        all_documents = []
        
        try:
            collections = self.client.get_collections()
            for collection in collections.collections:
                collection_name = collection.name
                
                # skip the system collection or non-document collection
                if collection_name.startswith("_") or collection_name == "default":
                    continue
                    
                # get all documents from the collection
                docs = self.client.get(
                    collection_name=collection_name,
                    include=["metadatas", "documents"],
                    limit=10000  # set a large limit value
                )
                
                # process the documents
                if docs and docs['ids']:
                    for i, doc_id in enumerate(docs['ids']):
                        document = {
                            "id": doc_id,
                            "text": docs['documents'][i] if docs['documents'] else "",
                            "metadata": docs['metadatas'][i] if docs['metadatas'] else {}
                        }
                        all_documents.append(document)
                        
            logger.info(f"Retrieved {len(all_documents)} documents in total")
            return all_documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return [] 