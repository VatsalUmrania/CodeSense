import tempfile
import uuid
import os
from git import Repo

class ClonerService:
    def clone_repo(self, repo_url: str):
        """
        Clones a repo to a temporary directory with optimized settings for speed.
        Returns (temp_dir_object, full_local_path, repo_id).
        """
        repo_id = str(uuid.uuid4())
        
        # Create a temporary directory that cleans itself up when the object is destroyed
        temp_dir = tempfile.TemporaryDirectory(prefix="codesense_")
        local_path = os.path.join(temp_dir.name, repo_id)
        
        print(f"Cloning {repo_url} to {local_path}...")
        
        # Optimization:
        # depth=1: Shallow clone (no history)
        # single_branch=True: Only fetch the default branch
        # no_tags=True: Don't fetch tags
        Repo.clone_from(
            repo_url, 
            local_path, 
            depth=1, 
            single_branch=True, 
            no_tags=True
        )
        
        return temp_dir, local_path, repo_id