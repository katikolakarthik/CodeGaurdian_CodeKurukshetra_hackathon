"""
GitHub utility to fetch repository code files via GitHub API.
"""

import os
import base64
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

ALLOWED_EXTENSIONS = {
    '.py', '.java', '.c', '.cpp', '.cs', '.js', '.jsx', '.ts', '.tsx', '.go', '.rb', '.rs', '.php', '.swift', '.kt', '.m', '.scala', '.sh', '.sql', '.html', '.css', '.ipynb'
}

class GitHubFetcher:
    """Fetch files from GitHub repositories using the API."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
        self.api_base = 'https://api.github.com'

    def _headers(self) -> Dict[str, str]:
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def parse_repo_url(self, url: str) -> Dict[str, str]:
        """Parse GitHub repo URL and extract owner, repo, and optional branch.
        Supports forms like:
        - https://github.com/owner/repo
        - https://github.com/owner/repo/tree/branch
        """
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
        resp = requests.get(f"{self.api_base}/repos/{owner}/{repo}", headers=self._headers(), timeout=20)
        resp.raise_for_status()
        return resp.json().get('default_branch', 'main')

    def fetch_repo_tree(self, owner: str, repo: str, branch: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch full repo tree (recursive) and filter to allowed file types."""
        if branch is None:
            branch = self.get_default_branch(owner, repo)
        # First get the branch to find the commit sha
        branch_resp = requests.get(f"{self.api_base}/repos/{owner}/{repo}/branches/{branch}", headers=self._headers(), timeout=20)
        branch_resp.raise_for_status()
        commit_sha = branch_resp.json()['commit']['sha']

        # Get recursive tree
        tree_resp = requests.get(f"{self.api_base}/repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1", headers=self._headers(), timeout=30)
        tree_resp.raise_for_status()
        tree = tree_resp.json().get('tree', [])

        files = []
        for node in tree:
            if node.get('type') == 'blob':
                path: str = node['path']
                _, ext = os.path.splitext(path)
                if ext.lower() in ALLOWED_EXTENSIONS:
                    files.append({'path': path, 'sha': node['sha'], 'size': node.get('size', 0)})
        return files

    def fetch_file_content(self, owner: str, repo: str, path: str, branch: Optional[str] = None) -> str:
        params = {'ref': branch} if branch else None
        content_resp = requests.get(f"{self.api_base}/repos/{owner}/{repo}/contents/{path}", headers=self._headers(), params=params, timeout=20)
        content_resp.raise_for_status()
        data = content_resp.json()
        if data.get('encoding') == 'base64':
            return base64.b64decode(data['content']).decode('utf-8', errors='ignore')
        # Fallback for raw
        if 'download_url' in data and data['download_url']:
            raw_resp = requests.get(data['download_url'], timeout=20)
            raw_resp.raise_for_status()
            return raw_resp.text
        return ''

    def fetch_repository(self, url: str, max_total_bytes: int = 10 * 1024 * 1024) -> Dict[str, Any]:
        """Fetch repository files and their contents.
        Returns dict with repo metadata and list of files: [{path, content}].
        """
        parts = self.parse_repo_url(url)
        owner, repo, branch = parts['owner'], parts['repo'], parts['branch']
        files_meta = self.fetch_repo_tree(owner, repo, branch)

        total_bytes = 0
        files: List[Dict[str, Any]] = []
        for meta in files_meta:
            if total_bytes > max_total_bytes:
                break
            try:
                content = self.fetch_file_content(owner, repo, meta['path'], branch)
                total_bytes += len(content.encode('utf-8'))
                files.append({'path': meta['path'], 'content': content, 'size': len(content)})
            except requests.HTTPError:
                continue
        return {
            'owner': owner,
            'repo': repo,
            'branch': branch or self.get_default_branch(owner, repo),
            'file_count': len(files),
            'files': files
        }

# Global instance
github_fetcher = GitHubFetcher()
