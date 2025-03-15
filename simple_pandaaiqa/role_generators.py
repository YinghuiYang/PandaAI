"""
Role-specific generators for PandaAIQA
Extends the base Generator with role-specific behaviors
"""

import logging
from typing import List, Dict, Any

from simple_pandaaiqa.generator import Generator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CustomerSupportGenerator(Generator):
    """Generator specialized for customer support queries"""
    
    def __init__(self, **kwargs):
        """Initialize with customer support specific system prompt"""
        super().__init__(**kwargs)
        self.system_prompt = """You are a Customer Support Agent for Panda AIQA.
- Focus on helping users solve their problems quickly and effectively
- Use a friendly, helpful, and empathetic tone
- Provide step-by-step solutions when applicable
- Only use information from the provided context to answer questions
- If you don't have enough information, offer to escalate the issue
- Format instructions like numbered steps when providing procedures
- Suggest related resources when appropriate"""
        
        logger.info("Initialized CustomerSupportGenerator")
    
    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate a customer support focused answer"""
        # Add customer support framing to the query if needed
        if not query.lower().startswith(("as a customer support", "customer support")):
            query = f"As a customer support agent, help with: {query}"
        
        return super().generate(query, context)
    
    def _prepare_context(self, context: List[Dict[str, Any]]) -> str:
        """Customer support specialized context preparation"""
        if not context:
            return "No relevant customer support documentation found."
        
        # Prioritize customer support specific resources in context
        # This is a simple implementation - you could add more sophisticated prioritization
        support_docs = []
        other_docs = []
        
        for doc in context:
            metadata = doc.get("metadata", {})
            if metadata.get("role") == "customer-support" or "support" in metadata.get("source", "").lower():
                support_docs.append(doc)
            else:
                other_docs.append(doc)
        
        # Combine prioritized docs
        sorted_docs = support_docs + other_docs
        
        # Format the context
        context_parts = []
        for i, doc in enumerate(sorted_docs):
            text = doc.get("text", "")
            source = doc.get("metadata", {}).get("source", f"Support Document {i+1}")
            context_parts.append(f"[{source}]\n{text}")
        
        return "\n\n".join(context_parts)


class SalesGenerator(Generator):
    """Generator specialized for sales representative queries"""
    
    def __init__(self, **kwargs):
        """Initialize with sales specific system prompt"""
        super().__init__(**kwargs)
        self.system_prompt = """You are a Sales Representative for Panda AIQA.
- Focus on highlighting product benefits and value propositions
- Be persuasive but honest and accurate
- Provide pricing, feature comparisons, and ROI information when relevant
- Only use information from the provided context
- If you don't have specific information, avoid making up details about products or pricing
- Suggest appropriate upsells or cross-sells when relevant
- Use confident and positive language"""
        
        logger.info("Initialized SalesGenerator")
    
    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate a sales-focused answer"""
        # Add sales framing to the query
        if not query.lower().startswith(("as a sales", "sales rep")):
            query = f"As a sales representative, respond to: {query}"
        
        return super().generate(query, context)
    
    def _prepare_context(self, context: List[Dict[str, Any]]) -> str:
        """Sales specialized context preparation"""
        if not context:
            return "No relevant sales materials found."
        
        # Prioritize sales specific resources in context
        sales_docs = []
        other_docs = []
        
        for doc in context:
            metadata = doc.get("metadata", {})
            if metadata.get("role") == "sales" or any(term in metadata.get("source", "").lower() for term in ["price", "product", "sales"]):
                sales_docs.append(doc)
            else:
                other_docs.append(doc)
        
        # Combine prioritized docs
        sorted_docs = sales_docs + other_docs
        
        # Format the context
        context_parts = []
        for i, doc in enumerate(sorted_docs):
            text = doc.get("text", "")
            source = doc.get("metadata", {}).get("source", f"Sales Material {i+1}")
            context_parts.append(f"[{source}]\n{text}")
        
        return "\n\n".join(context_parts)


class TechnicalGenerator(Generator):
    """Generator specialized for technical specialist queries"""
    
    def __init__(self, **kwargs):
        """Initialize with technical specific system prompt"""
        super().__init__(**kwargs)
        self.system_prompt = """You are a Technical Specialist for Panda AIQA.
- Provide accurate, detailed technical information
- Use precise technical terminology appropriate for developers and engineers
- Include code examples, API references, and technical specifications when relevant
- Only use information from the provided context
- If technical details are missing, acknowledge the limitation rather than inventing details
- Format code blocks properly with appropriate syntax highlighting hints
- Organize complex technical explanations in a logical, step-by-step manner"""
        
        logger.info("Initialized TechnicalGenerator")
    
    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate a technically-focused answer"""
        # Add technical framing to the query
        if not query.lower().startswith(("as a technical", "technical specialist")):
            query = f"As a technical specialist, explain: {query}"
        
        return super().generate(query, context)
    
    def _prepare_context(self, context: List[Dict[str, Any]]) -> str:
        """Technical specialized context preparation"""
        if not context:
            return "No relevant technical documentation found."
        
        # Prioritize technical specific resources in context
        technical_docs = []
        other_docs = []
        
        for doc in context:
            metadata = doc.get("metadata", {})
            if metadata.get("role") == "technical" or any(term in metadata.get("source", "").lower() for term in ["api", "code", "tech", "doc", "guide"]):
                technical_docs.append(doc)
            else:
                other_docs.append(doc)
        
        # Combine prioritized docs
        sorted_docs = technical_docs + other_docs
        
        # Format the context
        context_parts = []
        for i, doc in enumerate(sorted_docs):
            text = doc.get("text", "")
            source = doc.get("metadata", {}).get("source", f"Technical Document {i+1}")
            context_parts.append(f"[{source}]\n{text}")
        
        return "\n\n".join(context_parts)


# Factory function to get the appropriate generator for a role
def get_role_generator(role: str = None, **kwargs) -> Generator:
    """
    Get a generator for the specified role
    
    :param role: The role to get a generator for
    :param kwargs: Additional arguments to pass to the generator
    
    :return: A generator instance appropriate for the specified role
    """
    if role == "customer-support":
        return CustomerSupportGenerator(**kwargs)
    elif role == "sales":
        return SalesGenerator(**kwargs)
    elif role == "technical":
        return TechnicalGenerator(**kwargs)
    else:
        # Default generator for all other cases
        return Generator(**kwargs) 