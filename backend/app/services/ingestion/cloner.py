import os
import shutil
import uuid
from git import Repo

class ClonerService:
    BASE_DIR = "/tmp/codesense_repos"

    def clone_repo(self, repo_url: str) -> str:
        """
        Clones a repo to a unique temp directory.
        Returns the local path.
        """
        repo_id = str(uuid.uuid4())
        local_path = os.path.join(self.BASE_DIR, repo_id)
        
        # Clean up if exists (rare collision)
        if os.path.exists(local_path):
            shutil.rmtree(local_path)

        print(f"Cloning {repo_url} to {local_path}...")
        Repo.clone_from(repo_url, local_path)
        
        return local_path, repo_id