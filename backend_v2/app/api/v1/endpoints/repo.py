from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Any, List
import uuid

from app.api import deps
from app.db.session import get_db
from app.models.user import User, RepoAccess
from app.models.repository import Repository
from app.schemas.repository import RepositoryResponse
from app.models.enums import RepoRole

router = APIRouter()

@router.get("/", response_model=List[RepositoryResponse])
def list_repositories(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    List all repositories the user has access to.
    Does a JOIN between Repository and RepoAccess.
    """
    # 1. Get IDs from Access Table
    statement = (
        select(Repository, RepoAccess.role)
        .join(RepoAccess, RepoAccess.repo_id == Repository.id)
        .where(RepoAccess.user_id == current_user.id)
    )
    results = db.exec(statement).all()
    
    # 2. Transform to Schema
    repos = []
    for repo, role in results:
        # Pydantic handles the mapping, we just add the computed 'role'
        r_dict = repo.model_dump()
        r_dict["role"] = role
        r_dict["full_name"] = repo.full_name
        repos.append(RepositoryResponse(**r_dict))
        
    return repos

@router.get("/{repo_id}", response_model=RepositoryResponse)
def get_repository(
    repo_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    # Check Access
    access = db.exec(
        select(RepoAccess)
        .where(RepoAccess.repo_id == repo_id, RepoAccess.user_id == current_user.id)
    ).first()
    
    if not access:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    r_dict = repo.model_dump()
    r_dict["role"] = access.role
    r_dict["full_name"] = repo.full_name
    return RepositoryResponse(**r_dict)