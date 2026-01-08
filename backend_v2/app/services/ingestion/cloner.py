import git
import os
import shutil
import tempfile
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class GitCloner:
    @staticmethod
    def parse_url(url: str) -> tuple[str, str, str]:
        """
        Parses a git URL to extract provider, owner, and repo name.
        """
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        
        if len(path_parts) < 2:
            raise ValueError("Invalid Repository URL")
            
        provider = parsed.netloc
        owner = path_parts[0]
        name = path_parts[1].replace(".git", "")
        
        return provider, owner, name

    @staticmethod
    def get_remote_head(url: str) -> str:
        """
        Gets the latest commit SHA from the remote HEAD without cloning.
        """
        g = git.cmd.Git()
        try:
            # FIX: Use the correct git command syntax
            output = g.ls_remote(url, "HEAD")
            if not output:
                raise ValueError("No output from ls-remote")
            return output.split()[0]
        # FIX: Correct Exception Class
        except git.exc.GitCommandError as e:
            logger.error(f"Git Command Error: {e}")
            raise ValueError(f"Could not access repository: {e}")
        except Exception as e:
            logger.error(f"Unexpected Error checking remote head: {e}")
            raise ValueError(f"Failed to resolve repository HEAD: {e}")

    @staticmethod
    def clone_repo(provider: str, owner: str, name: str, commit_sha: str) -> str:
        """
        Clones the repository to a temporary directory and checks out the specific commit.
        Returns the local path.
        """
        # FIX: Handle Enum objects if passed directly from DB model
        if hasattr(provider, "value"):
            provider = provider.value

        # FIX: Normalize provider to a real domain (DB stores 'github', Git needs 'github.com')
        provider_str = str(provider).lower()
        if provider_str == "github":
            domain = "github.com"
        elif provider_str == "gitlab":
            domain = "gitlab.com"
        elif provider_str == "bitbucket":
            domain = "bitbucket.org"
        else:
            # Fallback for when the provider is already a domain (e.g. "github.com")
            domain = provider

        repo_url = f"https://{domain}/{owner}/{name}.git"
        temp_dir = tempfile.mkdtemp()
        
        try:
            logger.info(f"Cloning {repo_url} to {temp_dir}...")
            repo = git.Repo.clone_from(repo_url, temp_dir)
            
            logger.info(f"Checking out commit {commit_sha}...")
            repo.git.checkout(commit_sha)
            
            return temp_dir
        except Exception as e:
            logger.error(f"Failed to clone repo: {e}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e