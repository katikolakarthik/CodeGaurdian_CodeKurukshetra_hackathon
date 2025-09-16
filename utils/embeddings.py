"""
Embeddings utility for generating code embeddings using HuggingFace API.
"""

import os
import re
from typing import List, Dict, Any
import requests
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmbeddingGenerator:
    """Generate embeddings for code chunks using HuggingFace models."""
    
    def __init__(self):
        self.model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        
        # Initialize the model
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ Loaded embedding model: {self.model_name}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None
    
    def preprocess_code(self, code: str) -> str:
        """
        Preprocess code by removing comments, extra whitespace, and normalizing.
        """
        # Remove single-line comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove extra whitespace and normalize
        code = re.sub(r'\s+', ' ', code).strip()
        return code
    
    def chunk_code(self, code: str, max_chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]:
        """
        Split code into overlapping chunks for better similarity detection.
        
        Args:
            code: Source code string
            max_chunk_size: Maximum words per chunk
            overlap: Number of words to overlap between chunks
            
        Returns:
            List of dictionaries containing chunk info and preprocessed code
        """
        # Preprocess the code
        processed_code = self.preprocess_code(code)
        
        # Split into words
        words = processed_code.split()
        chunks = []
        
        for i in range(0, len(words), max_chunk_size - overlap):
            chunk_words = words[i:i + max_chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if chunk_text.strip():
                chunks.append({
                    'text': chunk_text,
                    'start_word': i,
                    'end_word': min(i + max_chunk_size, len(words)),
                    'original_text': ' '.join(words[i:i + max_chunk_size])
                })
        
        return chunks
    
    def generate_embeddings(self, code_chunks: List[Dict[str, Any]]) -> List[np.ndarray]:
        """
        Generate embeddings for code chunks using the loaded model.
        
        Args:
            code_chunks: List of code chunk dictionaries
            
        Returns:
            List of numpy arrays representing embeddings
        """
        if not self.model:
            raise Exception("Model not loaded. Check your HuggingFace API token.")
        
        # Extract text from chunks
        texts = [chunk['text'] for chunk in code_chunks]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        return embeddings.tolist()
    
    def generate_embedding_for_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Input text string
            
        Returns:
            Numpy array representing the embedding
        """
        if not self.model:
            raise Exception("Model not loaded. Check your HuggingFace API token.")
        
        # Preprocess the text
        processed_text = self.preprocess_code(text)
        
        # Generate embedding
        embedding = self.model.encode([processed_text], convert_to_numpy=True)
        
        return embedding[0].tolist()

# Global instance
embedding_generator = EmbeddingGenerator()
