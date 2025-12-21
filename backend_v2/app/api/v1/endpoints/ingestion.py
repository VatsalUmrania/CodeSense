from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Any
import uuid

from app.api import deps
from app.db.session import get_db
from app.models.user import User, RepoAccess
from app.models.repository import Repository, IngestionRun
from app.models.enums import RepoRole, IngestionStatus
from app.schemas.ingestion import IngestRepoRequest, IngestResponse, IngestionStatusResponse
from app.services.ingestion.coordinator import IngestionCoordinator
from app.services.ingestion.cloner import GitCloner

router = APIRouter()

@router.post("/", response_model=IngestResponse)
def ingest_repository(
    request: IngestRepoRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    coordinator: IngestionCoordinator = Depends(deps.get_ingestion_coordinator), # Fixed: Injection
) -> Any:
    # 1. Parse & Resolve SHA (Synchronous Check)
    try:
        provider, owner, name = GitCloner.parse_url(str(request.repo_url))
        commit_sha = GitCloner.get_remote_head(str(request.repo_url)) # Fixed: No "HEAD"
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Upsert Repository (Optimistic Lock Pattern)
    # We check if it exists to avoid unique constraint violations
    repo = db.exec(select(Repository).where(
        Repository.provider == provider,
        Repository.owner == owner,
        Repository.name == name
    )).first()

    if not repo:
        repo = Repository(
            provider=provider,
            owner=owner,
            name=name,
            is_private=request.is_private,
            default_branch=request.branch or "main",
            latest_commit_sha=commit_sha # Initialize with current
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        
        # Fixed: Grant Ownership immediately
        access = RepoAccess(
            user_id=current_user.id,
            repo_id=repo.id,
            role=RepoRole.OWNER
        )
        db.add(access)
        db.commit()
    else:
        # If repo exists, ensure user has access (or add them if public? logic varies)
        # For now, we enforce they must have access to re-trigger
        access = db.exec(select(RepoAccess).where(
            RepoAccess.repo_id == repo.id,
            RepoAccess.user_id == current_user.id
        )).first()
        if not access:
             raise HTTPException(status_code=403, detail="You do not have permission to re-index this repository.")
    
    # 3. Start Ingestion using Concrete SHA
    run_id = coordinator.start_ingestion(repo.id, commit_sha)

    return IngestResponse(
        run_id=run_id,
        repo_id=repo.id,
        status=IngestionStatus.PENDING,
        task_id=str(run_id)
    )

@router.get("/{run_id}", response_model=IngestionStatusResponse)
def get_ingestion_status(
    run_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    # Fixed: Secure Status Polling
    statement = (
        select(IngestionRun)
        .join(Repository, IngestionRun.repo_id == Repository.id)
        .join(RepoAccess, Repository.id == RepoAccess.repo_id)
        .where(
            IngestionRun.id == run_id,
            RepoAccess.user_id == current_user.id
        )
    )
    run = db.exec(statement).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found or access denied")
        
    return IngestionStatusResponse(
        run_id=run.id,
        status=run.status,
        error=run.error
    )