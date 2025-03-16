"""
Summarize Generator module for PandaAIQA
Handles text summarization using LM Studio API
"""

import requests
import json
import logging
from typing import List, Dict, Any, Optional

from simple_pandaaiqa.config import LM_STUDIO_API_BASE, LM_STUDIO_MODEL, LM_STUDIO_MAX_TOKENS, LM_STUDIO_TEMPERATURE

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SummarizeGenerator:
    """text summary generator class, using LM Studio API to generate knowledge base summary"""
    
    def __init__(self, 
                 api_base: str = LM_STUDIO_API_BASE, 
                 model: str = LM_STUDIO_MODEL,
                 max_tokens: int = LM_STUDIO_MAX_TOKENS,
                 temperature: float = 0.3,  # reduce the temperature, make the output more deterministic
                 language: str = "Korean"):  # Default to Korean
        """initialize the summary generator"""
        self.api_base = api_base
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.language = language
        
        logger.info(f"initialize the summary generator, API base URL: {api_base}")
    
    def _clean_response(self, text: str) -> str:
        """clean the response text, remove the thinking process and format markers"""
        # check if the response contains obvious thinking process patterns
        thinking_patterns = [
            "I'm trying to figure out", "First, looking at", "let me think",
            "Okay, so for", "I need to", "I should", "Let me", "I'll",
            "The user wants", "Alright, so", "Now I'll", "Let's"
        ]
        
        # if the response contains obvious thinking process patterns, try to identify the final answer part
        final_answer = None
        
        # find the start position of the formatted output
        format_markers = ["**Summary", "# Summary", "Summary:", "Here's the summary"]
        for marker in format_markers:
            if marker in text:
                final_answer = text[text.find(marker):]
                break
        
        # if the final answer part is found, return it directly
        if final_answer:
            return final_answer.strip()
        
        # if no obvious formatted output is found, but the thinking process is detected
        if any(pattern in text for pattern in thinking_patterns):
            # try to find the last paragraph as the answer
            paragraphs = text.split("\n\n")
            if len(paragraphs) > 1:
                # return the last few paragraphs, usually the conclusion
                return "\n\n".join(paragraphs[-2:]).strip()
        
        # remove common tags by default
        tags_to_remove = [
            '</think>', '<think>', '</thinking>', '<thinking>',
            '</response>', '<response>', '</answer>', '<answer>',
            '<assistant>', '</assistant>'
        ]
        
        cleaned_text = text
        for tag in tags_to_remove:
            cleaned_text = cleaned_text.replace(tag, '')
        
        # filter line by line
        lines = cleaned_text.split('\n')
        filtered_lines = []
        skip_thinking = False
        
        for line in lines:
            line_lower = line.lower()
            
            # determine if this line should be skipped
            if any(pattern in line_lower for pattern in ["thinking:", "thought:", "i'm thinking", "let me think"]):
                skip_thinking = True
                continue
                
            # detect the end of thinking
            if skip_thinking and any(marker in line_lower for marker in ["summary:", "conclusion:", "result:", "answer:"]):
                skip_thinking = False
            
            # skip the lines containing tags
            if any(tag in line_lower for tag in ['<', '>']):
                continue
                
            # skip the lines in the thinking process
            if skip_thinking:
                continue
                
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines).strip()

    def generate_summary(self, documents: List[Dict[str, Any]]) -> str:
        """
        generate comprehensive summary for all documents in the knowledge base
        
        Args:
            documents: the list of documents to summarize
            
        Returns:
            the generated summary text
        """
        logger.info(f"generate summary for {len(documents)} documents")
        
        if not documents:
            return "No documents in the knowledge base. Please upload documents first."
        
        # reduce the number of documents to speed up the processing - if there are too many documents, only process the first 10
        if len(documents) > 10:
            logger.info(f"too many documents, only process the first 10")
            documents = documents[:10]
            
        # simplify the prompt, keep the key structure requirements
        prompt = f"""Please generate a concise summary note based on the following document content, including:
1. Overall overview (1-2 sentences)
2. Main content (classified by theme)
3. Key points (list 3)

Document content:
"""

        # simplify the document processing logic
        total_tokens = 0
        max_tokens = 6000  # reduce the token limit to speed up the processing
        
        for i, doc in enumerate(documents):
            doc_text = doc.get("text", "")
            if not doc_text:
                continue
                
            # get the metadata
            metadata = doc.get("metadata", {})
            source = metadata.get("source", f"Document {i+1}")
            
            # truncate the too long document
            if len(doc_text) > 1000:
                doc_text = doc_text[:1000] + "...[content truncated]"
            
            doc_tokens = len(doc_text) // 4
            if total_tokens + doc_tokens > max_tokens:
                prompt += "\n[some documents are not included due to length limit]"
                break
            
            total_tokens += doc_tokens
            prompt += f"\n\n--- {source} ---\n{doc_text}\n"
        
        # generate the summary
        try:
            # optimize the request parameters
            payload = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": 1000,  # reduce the number of generated tokens
                "temperature": 0.7,  # increase the temperature to speed up the generation
                "stop": ["</s>"]
                # remove the unnecessary parameters to simplify the request
            }
            
            # use the v1/completions API endpoint
            logger.info(f"send request to LM Studio: {self.api_base}/v1/completions")
            response = requests.post(
                f"{self.api_base}/v1/completions",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30  # reduce the timeout time
            )
            
            # check the response
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    logger.info("successfully get the response from LM Studio")
                    raw_text = result["choices"][0]["text"].strip()
                    # clean the response text
                    cleaned_text = self._clean_response(raw_text)
                    return cleaned_text
            
            # record the detailed error information
            logger.error(f"failed to generate summary: {response.status_code}, {response.text}")
            return f"Sorry, failed to generate summary. API returned error: {response.status_code} - {response.text}"
            
        except Exception as e:
            logger.error(f"failed to generate summary: {str(e)}", exc_info=True)
            return f"Sorry, an error occurred while processing your request: {str(e)}" 