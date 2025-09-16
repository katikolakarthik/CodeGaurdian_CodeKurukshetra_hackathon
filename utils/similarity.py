"""
Similarity checking utility using FAISS for efficient vector similarity search.
"""

import numpy as np
import faiss
from typing import List, Dict, Any, Tuple
import json
import os
from datetime import datetime

class SimilarityChecker:
    """Handle vector similarity checking using FAISS."""
    
    def __init__(self, dimension: int = 384):  # all-MiniLM-L6-v2 has 384 dimensions
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity)
        self.metadata = []  # Store metadata for each vector
        self.submission_id = 0
        
    def add_embeddings(self, embeddings: List[List[float]], metadata: List[Dict[str, Any]]):
        """
        Add embeddings to the FAISS index.
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries for each embedding
        """
        if not embeddings:
            return
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Store metadata
        self.metadata.extend(metadata)
        
        print(f"✅ Added {len(embeddings)} embeddings to index. Total: {self.index.ntotal}")
    
    def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings using cosine similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top similar results to return
            
        Returns:
            List of similar results with scores and metadata
        """
        if self.index.ntotal == 0:
            return []
        
        # Convert to numpy array and normalize
        query_array = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_array)
        
        # Search
        scores, indices = self.index.search(query_array, min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:  # Valid index
                results.append({
                    'score': float(score),
                    'similarity_percentage': float(score * 100),
                    'metadata': self.metadata[idx]
                })
        
        return results
    
    def calculate_plagiarism_percentage(self, query_embedding: List[float], threshold: float = 0.7) -> Dict[str, Any]:
        """
        Calculate overall plagiarism percentage for a query.
        
        Args:
            query_embedding: Query embedding vector
            threshold: Similarity threshold for considering as plagiarism
            
        Returns:
            Dictionary with plagiarism analysis results
        """
        similar_results = self.search_similar(query_embedding, top_k=10)
        
        if not similar_results:
            return {
                'plagiarism_percentage': 0.0,
                'originality_score': 100.0,
                'similar_chunks': [],
                'max_similarity': 0.0
            }
        
        # Calculate plagiarism percentage based on highest similarity
        max_similarity = max([result['similarity_percentage'] for result in similar_results])
        
        # Plagiarism percentage is the highest similarity score
        plagiarism_percentage = max_similarity
        
        # Originality score is inverse of plagiarism
        originality_score = max(0, 100 - plagiarism_percentage)
        
        # Get chunks above threshold
        flagged_chunks = [result for result in similar_results if result['similarity_percentage'] >= threshold * 100]
        
        return {
            'plagiarism_percentage': round(plagiarism_percentage, 2),
            'originality_score': round(originality_score, 2),
            'similar_chunks': similar_results[:3],  # Top 3 most similar
            'flagged_chunks': flagged_chunks,
            'max_similarity': round(max_similarity, 2),
            'total_chunks_checked': len(similar_results)
        }
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'index_type': 'FAISS_IndexFlatIP'
        }
    
    def save_index(self, filepath: str):
        """Save the FAISS index to disk."""
        faiss.write_index(self.index, f"{filepath}.index")
        
        # Save metadata
        with open(f"{filepath}_metadata.json", 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def load_index(self, filepath: str):
        """Load the FAISS index from disk."""
        self.index = faiss.read_index(f"{filepath}.index")
        
        # Load metadata
        with open(f"{filepath}_metadata.json", 'r') as f:
            self.metadata = json.load(f)

# Global instance
similarity_checker = SimilarityChecker()
