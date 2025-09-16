"""
GitHub API utility for fetching repository code.
Separated from github.py for better organization.
"""

import os
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

class GitHubAPI:
    """GitHub API client for fetching repository code."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
        self.api_base = 'https://api.github.com'
        self.allowed_extensions = {
            '.py', '.java', '.c', '.cpp', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.php', '.rb', '.go', '.rs'
        }
    
    def _headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def parse_repo_url(self, url: str) -> Dict[str, str]:
        """Parse GitHub repo URL and extract owner, repo, and optional branch."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) < 2:
            raise ValueError('Invalid GitHub repository URL')
        owner, repo = path_parts[0], path_parts[1].replace('.git', '')
        branch = None
        if len(path_parts) >= 4 and path_parts[2] == 'tree':
            branch = path_parts[3]
        return {'owner': owner, 'repo': repo, 'branch': branch}
    
    def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch of a repository."""
        try:
            resp = requests.get(f"{self.api_base}/repos/{owner}/{repo}", headers=self._headers(), timeout=20)
            resp.raise_for_status()
            return resp.json().get('default_branch', 'main')
        except Exception as e:
            raise Exception(f"Failed to get default branch: {str(e)}")
    
    def fetch_repo_files(self, owner: str, repo: str, branch: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all code files from a repository."""
        if branch is None:
            branch = self.get_default_branch(owner, repo)
        
        # Get the commit SHA for the branch
        try:
            branch_resp = requests.get(f"{self.api_base}/repos/{owner}/{repo}/branches/{branch}", headers=self._headers(), timeout=20)
            branch_resp.raise_for_status()
            commit_sha = branch_resp.json()['commit']['sha']
        except Exception as e:
            raise Exception(f"Failed to get branch info: {str(e)}")
        
        # Get recursive tree
        try:
            tree_resp = requests.get(f"{self.api_base}/repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1", headers=self._headers(), timeout=30)
            tree_resp.raise_for_status()
            tree = tree_resp.json().get('tree', [])
        except Exception as e:
            raise Exception(f"Failed to get repository tree: {str(e)}")
        
        # Filter for code files
        files = []
        for node in tree:
            if node.get('type') == 'blob':
                path = node['path']
                _, ext = os.path.splitext(path)
                if ext.lower() in self.allowed_extensions:
                    files.append({
                        'path': path,
                        'sha': node['sha'],
                        'size': node.get('size', 0)
                    })
        
        return files
    
    def fetch_file_content(self, owner: str, repo: str, path: str, branch: Optional[str] = None) -> str:
        """Fetch the content of a specific file."""
        try:
            params = {'ref': branch} if branch else None
            content_resp = requests.get(f"{self.api_base}/repos/{owner}/{repo}/contents/{path}", headers=self._headers(), params=params, timeout=20)
            content_resp.raise_for_status()
            data = content_resp.json()
            
            if data.get('encoding') == 'base64':
                import base64
                return base64.b64decode(data['content']).decode('utf-8', errors='ignore')
            elif 'download_url' in data and data['download_url']:
                raw_resp = requests.get(data['download_url'], timeout=20)
                raw_resp.raise_for_status()
                return raw_resp.text
            else:
                return ''
        except Exception as e:
            raise Exception(f"Failed to fetch file content: {str(e)}")
    
    def fetch_repository(self, url: str, max_files: int = 50) -> Dict[str, Any]:
        """
        Fetch a complete repository with all code files.
        
        Args:
            url: GitHub repository URL
            max_files: Maximum number of files to process
            
        Returns:
            Dictionary with repository data and files
        """
        try:
            parts = self.parse_repo_url(url)
            owner, repo, branch = parts['owner'], parts['repo'], parts['branch']
            
            # Get default branch if not specified
            if branch is None:
                branch = self.get_default_branch(owner, repo)
            
            # Fetch file list
            files_meta = self.fetch_repo_files(owner, repo, branch)
            
            # Limit number of files
            if len(files_meta) > max_files:
                files_meta = files_meta[:max_files]
            
            # Fetch file contents
            files = []
            for meta in files_meta:
                try:
                    content = self.fetch_file_content(owner, repo, meta['path'], branch)
                    files.append({
                        'path': meta['path'],
                        'content': content,
                        'size': len(content),
                        'extension': os.path.splitext(meta['path'])[1].lower()
                    })
                except Exception as e:
                    print(f"Warning: Failed to fetch {meta['path']}: {e}")
                    continue
            
            return {
                'success': True,
                'owner': owner,
                'repo': repo,
                'branch': branch,
                'file_count': len(files),
                'files': files,
                'url': url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'owner': '',
                'repo': '',
                'branch': '',
                'file_count': 0,
                'files': [],
                'url': url
            }

# Global instance
github_api = GitHubAPI()
