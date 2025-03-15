"""
Generator module for PandaAIQA
Handles text generation using LM Studio API
"""

import requests
import json
import logging
from typing import List, Dict, Any, Tuple, Optional

from simple_pandaaiqa.config import LM_STUDIO_API_BASE, LM_STUDIO_MODEL, LM_STUDIO_MAX_TOKENS, LM_STUDIO_TEMPERATURE

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Generator:
    """text generator class, using LM Studio API to generate replies"""
    
    def __init__(self, 
                 api_base: str = LM_STUDIO_API_BASE, 
                 model: str = LM_STUDIO_MODEL,
                 max_tokens: int = LM_STUDIO_MAX_TOKENS,
                 temperature: float = LM_STUDIO_TEMPERATURE):
        """initialize generator"""
        self.api_base = api_base
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = """You are Panda AIQA assistant, a AI that focuses on answering questions based on the provided context.
- you should only use the information provided in the context to answer the question
- if there is not enough information in the context, please say you don't know
- do not make up information"""
        
        logger.info(f"initialize generator, API base URL: {api_base}")
        # check connection status when initializing
        self.check_connection()
    
    def check_connection(self) -> Tuple[bool, str]:
        """
        check connection status with LM Studio
        
        :return:
            Tuple[bool, str]: (connection status, status message)
        """
        try:
            # use the correct API endpoint /v1/models
            response = requests.get(
                f"{self.api_base}/v1/models",
                timeout=5
            )
            
            # check response
            if response.status_code == 200:
                logger.info("LM Studio connection successful")
                return True, "LM Studio connection successful"
            else:
                logger.error(f"LM Studio connection failed: HTTP {response.status_code}, {response.text}")
                return False, f"LM Studio connection failed: HTTP {response.status_code}"
        
        except requests.exceptions.ConnectTimeout:
            logger.error("LM Studio connection timeout")
            return False, "LM Studio connection timeout, please confirm the service has been started"
        
        except requests.exceptions.ConnectionError:
            logger.error(f"LM Studio connection failed: {self.api_base}")
            return False, f"LM Studio connection failed, please confirm the service has been started and check the URL: {self.api_base}"
        
        except Exception as e:
            logger.error(f"Error checking LM Studio connection: {str(e)}", exc_info=True)
            return False, f"Error checking LM Studio connection: {str(e)}"
    
    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """
        generate answer based on query and context
        
        :param query: user query
        :param context: context documents list
            
        :return:
            generated answer
        """
        try:
            # check connection status
            is_connected, message = self.check_connection()
            if not is_connected:
                return f"cannot connect to language model: {message}"
            
            # prepare context text
            context_text = self._prepare_context(context)
            
            # prepare prompt text (using completions format)
            prompt = f"{self.system_prompt}\n\nBased on the following information, answer the question:\n\nContext:\n{context_text}\n\nQuestion:\n{query}\n\nAnswer:"
            
            # prepare request
            payload = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stop": ["</s>", "\n\n"]  # common stop tokens
            }
            
            # use the correct API endpoint /v1/completions
            logger.info(f"Sending request to LM Studio: {self.api_base}/v1/completions")
            response = requests.post(
                f"{self.api_base}/v1/completions",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30
            )
            
            # check response
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    logger.info("Successfully got reply from LM Studio")
                    # completions API returns a different format from chat
                    return result["choices"][0]["text"].strip()
            
            # log detailed error information
            logger.error(f"Failed to generate answer: {response.status_code}, {response.text}")
            return f"Sorry, I cannot generate an answer. API returned an error: {response.status_code} - {response.text}"
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}", exc_info=True)
            return f"Sorry, an error occurred while processing your request: {str(e)}"
    
    def _prepare_context(self, context: List[Dict[str, Any]]) -> str:
        """
        prepare context text
        
        :param context: context documents list
            
        :return:
            formatted context text
        """
        if not context:
            return "No relevant context found."
        
        context_parts = []
        for i, doc in enumerate(context):
            text = doc.get("text", "")
            source = doc.get("metadata", {}).get("source", f"Document {i+1}")
            context_parts.append(f"[{source}]\n{text}")
        
        return "\n\n".join(context_parts) 