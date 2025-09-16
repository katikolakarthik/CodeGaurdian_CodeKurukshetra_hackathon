"""
Modular plagiarism detection utility.
Separated from main.py for better organization.
"""

import os
import sys
from typing import Dict, Any, List
import uuid
from datetime import datetime

# Add parent directory to path to import other utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embeddings import embedding_generator
from utils.similarity import similarity_checker

class PlagiarismChecker:
    """Modular plagiarism detection system."""
    
    def __init__(self):
        self.max_chunk_size = int(os.getenv('MAX_CHUNK_SIZE', '500'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '100'))
    
    def check_plagiarism(self, code: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check code for plagiarism against existing submissions.
        
        Args:
            code: Source code to check
            metadata: Metadata about the submission
            
        Returns:
            Dictionary with plagiarism analysis results
        """
        try:
            # Chunk the code
            chunks = embedding_generator.chunk_code(
                code, 
                max_chunk_size=self.max_chunk_size, 
                overlap=self.chunk_overlap
            )
            
            if not chunks:
                return {
                    'success': False,
                    'error': 'No valid code chunks found',
                    'plagiarism_percentage': 0.0,
                    'originality_score': 100.0,
                    'total_chunks': 0,
                    'flagged_chunks': 0,
                    'chunk_results': []
                }
            
            # Generate embeddings for chunks
            embeddings = embedding_generator.generate_embeddings(chunks)
            
            # Check each chunk for similarity
            all_results = []
            flagged_chunks = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Calculate plagiarism for this chunk
                plagiarism_result = similarity_checker.calculate_plagiarism_percentage(embedding)
                
                chunk_result = {
                    'chunk_id': f"{metadata.get('submission_id', 'unknown')}_chunk_{i}",
                    'start_word': chunk['start_word'],
                    'end_word': chunk['end_word'],
                    'text': chunk['original_text'],
                    'plagiarism_percentage': plagiarism_result['plagiarism_percentage'],
                    'originality_score': plagiarism_result['originality_score'],
                    'similar_chunks': plagiarism_result['similar_chunks'],
                    'is_flagged': plagiarism_result['plagiarism_percentage'] > 70.0  # 70% threshold
                }
                
                all_results.append(chunk_result)
                
                if chunk_result['is_flagged']:
                    flagged_chunks.append(chunk_result)
            
            # Calculate overall plagiarism percentage
            if all_results:
                overall_plagiarism = max([result['plagiarism_percentage'] for result in all_results])
                overall_originality = min([result['originality_score'] for result in all_results])
            else:
                overall_plagiarism = 0.0
                overall_originality = 100.0
            
            return {
                'success': True,
                'plagiarism_percentage': round(overall_plagiarism, 2),
                'originality_score': round(overall_originality, 2),
                'total_chunks': len(chunks),
                'flagged_chunks': len(flagged_chunks),
                'chunk_results': all_results,
                'top_similar_chunks': flagged_chunks[:3],  # Top 3 most similar
                'metadata': metadata
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Plagiarism check failed: {str(e)}',
                'plagiarism_percentage': 0.0,
                'originality_score': 100.0,
                'total_chunks': 0,
                'flagged_chunks': 0,
                'chunk_results': []
            }
    
    def ingest_code(self, code: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest code into the similarity index for future comparisons.
        
        Args:
            code: Source code to ingest
            metadata: Metadata about the submission
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            # Chunk the code
            chunks = embedding_generator.chunk_code(
                code, 
                max_chunk_size=self.max_chunk_size, 
                overlap=self.chunk_overlap
            )
            
            if not chunks:
                return {
                    'success': False,
                    'error': 'No valid code chunks found',
                    'chunk_count': 0
                }
            
            # Generate embeddings for chunks
            embeddings = embedding_generator.generate_embeddings(chunks)
            
            # Prepare metadata for each chunk
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_metadata.append({
                    'submission_id': metadata.get('submission_id', str(uuid.uuid4())),
                    'chunk_id': f"{metadata.get('submission_id', 'unknown')}_chunk_{i}",
                    'team_name': metadata.get('team_name', 'Unknown Team'),
                    'submission_name': metadata.get('submission_name', 'Unknown Submission'),
                    'language': metadata.get('language', 'unknown'),
                    'start_word': chunk['start_word'],
                    'end_word': chunk['end_word'],
                    'original_text': chunk['original_text'],
                    'processed_text': chunk['text']
                })
            
            # Add embeddings to similarity checker
            similarity_checker.add_embeddings(embeddings, chunk_metadata)
            
            return {
                'success': True,
                'chunk_count': len(chunks),
                'message': f'Successfully processed {len(chunks)} code chunks'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Code ingestion failed: {str(e)}',
                'chunk_count': 0
            }

# Global instance
plagiarism_checker = PlagiarismChecker()
