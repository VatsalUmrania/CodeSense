
def save_artifacts(repo: Repository, commit_sha: str, graph_data: dict, ast_data: list):
    paths = StoragePaths()
    storage = StorageService()
    
    # 1. Save Graph (MsgPack)
    graph_path = paths.get_artifact_path(
        repo.provider, repo.owner, repo.name, commit_sha, ArtifactType.GRAPH_DATA
    )
    packed_graph = msgpack.packb(graph_data)
    storage.upload_object(graph_path, packed_graph, "application/msgpack")
    
    # 2. Save Manifest
    manifest_path = paths.get_artifact_path(
        repo.provider, repo.owner, repo.name, commit_sha, ArtifactType.MANIFEST
    )
    manifest = {
        "commit": commit_sha,
        "nodes_count": len(graph_data['nodes']),
        "version": "v2"
    }
    storage.upload_object(manifest_path, json.dumps(manifest).encode(), "application/json")