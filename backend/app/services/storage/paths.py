from enum import Enum
from app.models.enums import RepoProvider

class ArtifactType(str, Enum):
    SOURCE_ARCHIVE = "source.tar.zst"
    GRAPH_DATA = "graph.msgpack"
    AST_DATA = "ast.msgpack"
    MANIFEST = "manifest.json"

class StoragePaths:
    @staticmethod
    def get_repo_root(provider: RepoProvider, owner: str, name: str) -> str:
        """repos/github/facebook/react/"""
        return f"repos/{provider.value}/{owner}/{name}"

    @staticmethod
    def get_commit_root(provider: RepoProvider, owner: str, name: str, commit_sha: str) -> str:
        """repos/github/facebook/react/commits/a1b2c3d4/"""
        repo_root = StoragePaths.get_repo_root(provider, owner, name)
        return f"{repo_root}/commits/{commit_sha}"

    @staticmethod
    def get_artifact_path(
        provider: RepoProvider, 
        owner: str, 
        name: str, 
        commit_sha: str, 
        artifact: ArtifactType
    ) -> str:
        """repos/github/facebook/react/commits/a1b2c3d4/graph.msgpack"""
        commit_root = StoragePaths.get_commit_root(provider, owner, name, commit_sha)
        return f"{commit_root}/{artifact.value}"