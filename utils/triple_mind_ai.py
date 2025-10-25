"""
TripleMind AI Service - Integration of three AI models for comprehensive code analysis
"""

import os
import requests
import json
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class TripleMindAI:
    """TripleMind AI service combining Gemini, DeepSeek, and GPT-OSS models"""
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        
    def call_gemini_api(self, prompt: str, context_chunks: List[Dict] = None, filename: str = "") -> Optional[str]:
        """Call Google Gemini API with context from code analysis"""
        if not self.google_api_key or self.google_api_key == "your_actual_google_api_key_here":
            # Return mock response for testing
            return f"📚 **Gemini Analysis:** This is a mock response for testing. The code appears to be well-structured with good practices. Consider adding more comments for better maintainability. [CodeFile L.1]"
            
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        if context_chunks:
            # Build context with code citations
            context_lines = []
            for chunk in context_chunks:
                file_name = chunk.get('filename', filename)
                line_num = chunk.get('line_number', 'N/A')
                snippet = chunk.get('text', '')[:500]
                context_lines.append(f"[{file_name} L.{line_num}] {snippet}")
            
            context_text = "\n\n".join(context_lines)
            
            full_prompt = f"""Context from code analysis:
{context_text}

Question: {prompt}

IMPORTANT: You MUST include inline citations in your answer using the format [FileName L.X] where X is the line number.

Rules for citations:
1. Every code reference must be cited with [FileName L.X]
2. Use the exact file names and line numbers from the context
3. Place citations immediately after the relevant information
4. If you reference multiple sources, cite each one appropriately

Please provide a simple, clean response with proper citations:
- Write in simple, clear sentences
- Include [FileName L.X] citations for all code references
- No bullet points or complex formatting
- Natural conversation style
- Easy to read line by line

Answer based on the provided context from the code analysis."""
        else:
            full_prompt = f"""Question: {prompt}

Please provide a simple, clean response in plain text format:
- Write in simple, clear sentences
- No bullet points, no special formatting
- No emojis or symbols
- Just plain text like ChatGPT
- Easy to read line by line
- Natural conversation style"""

        headers = {"Content-Type": "application/json"}
        
        data = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }]
        }
        
        try:
            response = requests.post(
                f"{url}?key={self.google_api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    return "Sorry, I couldn't generate a response. Please try again."
            else:
                return None
                
        except Exception as e:
            return None

    def call_deepseek_api(self, prompt: str) -> Optional[str]:
        """Call DeepSeek AI via OpenRouter for global knowledge"""
        if not self.openrouter_api_key or self.openrouter_api_key == "your_actual_openrouter_api_key_here":
            # Return mock response for testing
            return f"🌍 **DeepSeek Analysis:** This is a mock response for testing. Based on global programming knowledge, your question shows good understanding of the topic. Consider exploring advanced concepts for deeper learning."
            
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-plagiarism-detector.com",
            "X-Title": "AI Code Plagiarism Detector"
        }
        
        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant specializing in code analysis and programming. Provide clear, accurate answers in simple, conversational language. No bullet points or complex formatting - just clean, easy-to-read text like ChatGPT."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return None
            else:
                return None

        except Exception as e:
            return None

    def call_gpt_oss_api(self, prompt: str) -> Optional[str]:
        """Call GPT-OSS-120B via OpenRouter for high-reasoning capabilities"""
        if not self.openrouter_api_key or self.openrouter_api_key == "your_actual_openrouter_api_key_here":
            # Return mock response for testing
            return f"🤖 **GPT-OSS Analysis:** This is a mock response for testing. Using advanced reasoning capabilities, I can see this question requires deep analysis. The approach shows sophisticated thinking and demonstrates good problem-solving skills."
            
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-plagiarism-detector.com",
            "X-Title": "AI Code Plagiarism Detector"
        }
        
        data = {
            "model": "qwen/qwen-2.5-72b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert code analysis assistant with high reasoning capabilities. Provide detailed, well-structured answers with logical flow and clear explanations for code-related questions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return None
            else:
                return None

        except Exception as e:
            return None

    def parse_citations(self, response_text: str) -> List[Dict]:
        """Parse citations from AI response text"""
        import re
        
        # Pattern to match [FileName L.X] citations
        citation_pattern = r'\[([^\]]+)\s+L\.(\d+)\]'
        citations = []
        
        # Find all citations in the response
        matches = re.finditer(citation_pattern, response_text)
        for match in matches:
            file_name = match.group(1).strip()
            line_num = int(match.group(2))
            
            # Check if this citation already exists
            existing = next((c for c in citations if c['file'] == file_name and c['line'] == line_num), None)
            if not existing:
                citations.append({
                    'file': file_name,
                    'line': line_num,
                    'count': 1
                })
            else:
                existing['count'] += 1
        
        return citations

    def analyze_with_triple_mind(self, 
                               question: str, 
                               code_context: List[Dict] = None,
                               models: List[str] = None) -> Dict[str, Any]:
        """
        Analyze code using TripleMind approach
        
        Args:
            question: The question to analyze
            code_context: List of code chunks with metadata
            models: List of models to use ['gemini', 'deepseek', 'gpt_oss']
        
        Returns:
            Dictionary with responses from selected models
        """
        if models is None:
            models = ['gemini', 'deepseek', 'gpt_oss']
        
        results = {
            'question': question,
            'responses': {},
            'citations': [],
            'model_used': models
        }
        
        # Get Gemini response (code-specific)
        if 'gemini' in models:
            gemini_response = self.call_gemini_api(question, code_context)
            if gemini_response:
                results['responses']['gemini'] = gemini_response
                results['citations'] = self.parse_citations(gemini_response)
        
        # Get DeepSeek response (global knowledge)
        if 'deepseek' in models:
            deepseek_response = self.call_deepseek_api(question)
            if deepseek_response:
                results['responses']['deepseek'] = deepseek_response
        
        # Get GPT-OSS response (high reasoning)
        if 'gpt_oss' in models:
            gpt_oss_response = self.call_gpt_oss_api(question)
            if gpt_oss_response:
                results['responses']['gpt_oss'] = gpt_oss_response
        
        return results

    def get_combined_response(self, results: Dict[str, Any]) -> str:
        """Combine responses from multiple models into a single response"""
        combined = ""
        
        if 'gemini' in results['responses']:
            combined += f"📚 **Code-Specific Analysis (Gemini):**\n{results['responses']['gemini']}\n\n"
        
        if 'deepseek' in results['responses']:
            combined += f"🌍 **Global Knowledge (DeepSeek):**\n{results['responses']['deepseek']}\n\n"
        
        if 'gpt_oss' in results['responses']:
            combined += f"🤖 **High Reasoning (GPT-OSS):**\n{results['responses']['gpt_oss']}\n\n"
        
        return combined.strip()
