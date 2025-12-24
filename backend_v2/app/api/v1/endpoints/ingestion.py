from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Any
import uuid

from app.api import deps
# Ensure app.api.deps imports get_session as get_db, or use get_session directly
from app.api.deps import get_db 
from app.models.user import User, RepoAccess
from app.models.repository import Repository, IngestionRun
from app.models.enums import RepoRole, IngestionStatus
from app.schemas.ingestion import IngestRepoRequest, IngestResponse, IngestionStatusResponse
from app.services.ingestion.coordinator import IngestionCoordinator
from app.services.ingestion.cloner import GitCloner
from app.services.identity import get_or_create_user

router = APIRouter()

@router.post("", response_model=IngestResponse)
def ingest_repository(
    request: IngestRepoRequest,
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    coordinator: IngestionCoordinator = Depends(deps.get_ingestion_coordinator),
) -> Any:
    """
    Trigger the ingestion process for a repository.
    """
    try:
        # 1. Parse & Validate URL
        provider, owner, name = GitCloner.parse_url(str(request.repo_url))
        commit_sha = GitCloner.get_remote_head(str(request.repo_url))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Sync User (Write Op) - Ensure user exists in local DB
    user = get_or_create_user(db, auth["clerk_id"])

    # 3. Find or Create Repository
    repo = db.exec(select(Repository).where(
        Repository.provider == provider,
        Repository.owner == owner,
        Repository.name == name
    )).first()

    if not repo:
        # Create new repo
        repo = Repository(
            provider=provider,
            owner=owner,
            name=name,
            is_private=request.is_private,
            default_branch=request.branch or "main",
            latest_commit_sha=commit_sha
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        
        # Grant Ownership to the user who ingested it
        access = RepoAccess(
            user_id=user.id,
            repo_id=repo.id,
            role=RepoRole.OWNER
        )
        db.add(access)
        db.commit()
    else:
        # Check existing access permissions if repo already exists
        access = db.exec(select(RepoAccess).where(
            RepoAccess.repo_id == repo.id,
            RepoAccess.user_id == user.id
        )).first()
        if not access:
             raise HTTPException(status_code=403, detail="Permission denied. You do not have access to re-index this repository.")
    
    # 4. Start Ingestion Pipeline (Celery Task)
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
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get the status of a specific ingestion run.
    Validates that the authenticated user has access to the repository.
    """
    # Secure Status Polling via Join
    # Only return run if the user has a RepoAccess entry for the related repository
    statement = (
        select(IngestionRun)
        .join(Repository, IngestionRun.repo_id == Repository.id)
        .join(RepoAccess, Repository.id == RepoAccess.repo_id)
        .join(User, RepoAccess.user_id == User.id)
        .where(
            IngestionRun.id == run_id,
            User.external_id == auth["clerk_id"]
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