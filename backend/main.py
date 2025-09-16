"""
FastAPI backend for AI-powered code plagiarism detection.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import uuid

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embeddings import embedding_generator
from utils.similarity import similarity_checker
from utils.watsonx import watsonx_client
from utils.github import github_fetcher

# Initialize FastAPI app
app = FastAPI(
    title="AI Code Plagiarism Detector",
    description="AI-powered plagiarism detection for code submissions using embeddings and semantic analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for submissions (in production, use a proper database)
submissions_db = {}
chunks_db = {}

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "AI Code Plagiarism Detector API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Get current database statistics."""
    return {
        "total_submissions": len(submissions_db),
        "total_chunks": similarity_checker.get_index_stats()['total_vectors'],
        "index_stats": similarity_checker.get_index_stats()
    }

@app.post("/upload")
async def upload_code(
    file: UploadFile = File(...),
    team_name: str = Form("Unknown Team"),
    submission_name: str = Form("Unknown Submission"),
    language: str = Form("python")
):
    """
    Upload and process a code file for plagiarism detection.
    
    Args:
        file: Code file to upload
        team_name: Name of the team submitting
        submission_name: Name of the submission
        language: Programming language of the code
        
    Returns:
        JSON response with processing results
    """
    try:
        # Validate file size
        max_size = int(os.getenv('MAX_FILE_SIZE', '900')) * 1024 * 1024  # Convert MB to bytes
        content = await file.read()
        
        if len(content) > max_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {os.getenv('MAX_FILE_SIZE', '900')}MB"
            )
        
        # Decode content
        code_content = content.decode('utf-8')
        
        # Generate unique submission ID
        submission_id = str(uuid.uuid4())
        
        # Chunk the code
        max_chunk_size = int(os.getenv('MAX_CHUNK_SIZE', '500'))
        chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '100'))
        
        chunks = embedding_generator.chunk_code(
            code_content, 
            max_chunk_size=max_chunk_size, 
            overlap=chunk_overlap
        )
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No valid code chunks found")
        
        # Generate embeddings for chunks
        embeddings = embedding_generator.generate_embeddings(chunks)
        
        # Store submission metadata
        submission_metadata = {
            'submission_id': submission_id,
            'team_name': team_name,
            'submission_name': submission_name,
            'language': language,
            'filename': file.filename,
            'file_size': len(content),
            'chunk_count': len(chunks),
            'upload_time': datetime.now().isoformat()
        }
        
        submissions_db[submission_id] = submission_metadata
        
        # Prepare metadata for each chunk
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_metadata.append({
                'submission_id': submission_id,
                'chunk_id': f"{submission_id}_chunk_{i}",
                'team_name': team_name,
                'submission_name': submission_name,
                'language': language,
                'start_word': chunk['start_word'],
                'end_word': chunk['end_word'],
                'original_text': chunk['original_text'],
                'processed_text': chunk['text']
            })
        
        # Add embeddings to similarity checker
        similarity_checker.add_embeddings(embeddings, chunk_metadata)
        
        # Store chunks
        chunks_db[submission_id] = {
            'chunks': chunks,
            'embeddings': embeddings,
            'metadata': chunk_metadata
        }
        
        return {
            "success": True,
            "submission_id": submission_id,
            "message": f"Successfully processed {len(chunks)} code chunks",
            "metadata": submission_metadata,
            "chunk_count": len(chunks)
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a text file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/fetch_repo")
async def fetch_repo(
    repo_url: str = Form(...),
    team_name: str = Form("Unknown Team"),
    submission_name: str = Form("GitHub Repo"),
    language: str = Form("mixed")
):
    """
    Fetch a GitHub repository's code files and ingest them into the similarity index.
    Runs the same chunking + embeddings pipeline used for file uploads.
    """
    try:
        repo_data = github_fetcher.fetch_repository(repo_url)

        if not repo_data.get('files'):
            raise HTTPException(status_code=404, detail="No code files found in repository or access denied")

        submission_id = str(uuid.uuid4())

        max_chunk_size = int(os.getenv('MAX_CHUNK_SIZE', '500'))
        chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '100'))

        all_chunks = []
        chunk_metadata = []

        for file_obj in repo_data['files']:
            code_content = file_obj['content']
            chunks = embedding_generator.chunk_code(code_content, max_chunk_size=max_chunk_size, overlap=chunk_overlap)
            for i, ch in enumerate(chunks):
                meta = {
                    'submission_id': submission_id,
                    'chunk_id': f"{submission_id}_{file_obj['path']}_{i}",
                    'team_name': team_name,
                    'submission_name': submission_name,
                    'language': language,
                    'repo_owner': repo_data['owner'],
                    'repo_name': repo_data['repo'],
                    'branch': repo_data['branch'],
                    'file_path': file_obj['path'],
                    'start_word': ch['start_word'],
                    'end_word': ch['end_word'],
                    'original_text': ch['original_text'],
                    'processed_text': ch['text']
                }
                all_chunks.append(ch)
                chunk_metadata.append(meta)

        if not all_chunks:
            raise HTTPException(status_code=400, detail="No valid chunks produced from repository files")

        embeddings = embedding_generator.generate_embeddings(all_chunks)
        similarity_checker.add_embeddings(embeddings, chunk_metadata)

        submissions_db[submission_id] = {
            'submission_id': submission_id,
            'team_name': team_name,
            'submission_name': submission_name,
            'language': language,
            'source': 'github',
            'repo_url': repo_url,
            'repo_owner': repo_data['owner'],
            'repo_name': repo_data['repo'],
            'file_count': repo_data['file_count'],
            'chunk_count': len(all_chunks),
            'upload_time': datetime.now().isoformat()
        }

        chunks_db[submission_id] = {
            'chunks': all_chunks,
            'embeddings': embeddings,
            'metadata': chunk_metadata
        }

        return {
            "success": True,
            "submission_id": submission_id,
            "repo": {
                "owner": repo_data['owner'],
                "name": repo_data['repo'],
                "branch": repo_data['branch'],
                "file_count": repo_data['file_count']
            },
            "chunk_count": len(all_chunks),
            "message": "Repository fetched and ingested successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching repository: {str(e)}")

