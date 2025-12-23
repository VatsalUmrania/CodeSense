from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Any, List
import uuid

from app.api import deps
from app.api.deps import get_db
from app.models.user import User, RepoAccess
from app.models.repository import Repository
from app.schemas.repository import RepositoryResponse

router = APIRouter()

@router.get("/", response_model=List[RepositoryResponse])
def list_repositories(
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List repositories user has access to."""
    statement = (
        select(Repository, RepoAccess.role)
        .join(RepoAccess, RepoAccess.repo_id == Repository.id)
        .join(User, RepoAccess.user_id == User.id)
        .where(User.external_id == auth["clerk_id"])
    )
    results = db.exec(statement).all()
    
    repos = []
    for repo, role in results:
        r_dict = repo.model_dump()
        r_dict["role"] = role
        r_dict["full_name"] = repo.full_name
        repos.append(RepositoryResponse(**r_dict))
        
    return repos

@router.get("/{repo_id}", response_model=RepositoryResponse)
def get_repository(
    repo_id: uuid.UUID,
    auth: deps.AuthContext = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    repo = db.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    # Check Access via Join
    access = db.exec(
        select(RepoAccess)
        .join(User)
        .where(
            RepoAccess.repo_id == repo_id, 
            User.external_id == auth["clerk_id"]
        )
    ).first()
    
    if not access:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    r_dict = repo.model_dump()
    r_dict["role"] = access.role
    r_dict["full_name"] = repo.full_name
    return RepositoryResponse(**r_dict)