import git
import tempfile
import os
import shutil
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

    # --- ADDED THIS METHOD ---
    @staticmethod
    def clone_repo(provider: RepoProvider, owner: str, name: str, commit_sha: str) -> str:
        """
        Clones the repo to a temp folder and checks out the specific SHA.
        Returns the path to the local directory.
        """
        # Construct URL based on provider
        # Note: Ideally handle auth tokens here for private repos
        if provider == RepoProvider.GITLAB:
             url = f"https://gitlab.com/{owner}/{name}.git"
        else:
             url = f"https://github.com/{owner}/{name}.git"

        # Create unique temp dir
        local_path = tempfile.mkdtemp(prefix=f"codesense_{name}_")

        try:
            # Clone
            repo = git.Repo.clone_from(url, local_path)
            
            # Checkout specific commit
            repo.git.checkout(commit_sha)
            
            return local_path
        except git.Exc as e:
            # Clean up if failed
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            raise RuntimeError(f"Failed to clone {url} at {commit_sha}: {e}")