@app.post("/check")
async def check_plagiarism(
    file: UploadFile = File(...),
    team_name: str = Form("Unknown Team"),
    submission_name: str = Form("Unknown Submission"),
    language: str = Form("python")
):
    """
    Check uploaded code for plagiarism against existing submissions.
    
    Args:
        file: Code file to check
        team_name: Name of the team submitting
        submission_name: Name of the submission
        language: Programming language of the code
        
    Returns:
        JSON response with plagiarism analysis
    """
    try:
        # Read and decode file content
        content = await file.read()
        code_content = content.decode('utf-8')
        
        # Generate unique submission ID for this check
        check_id = str(uuid.uuid4())
        
        # Chunk the code
        max_chunk_size = int(os.getenv('MAX_CHUNK_SIZE', '500'))
        chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '100'))
        
        chunks = embedding_generator.chunk_code(
            code_content, 
            max_chunk_size=max_chunk_size, 
            overlap=chunk_overlap
        )
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No valid code chunks found")
        
        # Generate embeddings for chunks
        embeddings = embedding_generator.generate_embeddings(chunks)
        
        # Check each chunk for similarity
        all_results = []
        flagged_chunks = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Calculate plagiarism for this chunk
            plagiarism_result = similarity_checker.calculate_plagiarism_percentage(embedding)
            
            chunk_result = {
                'chunk_id': f"{check_id}_chunk_{i}",
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
        
        # Prepare response
        response = {
            "success": True,
            "check_id": check_id,
            "overall_plagiarism_percentage": round(overall_plagiarism, 2),
            "overall_originality_score": round(overall_originality, 2),
            "total_chunks": len(chunks),
            "flagged_chunks": len(flagged_chunks),
            "chunk_results": all_results,
            "top_similar_chunks": flagged_chunks[:3],  # Top 3 most similar
            "metadata": {
                "team_name": team_name,
                "submission_name": submission_name,
                "language": language,
                "filename": file.filename,
                "check_time": datetime.now().isoformat()
            }
        }
        
        return response
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a text file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking plagiarism: {str(e)}")

@app.post("/explain")
async def explain_plagiarism(
    suspicious_code: str = Form(...),
    similar_code: str = Form(...),
    similarity_score: float = Form(...),
    team_name: str = Form("Unknown Team"),
    submission_name: str = Form("Unknown Submission")
):
    """
    Generate human-readable explanation for plagiarism detection.
    
    Args:
        suspicious_code: The code chunk flagged as suspicious
        similar_code: The similar code chunk from database
        similarity_score: Similarity score between the chunks
        team_name: Name of the team
        submission_name: Name of the submission
        
    Returns:
        JSON response with explanation and suggestions
    """
    try:
        submission_info = {
            'team_name': team_name,
            'submission_name': submission_name
        }
        
        # Generate explanation using Watsonx
        explanation_result = watsonx_client.generate_explanation(
            suspicious_code=suspicious_code,
            similar_code=similar_code,
            similarity_score=similarity_score,
            submission_info=submission_info
        )
        
        # Generate rewrite suggestion if plagiarism is high
        rewrite_suggestion = None
        if similarity_score > 80.0:  # High similarity threshold
            rewrite_result = watsonx_client.generate_rewrite_suggestion(
                suspicious_code=suspicious_code,
                language="python"  # Could be made dynamic
            )
            if rewrite_result.get('success'):
                rewrite_suggestion = rewrite_result
        
        return {
            "success": True,
            "similarity_score": similarity_score,
            "explanation": explanation_result.get('explanation', 'No explanation available'),
            "similarities": explanation_result.get('similarities', []),
            "suggestion": explanation_result.get('suggestion', ''),
            "confidence": explanation_result.get('confidence', 'medium'),
            "rewrite_suggestion": rewrite_suggestion,
            "metadata": {
                "team_name": team_name,
                "submission_name": submission_name,
                "explanation_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

@app.post("/compare_repos")
async def compare_repos(
    repo_urls: str = Form(...),  # Comma-separated list of URLs
    team_prefix: str = Form("RepoTeam"),
    submission_prefix: str = Form("RepoSubmission")
):
    """
    Fetch multiple GitHub repositories, ingest embeddings, and compare originality across them.
    Returns a leaderboard with originality scores per repository.
    """
    try:
        urls = [u.strip() for u in repo_urls.split(',') if u.strip()]
        if len(urls) < 2:
            raise HTTPException(status_code=400, detail="Provide at least two repository URLs for comparison")

        repo_results = []
        repo_vectors = []
        repo_ids = []

        max_chunk_size = int(os.getenv('MAX_CHUNK_SIZE', '500'))
        chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '100'))

        for idx, url in enumerate(urls):
            data = github_fetcher.fetch_repository(url)
            submission_id = str(uuid.uuid4())
            all_chunks = []
            chunk_metadata = []
            for file_obj in data['files']:
                chunks = embedding_generator.chunk_code(file_obj['content'], max_chunk_size=max_chunk_size, overlap=chunk_overlap)
                for i, ch in enumerate(chunks):
                    meta = {
                        'submission_id': submission_id,
                        'chunk_id': f"{submission_id}_{file_obj['path']}_{i}",
                        'team_name': f"{team_prefix}-{idx+1}",
                        'submission_name': f"{submission_prefix}-{idx+1}",
                        'language': 'mixed',
                        'repo_owner': data['owner'],
                        'repo_name': data['repo'],
                        'branch': data['branch'],
                        'file_path': file_obj['path'],
                        'start_word': ch['start_word'],
                        'end_word': ch['end_word'],
                        'original_text': ch['original_text'],
                        'processed_text': ch['text']
                    }
                    all_chunks.append(ch)
                    chunk_metadata.append(meta)

            embeddings = embedding_generator.generate_embeddings(all_chunks) if all_chunks else []
            submissions_db[submission_id] = {
                'submission_id': submission_id,
                'team_name': f"{team_prefix}-{idx+1}",
                'submission_name': f"{submission_prefix}-{idx+1}",
                'source': 'github',
                'repo_url': url,
                'repo_owner': data.get('owner'),
                'repo_name': data.get('repo'),
                'file_count': data.get('file_count', 0),
                'chunk_count': len(all_chunks),
                'upload_time': datetime.now().isoformat()
            }
            chunks_db[submission_id] = {
                'chunks': all_chunks,
                'embeddings': embeddings,
                'metadata': chunk_metadata
            }

            repo_results.append({
                'submission_id': submission_id,
                'url': url,
                'owner': data.get('owner'),
                'repo': data.get('repo'),
                'chunk_count': len(all_chunks)
            })

            repo_vectors.append(embeddings)
            repo_ids.append(submission_id)

        # Compute pairwise originality scores: for each repo, compute max similarity to others and invert
        leaderboard = []
        for i, submission_id in enumerate(repo_ids):
            max_sim = 0.0
            # For each vector in repo i, compare against existing FAISS index via similarity_checker
            # To avoid contaminating comparisons, use current global index which already has all vectors now
            for vec in repo_vectors[i]:
                res = similarity_checker.calculate_plagiarism_percentage(vec)
                max_sim = max(max_sim, res['plagiarism_percentage'])
            originality = max(0.0, 100.0 - max_sim)
            leaderboard.append({
                'submission_id': submission_id,
                'repo_url': repo_results[i]['url'],
                'owner': repo_results[i]['owner'],
                'repo': repo_results[i]['repo'],
                'originality_score': round(originality, 2),
                'plagiarism_percentage': round(max_sim, 2),
                'chunk_count': repo_results[i]['chunk_count']
            })

        # Sort by originality descending
        leaderboard.sort(key=lambda x: (-x['originality_score'], x['plagiarism_percentage']))

        return {
            "success": True,
            "leaderboard": leaderboard,
            "repos_compared": len(urls)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing repositories: {str(e)}")

@app.get("/submissions")
async def get_submissions():
    """Get list of all uploaded submissions."""
    return {
        "success": True,
        "submissions": list(submissions_db.values()),
        "total_count": len(submissions_db)
    }

@app.get("/submissions/{submission_id}")
async def get_submission(submission_id: str):
    """Get details of a specific submission."""
    if submission_id not in submissions_db:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    submission = submissions_db[submission_id]
    chunks_info = chunks_db.get(submission_id, {})
    
    return {
        "success": True,
        "submission": submission,
        "chunks": chunks_info.get('chunks', []),
        "chunk_count": len(chunks_info.get('chunks', []))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
