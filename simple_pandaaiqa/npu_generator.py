"""
Generator module for PandaAIQA
Handles text generation using AnythingLLM API
"""

import requests
import json
import logging
from typing import List, Dict, Any, Tuple, Optional

from simple_pandaaiqa.config import ANYTHINGLLM_API_BASE, ANYTHINGLLM_KEY, ANYTHINGLLM_MODEL, ANYTHINGLLM_MAX_TOKENS, ANYTHINGLLM_TEMPERATURE

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NPU_Generator:
    """text generator class, using AnythingLLM API to generate replies"""
    
    def __init__(self, 
                 api_base: str = ANYTHINGLLM_API_BASE, 
                 model: str = ANYTHINGLLM_MODEL,
                 api_key: str = ANYTHINGLLM_KEY,
                 max_tokens: int = ANYTHINGLLM_MAX_TOKENS,
                 temperature: float = ANYTHINGLLM_TEMPERATURE):
        """initialize generator"""
        self.api_base = api_base
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.headers = {'Content-Type': 'application/json'}
        if self.api_key:
                self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.system_prompt = """You are Panda AIQA assistant utilizing Snapdragon NPU, a AI that focuses on answering questions based on the provided context.
- you should only use the information provided in the context to answer the question
- if there is not enough information in the context, please say you don't know
- do not make up information"""
        
        logger.info(f"initialize generator, API base URL: {api_base}")
        # check connection status when initializing
        self.check_connection()
    
    def check_connection(self) -> Tuple[bool, str]:
        """
        check connection status with AnythingLLM
        
        :return:
            Tuple[bool, str]: (connection status, status message)
        """
        try:
            # use the correct API endpoint /v1/models
            response = requests.get(
                f"{self.api_base}/v1/models",
                headers=self.headers,
                timeout=5
            )
            
            # check response
            if response.status_code == 200:
                logger.info("AnythingLLM connection successful")
                return True, "AnythingLLM connection successful"
            else:
                logger.error(f"AnythingLLM connection failed: HTTP {response.status_code}, {response.text}")
                return False, f"AnythingLLM connection failed: HTTP {response.status_code}"
        
        except requests.exceptions.ConnectTimeout:
            logger.error("AnythingLLM connection timeout")
            return False, "AnythingLLM connection timeout, please confirm the service has been started"
        
        except requests.exceptions.ConnectionError:
            logger.error(f"AnythingLLM connection failed: {self.api_base}")
            return False, f"AnythingLLM connection failed, please confirm the service has been started and check the URL: {self.api_base}"
        
        except Exception as e:
            logger.error(f"Error checking AnythingLLM connection: {str(e)}", exc_info=True)
            return False, f"Error checking AnythingLLM connection: {str(e)}"
    
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
            logger.info(f"Sending request AnythingLLM: {self.api_base}/v1/completions")
            response = requests.post(
                f"{self.api_base}/v1/completions",
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            # check response
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    logger.info("Successfully got reply from AnythingLLM")
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