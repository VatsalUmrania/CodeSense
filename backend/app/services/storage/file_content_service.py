"""
File content retrieval service for accessing source code from MinIO storage.

This service enables the CallGraphBuilder to retrieve source files that were
uploaded during ingestion, allowing AST re-parsing for call graph analysis.
"""

from typing import Optional, Dict
import uuid
import tarfile
import io
import logging
from pathlib import Path

from app.services.storage import StorageService, StoragePaths, ArtifactType

logger = logging.getLogger(__name__)


class FileContentService:
    """
    Retrieves source code files from MinIO storage.
    
    During ingestion, the complete source tree is uploaded as a compressed
    tarball. This service extracts individual files on-demand for analysis.
    """
    
    def __init__(self):
        self.storage = StorageService()
        self.paths = StoragePaths()
        
        # Cache for source tarballs (key: repo_id:commit_sha)
        self._tarball_cache: Dict[str, bytes] = {}
        
        # Cache for individual file contents (key: repo_id:commit_sha:file_path)
        self._file_cache: Dict[str, str] = {}
    
    def get_file_content(
        self,
        repo_id: uuid.UUID,
        commit_sha: str,
        file_path: str,
        provider: str,
        owner: str,
        name: str
    ) -> Optional[str]:
        """
        Retrieve source code for a specific file.
        
        Args:
            repo_id: Repository UUID
            commit_sha: Commit SHA
            file_path: Relative path to file within repository
            provider: Git provider (e.g., "github")
            owner: Repository owner
            name: Repository name
            
        Returns:
            File content as string, or None if not found
        """
        # Check file cache first
        file_cache_key = f"{repo_id}:{commit_sha}:{file_path}"
        if file_cache_key in self._file_cache:
            logger.debug(f"File cache hit: {file_path}")
            return self._file_cache[file_cache_key]
        
        # Load source tarball (with caching)
        tarball_bytes = self._get_source_tarball(
            repo_id, commit_sha, provider, owner, name
        )
        
        if not tarball_bytes:
            logger.warning(
                f"Source tarball not found for {owner}/{name}@{commit_sha}"
            )
            return None
        
        # Extract specific file from tarball
        try:
            content = self._extract_file_from_tarball(tarball_bytes, file_path)
            
            if content:
                # Cache for future requests
                self._file_cache[file_cache_key] = content
                logger.debug(f"Extracted and cached: {file_path}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting {file_path} from tarball: {e}")
            return None
    
    def _get_source_tarball(
        self,
        repo_id: uuid.UUID,
        commit_sha: str,
        provider: str,
        owner: str,
        name: str
    ) -> Optional[bytes]:
        """
        Retrieve the compressed source tree tarball from MinIO.
        
        Returns:
            Tarball bytes, or None if not found
        """
        tarball_cache_key = f"{repo_id}:{commit_sha}"
        
        # Check tarball cache
        if tarball_cache_key in self._tarball_cache:
            logger.debug(f"Tarball cache hit for {owner}/{name}@{commit_sha}")
            return self._tarball_cache[tarball_cache_key]
        
        # Convert enum to string if needed
        provider_str = str(provider).split('.')[-1].lower() if hasattr(provider, 'value') else provider
        
        # Construct MinIO path for source tree artifact
        source_artifact_key = self.paths.get_artifact_path(
            provider_str, owner, name, commit_sha, ArtifactType.SOURCE_TREE
        )
        
        try:
            logger.info(f"Downloading source tarball from {source_artifact_key}")
            tarball_bytes = self.storage.download_object(source_artifact_key)
            
            # Cache tarball for subsequent file extractions
            self._tarball_cache[tarball_cache_key] = tarball_bytes
            
            return tarball_bytes
            
        except Exception as e:
            logger.error(
                f"Failed to download source tarball for "
                f"{owner}/{name}@{commit_sha}: {e}"
            )
            return None
    
    def _extract_file_from_tarball(
        self,
        tarball_bytes: bytes,
        file_path: str
    ) -> Optional[str]:
        """
        Extract a single file from the tarball.
        
        Args:
            tarball_bytes: Compressed tarball data
            file_path: Relative path to file within the tarball
            
        Returns:
            File content as string, or None if not found
        """
        try:
            with tarfile.open(fileobj=io.BytesIO(tarball_bytes), mode='r:gz') as tar:
                # Try direct path first
                try:
                    member = tar.getmember(file_path)
                except KeyError:
                    # File might have a prefix directory, try fuzzy match
                    member = None
                    for tar_member in tar.getmembers():
                        if tar_member.name.endswith(file_path):
                            member = tar_member
                            break
                
                if not member:
                    logger.warning(f"File {file_path} not found in tarball")
                    return None
                
                # Extract and decode file content
                file_obj = tar.extractfile(member)
                if file_obj:
                    content = file_obj.read().decode('utf-8', errors='ignore')
                    return content
                else:
                    logger.warning(f"{file_path} is not a regular file")
                    return None
                    
        except tarfile.TarError as e:
            logger.error(f"Error reading tarball: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {file_path}: {e}")
            return None
    
    def clear_cache(self):
        """Clear all caches. Call between repository analyses."""
        self._tarball_cache.clear()
        self._file_cache.clear()
        logger.debug("FileContentService cache cleared")
    
    def preload_tarball(
        self,
        repo_id: uuid.UUID,
        commit_sha: str,
        provider: str,
        owner: str,
        name: str
    ) -> bool:
        """
        Preload a source tarball into cache.
        
        Useful for bulk operations where multiple files will be accessed.
        
        Returns:
            True if successfully loaded, False otherwise
        """
        tarball = self._get_source_tarball(
            repo_id, commit_sha, provider, owner, name
        )
        return tarball is not None
