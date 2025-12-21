import git
from typing import Tuple
from app.models.enums import RepoProvider

class GitCloner:
    @staticmethod
    def parse_url(url: str) -> Tuple[RepoProvider, str, str]:
        """
        Parses https://github.com/owner/name -> (provider, owner, name)
        """
        clean_url = url.strip()
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]
        
        # Remove protocol
        if "://" in clean_url:
            clean_url = clean_url.split("://")[1]
            
        # Split parts (github.com / owner / name)
        parts = clean_url.split("/")
        
        if len(parts) < 3:
            raise ValueError(f"Invalid repository URL format: {url}")
            
        domain = parts[0].lower()
        owner = parts[1]
        name = parts[2]
        
        # Detect Provider
        if "gitlab" in domain:
            provider = RepoProvider.GITLAB
        else:
            provider = RepoProvider.GITHUB
            
        return provider, owner, name

    @staticmethod
    def get_remote_head(url: str) -> str:
        """
        Synchronously fetches the latest commit SHA using git ls-remote.
        """
        g = git.cmd.Git()
        try:
            output = g.ls_remote(url, "HEAD")
            if not output:
                raise ValueError("Could not resolve HEAD for repository")
            sha = output.split()[0]
            return sha
        except git.Exc as e:
            raise ValueError(f"Failed to access repository: {str(e)}")