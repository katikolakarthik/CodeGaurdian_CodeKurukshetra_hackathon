"""
IBM Watsonx integration for generating human-readable explanations of plagiarism.
"""

import os
import requests
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WatsonxClient:
    """Client for IBM Watsonx API to generate explanations and suggestions."""
    
    def __init__(self):
        self.api_key = os.getenv('WATSONX_API_KEY')
        self.project_id = os.getenv('WATSONX_PROJECT_ID')
        self.url = os.getenv('WATSONX_URL')
        self.model = os.getenv('LLM_MODEL', 'ibm/granite-3-3-8b-instruct')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '300'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.5'))
        
        if not all([self.api_key, self.project_id, self.url]):
            raise ValueError("Missing required Watsonx configuration. Check your .env file.")
    
    def generate_explanation(self, 
                           suspicious_code: str, 
                           similar_code: str, 
                           similarity_score: float,
                           submission_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a human-readable explanation of plagiarism detection.
        
        Args:
            suspicious_code: The code chunk flagged as suspicious
            similar_code: The similar code chunk from database
            similarity_score: Similarity score between the chunks
            submission_info: Additional information about the submission
            
        Returns:
            Dictionary containing explanation and suggestions
        """
        
        prompt = self._create_explanation_prompt(
            suspicious_code, similar_code, similarity_score, submission_info
        )
        
        try:
            response = self._call_watsonx_api(prompt)
            
            if response.get('success'):
                return {
                    'success': True,
                    'explanation': response['explanation'],
                    'suggestion': response.get('suggestion', ''),
                    'confidence': response.get('confidence', 'medium')
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Unknown error'),
                    'explanation': f"This code block shows {similarity_score:.1f}% similarity to previously submitted code. The logic and structure appear to be very similar, which may indicate potential plagiarism."
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'explanation': f"This code block shows {similarity_score:.1f}% similarity to previously submitted code. The logic and structure appear to be very similar, which may indicate potential plagiarism."
            }
    
    def generate_rewrite_suggestion(self, suspicious_code: str, language: str = "python") -> Dict[str, Any]:
        """
        Generate alternative code suggestions to avoid plagiarism.
        
        Args:
            suspicious_code: The code that needs to be rewritten
            language: Programming language of the code
            
        Returns:
            Dictionary containing rewrite suggestions
        """
        
        prompt = f"""
        You are an expert code reviewer helping a student avoid plagiarism. 
        Rewrite the following {language} code to be original while maintaining the same functionality:
        
        Original Code:
        ```{language}
        {suspicious_code}
        ```
        
        Please provide:
        1. A rewritten version that achieves the same result but uses different logic/approach
        2. Brief explanation of the changes made
        3. Any best practices or improvements
        
        Format your response as JSON:
        {{
            "rewritten_code": "your rewritten code here",
            "explanation": "explanation of changes",
            "improvements": "list of improvements made"
        }}
        """
        
        try:
            response = self._call_watsonx_api(prompt)
            
            if response.get('success'):
                return {
                    'success': True,
                    'rewritten_code': response.get('rewritten_code', ''),
                    'explanation': response.get('explanation', ''),
                    'improvements': response.get('improvements', '')
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Failed to generate rewrite suggestion')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_explanation_prompt(self, 
                                 suspicious_code: str, 
                                 similar_code: str, 
                                 similarity_score: float,
                                 submission_info: Dict[str, Any] = None) -> str:
        """Create a detailed prompt for explanation generation."""
        
        team_info = ""
        if submission_info:
            team_info = f"Team: {submission_info.get('team_name', 'Unknown')}, "
            team_info += f"Submission: {submission_info.get('submission_name', 'Unknown')}"
        
        prompt = f"""
        You are an AI assistant helping detect code plagiarism in hackathon submissions. 
        Analyze the following code comparison and provide a clear, educational explanation.
        
        {team_info}
        Similarity Score: {similarity_score:.1f}%
        
        Suspicious Code (Current Submission):
        ```python
        {suspicious_code}
        ```
        
        Similar Code (Previous Submission):
        ```python
        {similar_code}
        ```
        
        Please provide a JSON response with:
        1. A clear explanation of why these code blocks are similar
        2. Specific similarities identified (variable names, logic flow, structure, etc.)
        3. A suggestion for how to make the code more original
        4. Confidence level (low/medium/high) in the plagiarism assessment
        
        Format as JSON:
        {{
            "explanation": "detailed explanation here",
            "similarities": ["list", "of", "specific", "similarities"],
            "suggestion": "suggestion for improvement",
            "confidence": "low/medium/high"
        }}
        """
        
        return prompt
    
    def _call_watsonx_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to Watsonx."""
        
        url = f"{self.url}/ml/v1/text/generation?version=2024-10-01"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 0.9,
                "repetition_penalty": 1.0
            },
            "model_id": self.model,
            "project_id": self.project_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the generated text
            if 'results' in result and len(result['results']) > 0:
                generated_text = result['results'][0]['generated_text']
                
                # Try to parse as JSON
                try:
                    parsed_response = json.loads(generated_text)
                    return {
                        'success': True,
                        **parsed_response
                    }
                except json.JSONDecodeError:
                    # If not JSON, return as explanation
                    return {
                        'success': True,
                        'explanation': generated_text,
                        'suggestion': 'Consider reviewing the code structure and logic for originality.'
                    }
            else:
                return {
                    'success': False,
                    'error': 'No results returned from Watsonx API'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'API request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

# Global instance
watsonx_client = WatsonxClient()
