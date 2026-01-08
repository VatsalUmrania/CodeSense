from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Any
import uuid

from app.api import deps
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
        
        # --- FIX: Normalize provider for DB Enum (e.g., "github.com" -> "github") ---
        if "." in provider:
            provider = provider.split(".")[0]
        # -----------------------------------------------------------------------------

        commit_sha = GitCloner.get_remote_head(str(request.repo_url))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # It is good practice to catch Git errors here if GitCloner doesn't wrap them in ValueError
    except Exception as e: 
        # Catching generic Exception for safety given the previous git.exc crashes
        # You might want to import git.exc.GitCommandError for more precision
        if "fatal:" in str(e) or "exit code" in str(e):
             raise HTTPException(status_code=400, detail=f"Git Error: {str(e)}")
        raise e

    # 2. Sync User
    user = get_or_create_user(db, auth["clerk_id"])

    # 3. Find or Create Repository
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
            latest_commit_sha=commit_sha
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        
        access = RepoAccess(
            user_id=user.id,
            repo_id=repo.id,
            role=RepoRole.OWNER
        )
        db.add(access)
        db.commit()
    else:
        # FIX: Always update the latest_commit_sha to the one we are about to ingest
        repo.latest_commit_sha = commit_sha
        db.add(repo)
        db.commit()
        db.refresh(repo)

        # Check existing access permissions
        access = db.exec(select(RepoAccess).where(
            RepoAccess.repo_id == repo.id,
            RepoAccess.user_id == user.id
        )).first()
        if not access:
             raise HTTPException(status_code=403, detail="Permission denied. You do not have access to re-index this repository.")
    
    # 4. Start Ingestion Pipeline
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